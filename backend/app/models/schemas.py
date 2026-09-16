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
    model_id: Optional[str] = None
    pricing_id: Optional[str] = None
    pareto_score: Optional[float] = None
    pareto_rank: Optional[int] = None

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
    tier1_pricing_id: Optional[str] = None
    tier2_pricing_id: Optional[str] = None

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
    quality_evaluation: Optional[QualityEvaluationResult] = None
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
    tier1_pricing_id: Optional[str] = None
    tier2_pricing_id: Optional[str] = None

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


class ModelPricingInfo(BaseModel):
    id: str
    input_price_per_million: float
    output_price_per_million: float
    cached_input_price_per_million: float = 0.0
    currency: str = "USD"
    effective_from: str
    effective_to: Optional[str] = None


class ModelInfo(BaseModel):
    id: str
    provider_name: str
    model_name: str
    display_name: str
    tier: str
    active: bool = True
    context_window: int = 0
    supports_tools: bool = False
    supports_json: bool = False
    supports_streaming: bool = True
    supports_prompt_cache: bool = False
    base_quality_score: float = 0.0
    expected_latency_ms: int = 0
    active_pricing: Optional[ModelPricingInfo] = None
    pareto_score: Optional[float] = None
    pareto_rank: Optional[int] = None


class QualityEvaluationResult(BaseModel):
    task_type: str
    quality_score: float
    deterministic_score: Optional[float] = None
    llm_judge_score: Optional[float] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class QualityHistoryItem(BaseModel):
    id: str
    model_id: str
    model_name: str
    provider_name: str
    query_id: str
    task_type: str
    quality_score: float
    deterministic_score: Optional[float] = None
    llm_judge_score: Optional[float] = None
    metrics_json: str = "{}"
    evaluated_at: str
