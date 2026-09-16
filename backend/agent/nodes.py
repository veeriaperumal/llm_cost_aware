import uuid
import time
import re
import json
import sys
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import settings
from agent.state import RouterState
from agent.escalation_reasons import EscalationReason
from app.models.schemas import TokenMetrics, ModelExecutionTrace


# =============================================================================
# Node 1: classify_task
# =============================================================================
async def classify_task(state: RouterState) -> dict:
    """Classify the user input by task type and complexity."""
    prompt = state["user_input"]
    word_count = len(prompt.split())

    complexity = 0.0
    requires_tools = False

    high_complexity_keywords = [
        "design", "architect", "distributed", "consensus", "trade-off",
        "concurrency", "parallel", "protocol", "scalability", "fault-tolerant",
        "explain the difference", "compare", "analyze", "critique", "reasoning",
        "multi-step", "deep", "comprehensive", "exhaustive", "rigorous",
    ]
    medium_complexity_keywords = [
        "how does", "why", "what are the", "implement", "code", "debug",
        "optimize", "refactor", "review", "explain", "describe",
    ]
    tool_keywords = [
        "search", "lookup", "fetch", "calculate", "compute", "run",
        "execute", "call", "api", "database", "query",
    ]

    prompt_lower = prompt.lower()
    for kw in high_complexity_keywords:
        if kw in prompt_lower:
            complexity += 0.15
    for kw in medium_complexity_keywords:
        if kw in prompt_lower:
            complexity += 0.08
    for kw in tool_keywords:
        if kw in prompt_lower:
            requires_tools = True
            complexity += 0.05

    if "?" in prompt:
        complexity += 0.05
    if word_count > 50:
        complexity += 0.10
    if word_count > 100:
        complexity += 0.10

    question_marks = prompt.count("?")
    if question_marks >= 2:
        complexity += 0.10

    has_code = bool(re.search(r"```|def |class |import |function |const |let |var ", prompt))
    if has_code:
        complexity += 0.10

    complexity = min(1.0, complexity)

    task_type = "qa"
    if has_code:
        task_type = "coding"
    elif complexity > 0.6:
        task_type = "analysis"
    elif any(kw in prompt_lower for kw in ["compare", "versus", "difference between"]):
        task_type = "comparison"

    return {
        "task_type": task_type,
        "complexity_score": round(complexity, 3),
        "requires_tools": requires_tools,
    }


# =============================================================================
# Node 2: select_models
# =============================================================================
async def select_models(state: RouterState) -> dict:
    """Query DB for available models, run Pareto filtering, select best."""
    from sqlalchemy import select
    from app.database import async_session
    from app.models.db_models import LLMModel, ModelPricing as DBModelPricing
    from app.graph.pareto import ModelCandidate, select_best
    from app.router.provider_client import LLMProviderClient
    from app.services.key_service import KeyService

    provider = state["provider"]
    user_id = state.get("user_id")
    user_keys = await KeyService.get_all_decrypted_user_keys(user_id) if user_id else {}
    all_candidates: List[ModelCandidate] = []

    try:
        async with async_session() as session:
            stmt = (
                select(LLMModel, DBModelPricing)
                .join(DBModelPricing, LLMModel.id == DBModelPricing.model_id)
                .where(
                    LLMModel.active == True,
                    DBModelPricing.effective_to.is_(None),
                )
            )
            result = await session.execute(stmt)
            rows = result.all()

            for model, pricing in rows:
                cost = pricing.input_price_per_million * 0.75 + pricing.output_price_per_million * 0.25
                p_clean = model.provider_name.lower().strip()
                has_key = bool(user_keys.get(p_clean)) or LLMProviderClient._provider_has_api_key(p_clean)
                all_candidates.append(ModelCandidate(
                    model_id=model.id,
                    provider_name=model.provider_name,
                    model_name=model.model_name,
                    display_name=model.display_name,
                    quality=model.base_quality_score,
                    latency_ms=model.expected_latency_ms,
                    cost_per_million=cost,
                    has_api_key=has_key,
                ))
    except Exception as e:
        print(f"[select_models] DB query failed: {e}", file=sys.stderr)

    eligible = [c for c in all_candidates if c.has_api_key]

    if provider == "mock":
        provider_filtered = [c for c in all_candidates if c.provider_name == "mock"]
        if provider_filtered:
            eligible = provider_filtered
    elif provider and provider not in ("auto", "mock"):
        provider_filtered = [c for c in eligible if c.provider_name == provider]
        if provider_filtered:
            eligible = provider_filtered

    pareto_best = select_best(eligible) if eligible else None

    return {
        "candidate_models": [{"id": c.model_id, "provider": c.provider_name, "name": c.display_name} for c in all_candidates],
        "eligible_models": [{"id": c.model_id, "provider": c.provider_name, "name": c.display_name} for c in eligible],
        "pareto_models": [{"id": c.model_id, "provider": c.provider_name, "name": c.display_name, "quality": c.quality, "latency": c.latency_ms, "cost": c.cost_per_million} for c in eligible],
        "selected_model": pareto_best.model_id if pareto_best else "",
        "routing_score": 0.0,
        "routing_factors": {
            "provider_preference": provider,
            "task_type": state.get("task_type", "qa"),
            "complexity": state.get("complexity_score", 0.0),
            "pareto_selected": pareto_best is not None,
        },
    }


# =============================================================================
# Node 3: execute_tier1
# =============================================================================
async def execute_tier1(state: RouterState) -> dict:
    """Execute Tier 1 model (fast/cheap) and extract confidence."""
    from app.router.provider_client import LLMProviderClient
    from app.observability.cost_tracker import CostTracker
    from app.services.key_service import KeyService

    provider = state["provider"]
    prompt = state["user_input"]
    user_id = state.get("user_id")
    traces = list(state.get("traces", []))
    start = time.time()

    # Determine key source for UI display
    key_source = "mock"
    if provider and provider.lower() != "mock":
        key_source = "server_env"
        if user_id:
            user_key = await KeyService.get_decrypted_user_key(user_id, provider.lower())
            if user_key:
                key_source = "user_db"

    try:
        draft, conf, uncertainties, tokens, latency = await LLMProviderClient.execute_tier1(
            provider=provider,
            prompt=prompt,
            user_id=user_id,
        )
    except Exception as e:
        err_str = str(e).lower()
        reason = EscalationReason.PROVIDER_ERROR
        if "timeout" in err_str:
            reason = EscalationReason.MODEL_TIMEOUT
        elif "rate" in err_str or "429" in err_str:
            reason = EscalationReason.MODEL_RATE_LIMIT

        return {
            "tier1_draft": "",
            "tier1_confidence": 0.0,
            "tier1_uncertainty_reasons": [str(e)],
            "tier1_tokens": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "tier1_latency_ms": round((time.time() - start) * 1000, 2),
            "tier1_model_id": "",
            "tier1_model_name": "",
            "escalation_reason": reason.value,
            "status": "escalated",
            "attempts": state.get("attempts", []) + [{"node": "execute_tier1", "error": str(e)}],
        }

    model_info = await LLMProviderClient.get_model_for_provider(provider, "tier1", user_id=user_id)
    model_id = model_info[0] if model_info else ""
    model_name = model_info[2] if model_info else f"{provider} tier1"

    tier1_cost, tier1_pricing_id = await CostTracker.calculate_model_cost(
        provider=provider,
        tier="tier1",
        input_tokens=tokens.input_tokens,
        output_tokens=tokens.output_tokens,
        model_id=model_id,
    )

    trace = {
        "model_name": model_name,
        "tier": "tier1",
        "prompt": prompt,
        "response_text": draft,
        "confidence": conf,
        "uncertainty_reasons": uncertainties,
        "tokens": {"input_tokens": tokens.input_tokens, "output_tokens": tokens.output_tokens, "total_tokens": tokens.total_tokens},
        "cost_usd": tier1_cost,
        "latency_ms": latency,
        "model_id": model_id,
        "pricing_id": tier1_pricing_id,
    }
    traces.append(trace)

    return {
        "tier1_draft": draft,
        "tier1_confidence": conf,
        "tier1_uncertainty_reasons": uncertainties,
        "tier1_tokens": {"input_tokens": tokens.input_tokens, "output_tokens": tokens.output_tokens, "total_tokens": tokens.total_tokens},
        "tier1_latency_ms": latency,
        "tier1_model_id": model_id,
        "tier1_model_name": model_name,
        "traces": traces,
        "actual_cost": state.get("actual_cost", 0.0) + tier1_cost,
        "key_source": key_source,
    }


# =============================================================================
# Node 4: decide_escalation
# =============================================================================
async def decide_escalation(state: RouterState) -> dict:
    """Evaluate confidence, apply budget policy, decide whether to escalate."""
    conf = state.get("tier1_confidence", 0.0)
    threshold = state.get("confidence_threshold", 0.75)
    force_esc = state.get("force_escalation", False)
    force_t1 = state.get("force_tier1_only", False)

    if force_esc:
        return {
            "escalation_reason": EscalationReason.FORCED_OVERRIDE.value,
            "status": "escalated",
        }

    if force_t1:
        return {
            "escalation_reason": None,
            "status": "running",
        }

    if state.get("escalation_reason"):
        return {"status": "escalated"}

    if conf < threshold:
        reasons = state.get("tier1_uncertainty_reasons", [])
        reasons_str = "; ".join(reasons) if reasons else "Model expressed uncertainty"
        return {
            "escalation_reason": EscalationReason.LOW_CONFIDENCE.value,
            "status": "escalated",
        }

    return {
        "escalation_reason": None,
        "status": "running",
    }


# =============================================================================
# Node 5: execute_tier2
# =============================================================================
async def execute_tier2(state: RouterState) -> dict:
    """Execute Tier 2 (frontier) model if escalation was decided."""
    from app.router.provider_client import LLMProviderClient
    from app.observability.cost_tracker import CostTracker

    provider = state["provider"]
    prompt = state["user_input"]
    user_id = state.get("user_id")
    tier1_draft = state.get("tier1_draft", "")
    escalation_reason = state.get("escalation_reason", "LOW_CONFIDENCE")
    uncertainty = state.get("tier1_uncertainty_reasons", [])
    traces = list(state.get("traces", []))
    start = time.time()

    try:
        answer, tokens, latency = await LLMProviderClient.execute_tier2(
            provider=provider,
            prompt=prompt,
            tier1_draft=tier1_draft,
            escalation_reason=escalation_reason,
            uncertainty_reasons=uncertainty,
            user_id=user_id,
        )
    except Exception as e:
        err_str = str(e).lower()
        reason = EscalationReason.PROVIDER_ERROR
        if "timeout" in err_str:
            reason = EscalationReason.MODEL_TIMEOUT
        elif "rate" in err_str or "429" in err_str:
            reason = EscalationReason.MODEL_RATE_LIMIT

        return {
            "tier2_answer": "",
            "tier2_tokens": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "tier2_latency_ms": round((time.time() - start) * 1000, 2),
            "tier2_model_id": "",
            "tier2_model_name": "",
            "escalation_reason": reason.value,
            "final_response": state.get("tier1_draft", "Error: Tier 2 failed"),
            "attempts": state.get("attempts", []) + [{"node": "execute_tier2", "error": str(e)}],
        }

    model_info = await LLMProviderClient.get_model_for_provider(provider, "tier2", user_id=user_id)
    model_id = model_info[0] if model_info else ""
    model_name = model_info[2] if model_info else f"{provider} tier2"

    tier2_cost, tier2_pricing_id = await CostTracker.calculate_model_cost(
        provider=provider,
        tier="tier2",
        input_tokens=tokens.input_tokens,
        output_tokens=tokens.output_tokens,
        model_id=model_id,
    )

    trace = {
        "model_name": model_name,
        "tier": "tier2",
        "prompt": f"Escalation context with Draft: {tier1_draft[:100]}...",
        "response_text": answer,
        "confidence": 0.98,
        "uncertainty_reasons": [],
        "tokens": {"input_tokens": tokens.input_tokens, "output_tokens": tokens.output_tokens, "total_tokens": tokens.total_tokens},
        "cost_usd": tier2_cost,
        "latency_ms": latency,
        "model_id": model_id,
        "pricing_id": tier2_pricing_id,
    }
    traces.append(trace)

    return {
        "tier2_answer": answer,
        "tier2_tokens": {"input_tokens": tokens.input_tokens, "output_tokens": tokens.output_tokens, "total_tokens": tokens.total_tokens},
        "tier2_latency_ms": latency,
        "tier2_model_id": model_id,
        "tier2_model_name": model_name,
        "final_response": answer,
        "traces": traces,
        "actual_cost": state.get("actual_cost", 0.0) + tier2_cost,
    }


# =============================================================================
# Node 6: evaluate_quality
# =============================================================================
async def evaluate_quality(state: RouterState) -> dict:
    """Run hybrid quality evaluation (deterministic + LLM judge)."""
    if not settings.quality_evaluation_enabled:
        return {"quality_score": 0.0, "evaluation": {}}

    final_answer = state.get("final_response", state.get("tier1_draft", ""))
    prompt = state["user_input"]
    model_id = state.get("tier2_model_id") or state.get("tier1_model_id", "")
    query_id = state.get("request_id", "")

    try:
        from app.evaluation.composite import evaluate_quality as eval_quality
        from app.database import async_session

        result = await eval_quality(
            prompt=prompt,
            response=final_answer,
            model_id=model_id,
            query_id=query_id,
        )

        try:
            async with async_session() as session:
                from app.models.db_models import ModelQualityEvaluation
                eval_db = ModelQualityEvaluation(
                    id=f"qeval_{uuid.uuid4().hex[:10]}",
                    model_id=model_id,
                    query_id=query_id,
                    task_type=result["task_type"],
                    quality_score=result["quality_score"],
                    deterministic_score=result.get("deterministic_score"),
                    llm_judge_score=result.get("llm_judge_score"),
                    metrics_json=json.dumps(result.get("metrics", {})),
                )
                session.add(eval_db)
                await session.commit()
        except Exception as e:
            print(f"[evaluate_quality] DB persist failed: {e}", file=sys.stderr)

        quality_score = result["quality_score"]
        escalation_reason = state.get("escalation_reason")
        status = state.get("status", "running")

        if quality_score < settings.quality_revise_threshold:
            if not escalation_reason:
                escalation_reason = EscalationReason.LOW_QUALITY.value
            status = "escalated"

        return {
            "quality_score": quality_score,
            "evaluation": result,
            "escalation_reason": escalation_reason,
            "status": status,
        }
    except Exception as e:
        print(f"[evaluate_quality] Failed: {e}", file=sys.stderr)
        return {"quality_score": 0.0, "evaluation": {}}


# =============================================================================
# Node 7: recover_quality
# =============================================================================
async def recover_quality(state: RouterState) -> dict:
    """Attempt quality revision if score is below accept threshold."""
    from app.database import async_session

    if not settings.quality_recovery_enabled:
        return {"quality_recovery": None}

    quality_score = state.get("quality_score", 0.0)
    if quality_score >= settings.quality_accept_threshold:
        return {"quality_recovery": None}

    final_answer = state.get("final_response", state.get("tier1_draft", ""))
    prompt = state["user_input"]
    provider = state["provider"]
    model_id = state.get("tier2_model_id") or state.get("tier1_model_id", "")
    model_name = state.get("tier2_model_name") or state.get("tier1_model_name", "")
    tier = "tier2" if state.get("tier2_model_id") else "tier1"

    try:
        from app.evaluation.recovery import apply_quality_recovery

        result = await apply_quality_recovery(
            prompt=prompt,
            current_answer=final_answer,
            current_provider=provider,
            current_model_id=model_id,
            current_model_name=model_name,
            current_tier=tier,
            quality_score=quality_score,
            quality_metrics=state.get("evaluation", {}).get("metrics", {}),
        )

        recovery_dict = {
            "action_taken": result.action_taken,
            "original_score": result.original_score,
            "final_score": result.final_score,
            "revision_attempts": result.revision_attempts,
            "recovery_model": result.recovery_model,
            "recovery_model_id": result.recovery_model_id,
            "recovery_cost_usd": result.recovery_cost_usd,
            "recovery_latency_ms": result.recovery_latency_ms,
        }

        new_answer = state.get("final_response", "")
        new_model = model_name
        new_tier = tier
        traces = list(state.get("traces", []))
        escalation_reason = state.get("escalation_reason")

        if result.action_taken in ("revise_success", "escalate"):
            new_answer = result.final_answer
            new_model = result.recovery_model
            traces.append({
                "model_name": result.recovery_model,
                "tier": f"recovery_{tier}",
                "prompt": f"Quality recovery ({result.action_taken})",
                "response_text": result.final_answer,
                "confidence": None,
                "uncertainty_reasons": [],
                "tokens": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                "cost_usd": result.recovery_cost_usd,
                "latency_ms": result.recovery_latency_ms,
                "model_id": result.recovery_model_id,
            })

        if result.action_taken == "revise_failed":
            escalation_reason = EscalationReason.QUALITY_REVISION_FAILED.value

        try:
            async with async_session() as session:
                from app.models.db_models import ModelQualityRecovery
                recovery_db = ModelQualityRecovery(
                    id=f"qrec_{uuid.uuid4().hex[:10]}",
                    model_id=model_id,
                    query_id=state.get("request_id", ""),
                    original_quality_score=result.original_score,
                    final_quality_score=result.final_score,
                    action_taken=result.action_taken,
                    revision_attempts=result.revision_attempts,
                    recovery_model=result.recovery_model,
                    recovery_model_id=result.recovery_model_id,
                    recovery_cost_usd=result.recovery_cost_usd,
                    recovery_latency_ms=result.recovery_latency_ms,
                )
                session.add(recovery_db)
                await session.commit()
        except Exception as e:
            print(f"[recover_quality] DB persist failed: {e}", file=sys.stderr)

        return {
            "final_response": new_answer,
            "traces": traces,
            "actual_cost": state.get("actual_cost", 0.0) + result.recovery_cost_usd,
            "quality_recovery": recovery_dict,
            "escalation_reason": escalation_reason,
        }
    except Exception as e:
        print(f"[recover_quality] Failed: {e}", file=sys.stderr)
        return {"quality_recovery": None}


# =============================================================================
# Node 8: compute_costs
# =============================================================================
async def compute_costs(state: RouterState) -> dict:
    """Calculate full cost breakdown and audit justification."""
    from app.observability.cost_tracker import CostTracker

    provider = state["provider"]
    tier1_tokens_raw = state.get("tier1_tokens", {})
    tier2_tokens_raw = state.get("tier2_tokens", {})

    tier1_tokens = TokenMetrics(
        input_tokens=tier1_tokens_raw.get("input_tokens", 0),
        output_tokens=tier1_tokens_raw.get("output_tokens", 0),
        total_tokens=tier1_tokens_raw.get("total_tokens", 0),
    )
    tier2_tokens = TokenMetrics(
        input_tokens=tier2_tokens_raw.get("input_tokens", 0),
        output_tokens=tier2_tokens_raw.get("output_tokens", 0),
        total_tokens=tier2_tokens_raw.get("total_tokens", 0),
    )

    from app.models.schemas import EscalationEvent
    escalation = EscalationEvent(
        escalated=state.get("status") == "escalated",
        reason=state.get("escalation_reason"),
        explanation=None,
        trigger_confidence=state.get("tier1_confidence"),
        threshold=state.get("confidence_threshold"),
    )

    breakdown = await CostTracker.calculate_cost_breakdown(
        provider=provider,
        tier1_tokens=tier1_tokens,
        tier2_tokens=tier2_tokens,
        escalation=escalation,
        tier1_model_id=state.get("tier1_model_id"),
        tier2_model_id=state.get("tier2_model_id"),
    )

    return {
        "cost_breakdown": {
            "tier1_cost_usd": breakdown.tier1_cost_usd,
            "tier2_cost_usd": breakdown.tier2_cost_usd,
            "total_cost_usd": breakdown.total_cost_usd,
            "baseline_sonnet_cost_usd": breakdown.baseline_sonnet_cost_usd,
            "savings_usd": breakdown.savings_usd,
            "savings_percent": breakdown.savings_percent,
            "currency": breakdown.currency,
            "spend_justification": breakdown.spend_justification,
            "tier1_pricing_id": breakdown.tier1_pricing_id,
            "tier2_pricing_id": breakdown.tier2_pricing_id,
        },
        "estimated_cost": breakdown.total_cost_usd,
    }


# =============================================================================
# Node 9: finalize
# =============================================================================
async def finalize(state: RouterState) -> dict:
    """Assemble final response and persist audit history."""
    from app.persistence.history_store import history_store
    from app.models.schemas import QueryHistoryItem

    tier1_tokens = state.get("tier1_tokens", {})
    tier2_tokens = state.get("tier2_tokens", {})
    cost = state.get("cost_breakdown", {})
    utc_now = datetime.now(timezone.utc)

    is_escalated = state.get("status") == "escalated"
    served_by_tier = "tier2" if is_escalated and state.get("tier2_answer") else "tier1"
    served_by_model = state.get("tier2_model_name") or state.get("tier1_model_name", "")
    final_response = state.get("final_response", state.get("tier1_draft", ""))

    history_item = QueryHistoryItem(
        id=state["request_id"],
        timestamp=utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        prompt=state["user_input"],
        final_answer=final_response,
        provider=state["provider"],
        served_by_model=served_by_model,
        served_by_tier=served_by_tier,
        confidence=state.get("tier1_confidence", 0.0),
        escalated=is_escalated,
        escalation_reason=state.get("escalation_reason"),
        total_tokens=tier1_tokens.get("total_tokens", 0) + tier2_tokens.get("total_tokens", 0),
        total_cost_usd=cost.get("total_cost_usd", 0.0),
        savings_usd=cost.get("savings_usd", 0.0),
        spend_justification=cost.get("spend_justification", ""),
        tier1_pricing_id=cost.get("tier1_pricing_id"),
        tier2_pricing_id=cost.get("tier2_pricing_id"),
    )
    history_store.add(history_item)

    return {
        "final_response": final_response,
        "status": "completed" if final_response else "failed",
    }
