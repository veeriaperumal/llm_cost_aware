from typing import Dict, Any, List, Optional, Tuple
from config.settings import settings, ModelPricing
from app.models.schemas import TokenMetrics, CostBreakdown, EscalationEvent


class CostTracker:
    _db_cache: Dict[str, Tuple[str, float, float]] = {}

    @staticmethod
    async def _get_db_pricing_by_model_id(model_id: str) -> Optional[Tuple[str, float, float]]:
        try:
            from sqlalchemy import select
            from app.database import async_session
            from app.models.db_models import ModelPricing as DBModelPricing

            async with async_session() as session:
                stmt = (
                    select(DBModelPricing)
                    .where(
                        DBModelPricing.model_id == model_id,
                        DBModelPricing.effective_to.is_(None),
                    )
                    .limit(1)
                )
                result = await session.execute(stmt)
                pricing = result.scalars().first()
                if pricing:
                    return (pricing.id, pricing.input_price_per_million, pricing.output_price_per_million)
        except Exception:
            pass
        return None

    @staticmethod
    async def _get_db_pricing(provider: str, tier: str) -> Optional[Tuple[str, float, float]]:
        try:
            from sqlalchemy import select
            from app.database import async_session
            from app.models.db_models import LLMModel, ModelPricing as DBModelPricing

            async with async_session() as session:
                stmt = (
                    select(LLMModel, DBModelPricing)
                    .join(DBModelPricing, LLMModel.id == DBModelPricing.model_id)
                    .where(
                        LLMModel.provider_name == provider,
                        LLMModel.tier == tier,
                        LLMModel.active == True,
                        DBModelPricing.effective_to.is_(None),
                    )
                    .limit(1)
                )
                result = await session.execute(stmt)
                row = result.first()
                if row:
                    model, pricing = row
                    return (pricing.id, pricing.input_price_per_million, pricing.output_price_per_million)
        except Exception:
            pass
        return None

    @staticmethod
    async def calculate_model_cost(
        provider: str, tier: str, input_tokens: int, output_tokens: int,
        model_id: Optional[str] = None,
    ) -> Tuple[float, Optional[str]]:
        db_pricing = None
        if model_id:
            db_pricing = await CostTracker._get_db_pricing_by_model_id(model_id)
        if not db_pricing:
            db_pricing = await CostTracker._get_db_pricing(provider, tier)

        if db_pricing:
            pricing_id, input_cost_per_m, output_cost_per_m = db_pricing
        else:
            provider_catalog = settings.pricing_catalog.get(provider.lower(), settings.pricing_catalog["mock"])
            pricing: ModelPricing = provider_catalog.get(tier, provider_catalog["tier1"])
            input_cost_per_m = pricing.input_cost_per_million
            output_cost_per_m = pricing.output_cost_per_million
            pricing_id = None

        input_cost = (input_tokens / 1_000_000.0) * input_cost_per_m
        output_cost = (output_tokens / 1_000_000.0) * output_cost_per_m
        return round(input_cost + output_cost, 6), pricing_id

    @staticmethod
    async def calculate_cost_breakdown(
        provider: str,
        tier1_tokens: TokenMetrics,
        tier2_tokens: TokenMetrics,
        escalation: EscalationEvent,
        tier1_model_id: Optional[str] = None,
        tier2_model_id: Optional[str] = None,
    ) -> CostBreakdown:
        tier1_cost, tier1_pricing_id = await CostTracker.calculate_model_cost(
            provider, "tier1", tier1_tokens.input_tokens, tier1_tokens.output_tokens,
            model_id=tier1_model_id,
        )

        tier2_cost = 0.0
        tier2_pricing_id = None
        if escalation.escalated:
            tier2_cost, tier2_pricing_id = await CostTracker.calculate_model_cost(
                provider, "tier2", tier2_tokens.input_tokens, tier2_tokens.output_tokens,
                model_id=tier2_model_id,
            )

        total_cost = round(tier1_cost + tier2_cost, 6)

        total_input = tier1_tokens.input_tokens
        total_output = tier2_tokens.output_tokens if escalation.escalated else tier1_tokens.output_tokens
        baseline_cost, _ = await CostTracker.calculate_model_cost(provider, "tier2", total_input, total_output)

        savings = round(baseline_cost - total_cost, 6)
        savings_pct = 0.0
        if baseline_cost > 0:
            savings_pct = round(max(-100.0, min(100.0, (savings / baseline_cost) * 100.0)), 2)

        if escalation.escalated:
            spend_justification = (
                f"Extra spend incurred: Tier 1 confidence was {escalation.trigger_confidence:.2f} "
                f"(below threshold {escalation.threshold:.2f}). Escalated to Tier 2 with reason '{escalation.reason}' "
                f"to guarantee answer accuracy for a complex inquiry."
            )
        else:
            spend_justification = (
                f"Budget saved! Tier 1 solved with high confidence ({escalation.trigger_confidence:.2f} >= {escalation.threshold:.2f}). "
                f"Avoided costly Tier 2 invocation, saving ${max(0.0, savings):.6f} ({max(0.0, savings_pct)}%)."
            )

        return CostBreakdown(
            tier1_cost_usd=tier1_cost,
            tier2_cost_usd=tier2_cost,
            total_cost_usd=total_cost,
            baseline_sonnet_cost_usd=baseline_cost,
            savings_usd=savings,
            savings_percent=savings_pct,
            spend_justification=spend_justification,
            tier1_pricing_id=tier1_pricing_id,
            tier2_pricing_id=tier2_pricing_id,
        )
