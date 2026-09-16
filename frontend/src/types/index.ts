export interface TokenMetrics {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface ModelExecutionTrace {
  model_name: string;
  tier: "tier1" | "tier2";
  prompt: string;
  response_text: string;
  confidence?: number;
  uncertainty_reasons: string[];
  tokens: TokenMetrics;
  cost_usd: number;
  latency_ms: number;
}

export interface EscalationEvent {
  escalated: boolean;
  reason?: string;
  explanation?: string;
  trigger_confidence?: number;
  threshold?: number;
}

export interface CostBreakdown {
  tier1_cost_usd: number;
  tier2_cost_usd: number;
  total_cost_usd: number;
  baseline_sonnet_cost_usd: number;
  savings_usd: number;
  savings_percent: number;
  currency: string;
  spend_justification: string;
}

export interface QualityEvaluationResult {
  task_type: string;
  quality_score: number;
  deterministic_score?: number;
  llm_judge_score?: number;
  metrics: Record<string, number>;
}

export interface QualityRecoveryResult {
  action_taken: string;
  original_score: number;
  final_score?: number;
  revision_attempts: number;
  recovery_model?: string;
  recovery_model_id?: string;
  recovery_cost_usd: number;
  recovery_latency_ms: number;
}

export interface ChatResponse {
  id: string;
  prompt: string;
  final_answer: string;
  served_by_tier: "tier1" | "tier2";
  served_by_model: string;
  confidence: number;
  escalation: EscalationEvent;
  traces: ModelExecutionTrace[];
  cost_breakdown: CostBreakdown;
  total_latency_ms: number;
  quality_evaluation?: QualityEvaluationResult;
  quality_recovery?: QualityRecoveryResult;
  timestamp: string;
}

export interface QueryHistoryItem {
  id: string;
  timestamp: string;
  prompt: string;
  final_answer: string;
  provider: string;
  served_by_model: string;
  served_by_tier: string;
  confidence: number;
  escalated: boolean;
  escalation_reason?: string;
  total_tokens: number;
  total_cost_usd: number;
  savings_usd: number;
  spend_justification: string;
}

export interface AnalyticsSummary {
  total_queries: number;
  total_spend_usd: number;
  total_baseline_cost_usd: number;
  total_savings_usd: number;
  average_savings_percent: number;
  escalation_rate_percent: number;
  tier1_handled_count: number;
  tier2_escalated_count: number;
  escalation_reasons_breakdown: Record<string, number>;
}
