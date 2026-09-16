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

export type EscalationReason =
  | "LOW_CONFIDENCE"
  | "LOW_QUALITY"
  | "TOOL_FAILURE"
  | "MODEL_TIMEOUT"
  | "MODEL_RATE_LIMIT"
  | "PROVIDER_ERROR"
  | "BUDGET_POLICY"
  | "CONTEXT_LIMIT"
  | "STRUCTURED_OUTPUT_FAILURE"
  | "PROMPT_INJECTION_RISK"
  | "QUALITY_REVISION_FAILED"
  | "FORCED_OVERRIDE";

export const ESCALATION_LABELS: Record<EscalationReason, string> = {
  LOW_CONFIDENCE: "Low Confidence",
  LOW_QUALITY: "Low Quality Score",
  TOOL_FAILURE: "Tool Execution Failure",
  MODEL_TIMEOUT: "Model Timeout",
  MODEL_RATE_LIMIT: "Model Rate Limit",
  PROVIDER_ERROR: "Provider Error",
  BUDGET_POLICY: "Budget Policy Override",
  CONTEXT_LIMIT: "Context Window Exceeded",
  STRUCTURED_OUTPUT_FAILURE: "Structured Output Failure",
  PROMPT_INJECTION_RISK: "Prompt Injection Risk",
  QUALITY_REVISION_FAILED: "Quality Revision Failed",
  FORCED_OVERRIDE: "Forced Tier 2 Override",
};

export const ESCALATION_COLORS: Record<EscalationReason, string> = {
  LOW_CONFIDENCE: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  LOW_QUALITY: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  TOOL_FAILURE: "bg-red-500/20 text-red-300 border-red-500/30",
  MODEL_TIMEOUT: "bg-red-500/20 text-red-300 border-red-500/30",
  MODEL_RATE_LIMIT: "bg-red-500/20 text-red-300 border-red-500/30",
  PROVIDER_ERROR: "bg-red-500/20 text-red-300 border-red-500/30",
  BUDGET_POLICY: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  CONTEXT_LIMIT: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  STRUCTURED_OUTPUT_FAILURE: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  PROMPT_INJECTION_RISK: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  QUALITY_REVISION_FAILED: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  FORCED_OVERRIDE: "bg-neutral-500/20 text-neutral-300 border-neutral-500/30",
};

export interface EscalationEvent {
  escalated: boolean;
  reason?: EscalationReason | string | null;
  explanation?: string | null;
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
  key_source?: "user_db" | "server_env" | "mock";
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
