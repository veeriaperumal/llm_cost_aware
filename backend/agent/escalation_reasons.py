from enum import Enum


class EscalationReason(str, Enum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    LOW_QUALITY = "LOW_QUALITY"
    TOOL_FAILURE = "TOOL_FAILURE"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    MODEL_RATE_LIMIT = "MODEL_RATE_LIMIT"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    BUDGET_POLICY = "BUDGET_POLICY"
    CONTEXT_LIMIT = "CONTEXT_LIMIT"
    STRUCTURED_OUTPUT_FAILURE = "STRUCTURED_OUTPUT_FAILURE"
    PROMPT_INJECTION_RISK = "PROMPT_INJECTION_RISK"
    QUALITY_REVISION_FAILED = "QUALITY_REVISION_FAILED"
    FORCED_OVERRIDE = "FORCED_OVERRIDE"


ESCALATION_LABELS = {
    EscalationReason.LOW_CONFIDENCE: "Low Confidence",
    EscalationReason.LOW_QUALITY: "Low Quality Score",
    EscalationReason.TOOL_FAILURE: "Tool Execution Failure",
    EscalationReason.MODEL_TIMEOUT: "Model Timeout",
    EscalationReason.MODEL_RATE_LIMIT: "Model Rate Limit",
    EscalationReason.PROVIDER_ERROR: "Provider Error",
    EscalationReason.BUDGET_POLICY: "Budget Policy Override",
    EscalationReason.CONTEXT_LIMIT: "Context Window Exceeded",
    EscalationReason.STRUCTURED_OUTPUT_FAILURE: "Structured Output Failure",
    EscalationReason.PROMPT_INJECTION_RISK: "Prompt Injection Risk",
    EscalationReason.QUALITY_REVISION_FAILED: "Quality Revision Failed",
    EscalationReason.FORCED_OVERRIDE: "Forced Tier 2 Override",
}
