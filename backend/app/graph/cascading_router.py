import uuid
import time
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# Ensure both root and backend dirs are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    from config.settings import settings
    from app.models.schemas import (
        ChatRequest, ChatResponse, ModelExecutionTrace,
        EscalationEvent, TokenMetrics, QueryHistoryItem
    )
    from app.router.provider_client import LLMProviderClient
    from app.observability.cost_tracker import CostTracker
    from app.persistence.history_store import history_store
except ImportError:
    from config.settings import settings
    from app.models.schemas import (
        ChatRequest, ChatResponse, ModelExecutionTrace,
        EscalationEvent, TokenMetrics, QueryHistoryItem
    )
    from app.router.provider_client import LLMProviderClient
    from app.observability.cost_tracker import CostTracker
    from app.persistence.history_store import history_store

class CascadingRouter:
    """
    Cascading Multi-Tier LLM Router.
    Implements:
      User Prompt -> Tier 1 (Haiku) -> Confidence Evaluation -> Decision Edge
        -> If confidence < threshold: ESCALATE (reason="low_confidence") -> Tier 2 (Sonnet) -> Final Answer
        -> Else: Tier 1 Direct -> Final Answer
      Cost & Audit Ledger logs why the extra money was spent.
    """

    @classmethod
    async def process_query(cls, request: ChatRequest) -> ChatResponse:
        total_start = time.time()
        query_id = f"qry_{uuid.uuid4().hex[:10]}"
        provider = (request.provider or settings.default_provider).lower()
        threshold = request.confidence_threshold if request.confidence_threshold is not None else settings.confidence_threshold

        provider_catalog = settings.pricing_catalog.get(provider, settings.pricing_catalog["mock"])
        tier1_meta = provider_catalog.get("tier1", provider_catalog["tier1"])
        tier2_meta = provider_catalog.get("tier2", provider_catalog["tier2"])

        traces: List[ModelExecutionTrace] = []

        # ---------------------------------------------------------------------
        # STEP 1: Execute Tier 1 Model (Haiku / Flash / Fast)
        # ---------------------------------------------------------------------
        tier1_draft, tier1_conf, tier1_uncertainties, tier1_tokens, tier1_latency = await LLMProviderClient.execute_tier1(
            provider=provider,
            prompt=request.prompt
        )

        tier1_cost = CostTracker.calculate_model_cost(
            provider=provider,
            tier="tier1",
            input_tokens=tier1_tokens.input_tokens,
            output_tokens=tier1_tokens.output_tokens
        )

        tier1_trace = ModelExecutionTrace(
            model_name=tier1_meta.name,
            tier="tier1",
            prompt=request.prompt,
            response_text=tier1_draft,
            confidence=tier1_conf,
            uncertainty_reasons=tier1_uncertainties,
            tokens=tier1_tokens,
            cost_usd=tier1_cost,
            latency_ms=tier1_latency
        )
        traces.append(tier1_trace)

        # ---------------------------------------------------------------------
        # STEP 2: Confidence Decision Gate & Escalation Check
        # ---------------------------------------------------------------------
        should_escalate = False
        escalation_reason: Optional[str] = None
        escalation_explanation: Optional[str] = None

        if request.force_escalation:
            should_escalate = True
            escalation_reason = "forced_override"
            escalation_explanation = "Manual test override forced Tier 2 escalation."
        elif not request.force_tier1_only and tier1_conf < threshold:
            should_escalate = True
            escalation_reason = "low_confidence"
            reasons_str = "; ".join(tier1_uncertainties) if tier1_uncertainties else "Model expressed uncertainty on reasoning/nuance"
            escalation_explanation = f"Confidence {tier1_conf:.2f} is below threshold {threshold:.2f}. Identified flags: {reasons_str}"

        escalation_event = EscalationEvent(
            escalated=should_escalate,
            reason=escalation_reason,
            explanation=escalation_explanation,
            trigger_confidence=tier1_conf,
            threshold=threshold
        )

        # ---------------------------------------------------------------------
        # STEP 3: Execute Tier 2 Model (Sonnet / Frontier) if Escalated
        # ---------------------------------------------------------------------
        tier2_tokens = TokenMetrics()
        final_answer = tier1_draft
        served_by_tier = "tier1"
        served_by_model = tier1_meta.name

        if should_escalate:
            tier2_answer, tier2_tokens, tier2_latency = await LLMProviderClient.execute_tier2(
                provider=provider,
                prompt=request.prompt,
                tier1_draft=tier1_draft,
                escalation_reason=escalation_reason or "low_confidence",
                uncertainty_reasons=tier1_uncertainties
            )

            tier2_cost = CostTracker.calculate_model_cost(
                provider=provider,
                tier="tier2",
                input_tokens=tier2_tokens.input_tokens,
                output_tokens=tier2_tokens.output_tokens
            )

            tier2_trace = ModelExecutionTrace(
                model_name=tier2_meta.name,
                tier="tier2",
                prompt=f"Escalation context with Draft: {tier1_draft[:100]}...",
                response_text=tier2_answer,
                confidence=0.98,
                uncertainty_reasons=[],
                tokens=tier2_tokens,
                cost_usd=tier2_cost,
                latency_ms=tier2_latency
            )
            traces.append(tier2_trace)

            final_answer = tier2_answer
            served_by_tier = "tier2"
            served_by_model = tier2_meta.name

        # ---------------------------------------------------------------------
        # STEP 4: Calculate Cost Breakdown & Audit Justification
        # ---------------------------------------------------------------------
        cost_breakdown = CostTracker.calculate_cost_breakdown(
            provider=provider,
            tier1_tokens=tier1_tokens,
            tier2_tokens=tier2_tokens,
            escalation=escalation_event
        )

        total_latency_ms = round((time.time() - total_start) * 1000, 2)
        utc_now = datetime.now(timezone.utc)

        response = ChatResponse(
            id=query_id,
            prompt=request.prompt,
            final_answer=final_answer,
            served_by_tier=served_by_tier,
            served_by_model=served_by_model,
            confidence=tier1_conf,
            escalation=escalation_event,
            traces=traces,
            cost_breakdown=cost_breakdown,
            total_latency_ms=total_latency_ms,
            timestamp=utc_now
        )

        # ---------------------------------------------------------------------
        # STEP 5: Persist Audit History
        # ---------------------------------------------------------------------
        history_item = QueryHistoryItem(
            id=query_id,
            timestamp=utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            prompt=request.prompt,
            final_answer=final_answer,
            provider=provider,
            served_by_model=served_by_model,
            served_by_tier=served_by_tier,
            confidence=tier1_conf,
            escalated=should_escalate,
            escalation_reason=escalation_reason,
            total_tokens=tier1_tokens.total_tokens + tier2_tokens.total_tokens,
            total_cost_usd=cost_breakdown.total_cost_usd,
            savings_usd=cost_breakdown.savings_usd,
            spend_justification=cost_breakdown.spend_justification
        )
        history_store.add(history_item)

        return response
