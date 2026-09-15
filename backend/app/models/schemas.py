from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class ChatRequest(BaseModel):
    prompt: str = Field(..., description="User prompt or question to process")
    provider: Optional[str] = Field(None, description="Provider to use: gemini, groq, openai, mistral, anthropic, mock")
    confidence_threshold: Optional[float] = Field(0.75, ge=0.0, le=1.0, description="Confidence threshold for escalation")
    force_escalation: Optional[bool] = Field(False, description="Force Tier 2 escalation for testing")
    force_tier1_only: Optional[bool] = Field(False, description="Force Tier 1 response only without escalation")

class TokenMetrics(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

class ModelExecutionTrace(BaseModel):
    model_name: str
    tier: str  # "tier1" or "tier2"
    prompt: str
    response_text: str
    confidence: Optional[float] = None
    uncertainty_reasons: List[str] = Field(default_factory=list)
    tokens: TokenMetrics
    cost_usd: float
    latency_ms: float

class EscalationEvent(BaseModel):
    escalated: bool
    reason: Optional[str] = None  # e.g., "low_confidence", "complexity_detected", "manual_override"
    explanation: Optional[str] = None
    trigger_confidence: Optional[float] = None
    threshold: Optional[float] = None

class CostBreakdown(BaseModel):
    tier1_cost_usd: float = 0.0
    tier2_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    baseline_sonnet_cost_usd: float = 0.0
    savings_usd: float = 0.0
    savings_percent: float = 0.0
    currency: str = "USD"
    spend_justification: str  # Explains clearly why extra money was (or wasn't) spent

class ChatResponse(BaseModel):
    id: str
    prompt: str
    final_answer: str
    served_by_tier: str  # "tier1" or "tier2"
    served_by_model: str
    confidence: float
    escalation: EscalationEvent
    traces: List[ModelExecutionTrace]
    cost_breakdown: CostBreakdown
    total_latency_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QueryHistoryItem(BaseModel):
    id: str
    timestamp: str
    prompt: str
    final_answer: str
    provider: str
    served_by_model: str
    served_by_tier: str
    confidence: float
    escalated: bool
    escalation_reason: Optional[str]
    total_tokens: int
    total_cost_usd: float
    savings_usd: float
    spend_justification: str

class AnalyticsSummary(BaseModel):
    total_queries: int = 0
    total_spend_usd: float = 0.0
    total_baseline_cost_usd: float = 0.0
    total_savings_usd: float = 0.0
    average_savings_percent: float = 0.0
    escalation_rate_percent: float = 0.0
    tier1_handled_count: int = 0
    tier2_escalated_count: int = 0
    escalation_reasons_breakdown: Dict[str, int] = Field(default_factory=dict)
