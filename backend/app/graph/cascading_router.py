import uuid
import time
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from config.settings import settings
from app.models.schemas import (
    ChatRequest, ChatResponse, ModelExecutionTrace,
    EscalationEvent, TokenMetrics, QualityEvaluationResult, QualityRecoveryResult,
)


class CascadingRouter:
    """
    Cascading Multi-Tier LLM Router backed by LangGraph.

    Graph flow:
      START → classify_task → select_models → execute_tier1 → decide_escalation
        → [if escalated] execute_tier2 → evaluate_quality
        → [if direct]    evaluate_quality
        → recover_quality → compute_costs → finalize → END
    """

    _graph = None
    _checkpointer = None
    _loop = None

    @classmethod
    async def _get_graph(cls):
        import asyncio
        curr_loop = asyncio.get_running_loop()
        if cls._graph is None or cls._loop is not curr_loop:
            from agent.graph import build_router_graph
            from app.database import get_checkpointer

            cls._loop = curr_loop
            cls._checkpointer = await get_checkpointer()
            graph = build_router_graph()
            cls._graph = graph.compile(checkpointer=cls._checkpointer)
        return cls._graph

    @classmethod
    async def process_query(cls, request: ChatRequest) -> ChatResponse:
        total_start = time.time()
        query_id = f"qry_{uuid.uuid4().hex[:10]}"
        provider = (request.provider or settings.default_provider).lower()
        threshold = (
            request.confidence_threshold
            if request.confidence_threshold is not None
            else settings.confidence_threshold
        )

        graph = await cls._get_graph()

        initial_state = {
            "request_id": query_id,
            "tenant_id": "default",
            "user_id": request.user_id,
            "user_input": request.prompt,
            "provider": provider,
            "confidence_threshold": threshold,
            "force_escalation": request.force_escalation or False,
            "force_tier1_only": request.force_tier1_only or False,
            "task_type": "",
            "complexity_score": 0.0,
            "requires_tools": False,
            "candidate_models": [],
            "eligible_models": [],
            "pareto_models": [],
            "selected_model": "",
            "routing_score": 0.0,
            "routing_factors": {},
            "attempts": [],
            "tool_calls": [],
            "quality_score": 0.0,
            "evaluation": {},
            "escalation_reason": None,
            "retry_count": 0,
            "budget_remaining": 1.0,
            "estimated_cost": 0.0,
            "actual_cost": 0.0,
            "final_response": "",
            "status": "running",
            "tier1_draft": "",
            "tier1_confidence": 0.0,
            "tier1_uncertainty_reasons": [],
            "tier1_tokens": {},
            "tier1_latency_ms": 0.0,
            "tier1_model_id": "",
            "tier1_model_name": "",
            "tier2_answer": "",
            "tier2_tokens": {},
            "tier2_latency_ms": 0.0,
            "tier2_model_id": "",
            "tier2_model_name": "",
            "traces": [],
            "cost_breakdown": {},
            "quality_evaluation": None,
            "quality_recovery": None,
        }

        result = await graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": query_id}},
        )

        total_latency_ms = round((time.time() - total_start) * 1000, 2)
        return _assemble_response(result, total_latency_ms)


def _assemble_response(state: dict, total_latency_ms: float) -> ChatResponse:
    """Convert final LangGraph state into a ChatResponse."""
    is_escalated = state.get("status") == "escalated" or state.get("escalation_reason") is not None
    served_by_tier = "tier2" if is_escalated and state.get("tier2_answer") else "tier1"
    served_by_model = state.get("tier2_model_name") or state.get("tier1_model_name") or ""
    final_answer = state.get("final_response") or state.get("tier1_draft") or ""

    traces = []
    for t in state.get("traces", []):
        traces.append(ModelExecutionTrace(
            model_name=t.get("model_name", ""),
            tier=t.get("tier", "tier1"),
            prompt=t.get("prompt", ""),
            response_text=t.get("response_text", ""),
            confidence=t.get("confidence"),
            uncertainty_reasons=t.get("uncertainty_reasons", []),
            tokens=TokenMetrics(
                input_tokens=t.get("tokens", {}).get("input_tokens", 0),
                output_tokens=t.get("tokens", {}).get("output_tokens", 0),
                total_tokens=t.get("tokens", {}).get("total_tokens", 0),
            ),
            cost_usd=t.get("cost_usd", 0.0),
            latency_ms=t.get("latency_ms", 0.0),
            model_id=t.get("model_id"),
            pricing_id=t.get("pricing_id"),
            pareto_score=t.get("pareto_score"),
            pareto_rank=t.get("pareto_rank"),
        ))

    cb = state.get("cost_breakdown", {})
    cost_breakdown_obj = type("CostBreakdown", (), {
        "tier1_cost_usd": cb.get("tier1_cost_usd", 0.0),
        "tier2_cost_usd": cb.get("tier2_cost_usd", 0.0),
        "total_cost_usd": cb.get("total_cost_usd", 0.0),
        "baseline_sonnet_cost_usd": cb.get("baseline_sonnet_cost_usd", 0.0),
        "savings_usd": cb.get("savings_usd", 0.0),
        "savings_percent": cb.get("savings_percent", 0.0),
        "currency": cb.get("currency", "USD"),
        "spend_justification": cb.get("spend_justification", ""),
        "tier1_pricing_id": cb.get("tier1_pricing_id"),
        "tier2_pricing_id": cb.get("tier2_pricing_id"),
    })()

    from app.models.schemas import CostBreakdown
    cost_breakdown = CostBreakdown(
        tier1_cost_usd=cb.get("tier1_cost_usd", 0.0),
        tier2_cost_usd=cb.get("tier2_cost_usd", 0.0),
        total_cost_usd=cb.get("total_cost_usd", 0.0),
        baseline_sonnet_cost_usd=cb.get("baseline_sonnet_cost_usd", 0.0),
        savings_usd=cb.get("savings_usd", 0.0),
        savings_percent=cb.get("savings_percent", 0.0),
        currency=cb.get("currency", "USD"),
        spend_justification=cb.get("spend_justification", ""),
        tier1_pricing_id=cb.get("tier1_pricing_id"),
        tier2_pricing_id=cb.get("tier2_pricing_id"),
    )

    escalation = EscalationEvent(
        escalated=is_escalated,
        reason=state.get("escalation_reason"),
        explanation=_build_escalation_explanation(state),
        trigger_confidence=state.get("tier1_confidence"),
        threshold=state.get("confidence_threshold"),
    )

    quality_eval = None
    if state.get("evaluation"):
        qe = state["evaluation"]
        quality_eval = QualityEvaluationResult(
            task_type=qe.get("task_type", "unknown"),
            quality_score=qe.get("quality_score", 0.0),
            deterministic_score=qe.get("deterministic_score"),
            llm_judge_score=qe.get("llm_judge_score"),
            metrics=qe.get("metrics", {}),
        )

    quality_recovery = None
    qr = state.get("quality_recovery")
    if qr:
        quality_recovery = QualityRecoveryResult(
            action_taken=qr.get("action_taken", "accept"),
            original_score=qr.get("original_score", 0.0),
            final_score=qr.get("final_score"),
            revision_attempts=qr.get("revision_attempts", 0),
            recovery_model=qr.get("recovery_model"),
            recovery_model_id=qr.get("recovery_model_id"),
            recovery_cost_usd=qr.get("recovery_cost_usd", 0.0),
            recovery_latency_ms=qr.get("recovery_latency_ms", 0.0),
        )

    return ChatResponse(
        id=state.get("request_id", ""),
        prompt=state.get("user_input", ""),
        final_answer=final_answer,
        served_by_tier=served_by_tier,
        served_by_model=served_by_model,
        confidence=state.get("tier1_confidence", 0.0),
        escalation=escalation,
        traces=traces,
        cost_breakdown=cost_breakdown,
        total_latency_ms=total_latency_ms,
        quality_evaluation=quality_eval,
        quality_recovery=quality_recovery,
        key_source=state.get("key_source"),
        timestamp=datetime.now(timezone.utc),
    )


def _build_escalation_explanation(state: dict) -> str:
    """Build a human-readable escalation explanation."""
    reason = state.get("escalation_reason")
    if not reason:
        return ""

    conf = state.get("tier1_confidence", 0.0)
    threshold = state.get("confidence_threshold", 0.75)
    uncertainty = state.get("tier1_uncertainty_reasons", [])

    if reason == "LOW_CONFIDENCE":
        reasons_str = "; ".join(uncertainty) if uncertainty else "Model expressed uncertainty"
        return f"Confidence {conf:.2f} is below threshold {threshold:.2f}. Identified flags: {reasons_str}"
    elif reason == "LOW_QUALITY":
        qs = state.get("quality_score", 0.0)
        return f"Quality score {qs:.2f} fell below the revision threshold. Upgrading to frontier model."
    elif reason == "FORCED_OVERRIDE":
        return "Manual test override forced Tier 2 escalation."
    elif reason == "MODEL_TIMEOUT":
        return "Tier 1 model timed out. Falling back to Tier 2."
    elif reason == "MODEL_RATE_LIMIT":
        return "Tier 1 model rate limited. Falling back to Tier 2."
    elif reason == "PROVIDER_ERROR":
        return "Tier 1 provider returned an error. Falling back to Tier 2."
    elif reason == "QUALITY_REVISION_FAILED":
        return "Quality revision attempts exhausted without meeting threshold."
    else:
        return f"Escalation triggered: {reason}"
