import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.models.schemas import ChatRequest
from app.graph.cascading_router import CascadingRouter
from app.observability.cost_tracker import CostTracker
from config.settings import settings

@pytest.mark.asyncio
async def test_simple_query_routes_to_tier1_only():
    """Simple query should have high confidence and NOT escalate."""
    request = ChatRequest(
        prompt="What is the capital of France?",
        provider="mock",
        confidence_threshold=0.75
    )
    response = await CascadingRouter.process_query(request)
    
    assert response.confidence >= 0.75
    assert response.escalation.escalated is False
    assert response.served_by_tier == "tier1"
    assert response.cost_breakdown.tier2_cost_usd == 0.0
    assert response.cost_breakdown.savings_usd > 0
    assert "Budget saved!" in response.cost_breakdown.spend_justification

@pytest.mark.asyncio
async def test_complex_query_triggers_escalation_with_reason():
    """Complex query should have low confidence (e.g. 0.61) and trigger ESCALATION with reason 'low_confidence'."""
    request = ChatRequest(
        prompt="How to design a distributed consensus algorithm with high throughput and low latency tradeoff proof?",
        provider="mock",
        confidence_threshold=0.75
    )
    response = await CascadingRouter.process_query(request)
    
    assert response.confidence < 0.75
    assert response.escalation.escalated is True
    assert response.escalation.reason == "low_confidence"
    assert response.served_by_tier == "tier2"
    assert response.cost_breakdown.tier2_cost_usd > 0.0
    assert len(response.traces) == 2  # Tier 1 (Haiku) trace + Tier 2 (Sonnet) trace
    assert "Extra spend incurred" in response.cost_breakdown.spend_justification
    assert "low_confidence" in response.cost_breakdown.spend_justification

@pytest.mark.asyncio
async def test_forced_escalation():
    """Testing force_escalation override flag."""
    request = ChatRequest(
        prompt="Simple question",
        provider="mock",
        force_escalation=True
    )
    response = await CascadingRouter.process_query(request)
    assert response.escalation.escalated is True
    assert response.escalation.reason == "forced_override"
    assert response.served_by_tier == "tier2"

@pytest.mark.asyncio
async def test_cost_tracker_calculation():
    """Validate cost calculation for Haiku vs Sonnet tokens."""
    # 1,000 input tokens + 500 output tokens on Anthropic Haiku ($0.80 / $4.00 per 1M)
    haiku_cost, _ = await CostTracker.calculate_model_cost("anthropic", "tier1", 1000, 500)
    expected_haiku = (1000 / 1_000_000 * 0.80) + (500 / 1_000_000 * 4.00)
    assert haiku_cost == round(expected_haiku, 6)
    
    # 1,000 input tokens + 500 output tokens on Anthropic Sonnet ($3.00 / $15.00 per 1M)
    sonnet_cost, _ = await CostTracker.calculate_model_cost("anthropic", "tier2", 1000, 500)
    expected_sonnet = (1000 / 1_000_000 * 3.00) + (500 / 1_000_000 * 15.00)
    assert sonnet_cost == round(expected_sonnet, 6)
    assert sonnet_cost > haiku_cost
