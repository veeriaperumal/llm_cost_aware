from typing import Dict, Any, List
from config.settings import settings, ModelPricing
from app.models.schemas import TokenMetrics, CostBreakdown, EscalationEvent

class CostTracker:
    @staticmethod
    def calculate_model_cost(provider: str, tier: str, input_tokens: int, output_tokens: int) -> float:
        provider_catalog = settings.pricing_catalog.get(provider.lower(), settings.pricing_catalog["mock"])
        pricing: ModelPricing = provider_catalog.get(tier, provider_catalog["tier1"])
        
        input_cost = (input_tokens / 1_000_000.0) * pricing.input_cost_per_million
        output_cost = (output_tokens / 1_000_000.0) * pricing.output_cost_per_million
        return round(input_cost + output_cost, 6)

    @staticmethod
    def calculate_cost_breakdown(
        provider: str,
        tier1_tokens: TokenMetrics,
        tier2_tokens: TokenMetrics,
        escalation: EscalationEvent
    ) -> CostBreakdown:
        tier1_cost = CostTracker.calculate_model_cost(provider, "tier1", tier1_tokens.input_tokens, tier1_tokens.output_tokens)
        
        tier2_cost = 0.0
        if escalation.escalated:
            tier2_cost = CostTracker.calculate_model_cost(provider, "tier2", tier2_tokens.input_tokens, tier2_tokens.output_tokens)
            
        total_cost = round(tier1_cost + tier2_cost, 6)
        
        # Baseline is what we would have paid if we routed directly to Tier 2 (Sonnet) alone without cascade
        total_input = tier1_tokens.input_tokens
        total_output = tier2_tokens.output_tokens if escalation.escalated else tier1_tokens.output_tokens
        baseline_cost = CostTracker.calculate_model_cost(provider, "tier2", total_input, total_output)
        
        # Savings
        savings = round(baseline_cost - total_cost, 6)
        savings_pct = 0.0
        if baseline_cost > 0:
            savings_pct = round(max(-100.0, min(100.0, (savings / baseline_cost) * 100.0)), 2)

        # Build Business Spend Justification
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
            spend_justification=spend_justification
        )
