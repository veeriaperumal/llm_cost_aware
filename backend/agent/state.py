from typing import TypedDict, Optional


class RouterState(TypedDict):
    request_id: str
    tenant_id: str
    user_id: Optional[str]

    task_type: str
    user_input: str

    complexity_score: float
    requires_tools: bool

    candidate_models: list
    eligible_models: list
    pareto_models: list

    selected_model: str
    routing_score: float
    routing_factors: dict

    attempts: list
    tool_calls: list

    quality_score: float
    evaluation: dict

    escalation_reason: Optional[str]
    retry_count: int

    budget_remaining: float
    estimated_cost: float
    actual_cost: float

    final_response: str
    status: str

    provider: str
    confidence_threshold: float
    force_escalation: bool
    force_tier1_only: bool

    tier1_draft: str
    tier1_confidence: float
    tier1_uncertainty_reasons: list
    tier1_tokens: dict
    tier1_latency_ms: float
    tier1_model_id: str
    tier1_model_name: str

    tier2_answer: str
    tier2_tokens: dict
    tier2_latency_ms: float
    tier2_model_id: str
    tier2_model_name: str

    traces: list
    cost_breakdown: dict
    quality_evaluation: Optional[dict]
    quality_recovery: Optional[dict]

    key_source: Optional[str]
