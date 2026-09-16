import time
import sys
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any

from config.settings import settings
from app.models.schemas import TokenMetrics


@dataclass
class RecoveryDecision:
    action: str              # "accept" | "revise" | "escalate"
    quality_score: float
    reason: str


@dataclass
class RecoveryResult:
    original_answer: str
    final_answer: str
    original_score: float
    final_score: Optional[float] = None
    action_taken: str = "accept"  # accept | revise_success | revise_failed | escalate | tier2_best_available
    revision_attempts: int = 0
    recovery_model: str = ""
    recovery_model_id: Optional[str] = None
    recovery_cost_usd: float = 0.0
    recovery_latency_ms: float = 0.0
    recovery_tokens: Optional[TokenMetrics] = None


def decide_action(score: float, tier: str) -> RecoveryDecision:
    """Apply thresholds to decide accept/revise/escalate.

    If tier2 and action would be escalate, return accept (best available).
    """
    accept_threshold = settings.quality_accept_threshold
    revise_threshold = settings.quality_revise_threshold

    if score >= accept_threshold:
        return RecoveryDecision(
            action="accept",
            quality_score=score,
            reason=f"Score {score:.2f} >= accept threshold {accept_threshold:.2f}",
        )

    if score >= revise_threshold:
        if tier == "tier2":
            return RecoveryDecision(
                action="accept",
                quality_score=score,
                reason=f"Score {score:.2f} is in revise range but already on tier2 (best available)",
            )
        return RecoveryDecision(
            action="revise",
            quality_score=score,
            reason=f"Score {score:.2f} is between revise threshold {revise_threshold:.2f} and accept threshold {accept_threshold:.2f}",
        )

    if tier == "tier2":
        return RecoveryDecision(
            action="accept",
            quality_score=score,
            reason=f"Score {score:.2f} < revise threshold {revise_threshold:.2f} but already on tier2 (best available)",
        )

    return RecoveryDecision(
        action="escalate",
        quality_score=score,
        reason=f"Score {score:.2f} < revise threshold {revise_threshold:.2f}",
    )


def build_revision_prompt(prompt: str, current_answer: str, metrics: Dict[str, Any]) -> str:
    """Build revision prompt including quality metrics."""
    metric_lines = []
    for key in ("relevance", "accuracy", "faithfulness"):
        if key in metrics:
            metric_lines.append(f"- {key.capitalize()}: {metrics[key]:.2f}/1.0")

    if "format_validity" in metrics:
        metric_lines.append(f"- Format validity: {metrics['format_validity']:.2f}/1.0")
    if "token_overlap" in metrics:
        metric_lines.append(f"- Content coverage: {metrics['token_overlap']:.2f}/1.0")

    metrics_str = "\n".join(metric_lines) if metric_lines else "- Overall quality score applied"

    return (
        f"The following response was evaluated on quality dimensions:\n"
        f"{metrics_str}\n\n"
        f"Please revise the response to improve the weakest dimensions while "
        f"preserving any correct information.\n\n"
        f"Original question: {prompt}\n\n"
        f"Current response: {current_answer}\n\n"
        f"Provide an improved response:"
    )


async def attempt_revision(
    prompt: str,
    current_answer: str,
    metrics: Dict[str, Any],
    provider: str,
    tier: str,
) -> Tuple[str, TokenMetrics, float, Optional[str]]:
    """Re-run same model with revision prompt.

    Returns (answer, tokens, latency_ms, model_id).
    """
    from app.router.provider_client import LLMProviderClient

    revision_prompt = build_revision_prompt(prompt, current_answer, metrics)
    start = time.time()

    if tier == "tier2":
        answer, tokens, latency = await LLMProviderClient.execute_tier2(
            provider=provider,
            prompt=revision_prompt,
            tier1_draft=current_answer,
            escalation_reason="quality_revision",
            uncertainty_reasons=[],
        )
    else:
        draft, _conf, _reasons, tokens, _lat = await LLMProviderClient.execute_tier1(
            provider=provider,
            prompt=revision_prompt,
        )
        answer = draft
        latency = (time.time() - start) * 1000

    return answer, tokens, latency, None


async def attempt_escalation(
    prompt: str,
    current_answer: str,
    provider: str,
) -> Tuple[str, TokenMetrics, float, str, Optional[str]]:
    """Use tier2 model (only called when current tier is tier1).

    Returns (answer, tokens, latency_ms, model_name, model_id).
    """
    from app.router.provider_client import LLMProviderClient

    model_info = await LLMProviderClient.get_model_for_provider(provider, "tier2")
    escalation_provider = model_info[3] if model_info else provider
    model_display = model_info[2] if model_info else "tier2"

    answer, tokens, latency = await LLMProviderClient.execute_tier2(
        provider=escalation_provider,
        prompt=prompt,
        tier1_draft=current_answer,
        escalation_reason="quality_low_score",
        uncertainty_reasons=["Quality score below revise threshold"],
    )

    return answer, tokens, latency, model_display, model_info[0] if model_info else None


async def apply_quality_recovery(
    prompt: str,
    current_answer: str,
    current_provider: str,
    current_model_id: Optional[str],
    current_model_name: str,
    current_tier: str,
    quality_score: float,
    quality_metrics: Dict[str, Any],
) -> RecoveryResult:
    """Main entry: decide → revise/escalate → return result."""
    decision = decide_action(quality_score, current_tier)

    if decision.action == "accept":
        return RecoveryResult(
            original_answer=current_answer,
            final_answer=current_answer,
            original_score=quality_score,
            action_taken="accept",
            recovery_model=current_model_name,
            recovery_model_id=current_model_id,
        )

    max_revisions = settings.quality_max_revisions
    last_answer = current_answer
    last_score = quality_score
    attempts = 0

    for attempt in range(max_revisions):
        attempts += 1
        try:
            revised_answer, tokens, latency, model_id = await attempt_revision(
                prompt=prompt,
                current_answer=last_answer,
                metrics=quality_metrics,
                provider=current_provider,
                tier=current_tier,
            )

            from app.evaluation.composite import evaluate_quality
            eval_result = await evaluate_quality(
                prompt=prompt,
                response=revised_answer,
                model_id=current_model_id,
            )
            revised_score = eval_result.get("quality_score", last_score)

            if revised_score >= settings.quality_accept_threshold:
                return RecoveryResult(
                    original_answer=current_answer,
                    final_answer=revised_answer,
                    original_score=quality_score,
                    final_score=revised_score,
                    action_taken="revise_success",
                    revision_attempts=attempts,
                    recovery_model=current_model_name,
                    recovery_model_id=model_id,
                    recovery_tokens=tokens,
                    recovery_latency_ms=latency,
                )

            last_answer = revised_answer
            last_score = revised_score

        except Exception as e:
            print(f"[quality_recovery] Revision attempt {attempts} failed: {e}", file=sys.stderr)
            break

    if decision.action == "revise" and current_tier == "tier1":
        try:
            esc_answer, esc_tokens, esc_latency, esc_model, esc_model_id = await attempt_escalation(
                prompt=prompt,
                current_answer=last_answer,
                provider=current_provider,
            )

            from app.evaluation.composite import evaluate_quality
            eval_result = await evaluate_quality(
                prompt=prompt,
                response=esc_answer,
                model_id=esc_model_id,
            )
            esc_score = eval_result.get("quality_score", last_score)

            return RecoveryResult(
                original_answer=current_answer,
                final_answer=esc_answer,
                original_score=quality_score,
                final_score=esc_score,
                action_taken="escalate",
                revision_attempts=attempts,
                recovery_model=esc_model,
                recovery_model_id=esc_model_id,
                recovery_tokens=esc_tokens,
                recovery_latency_ms=esc_latency,
            )
        except Exception as e:
            print(f"[quality_recovery] Escalation failed: {e}", file=sys.stderr)

    return RecoveryResult(
        original_answer=current_answer,
        final_answer=last_answer,
        original_score=quality_score,
        final_score=last_score,
        action_taken="revise_failed" if decision.action == "revise" else "escalate",
        revision_attempts=attempts,
        recovery_model=current_model_name,
        recovery_model_id=current_model_id,
    )
