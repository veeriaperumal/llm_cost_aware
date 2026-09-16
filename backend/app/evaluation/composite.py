import json
from typing import Dict, Any, Optional
from app.evaluation.task_classifier import TaskType, classify_task
from app.evaluation.deterministic import (
    evaluate_classification, evaluate_extraction, evaluate_summarization,
)
from app.evaluation.llm_judge import evaluate_qa, evaluate_tool_calling


async def evaluate_quality(
    prompt: str,
    response: str,
    model_id: Optional[str] = None,
    query_id: Optional[str] = None,
    source: Optional[str] = None,
    ground_truth: Optional[str] = None,
    expected_fields: Optional[list] = None,
    tool_used: bool = False,
    tool_succeeded: bool = False,
) -> Dict[str, Any]:
    """Run hybrid quality evaluation on a model response.

    Returns:
        {
            "task_type": str,
            "quality_score": float,
            "deterministic_score": float | None,
            "llm_judge_score": float | None,
            "metrics": dict,
        }
    """
    task_type = classify_task(prompt)

    det_result = None
    judge_result = None

    if task_type == TaskType.CLASSIFICATION:
        det_result = evaluate_classification(response, ground_truth)

    elif task_type == TaskType.EXTRACTION:
        det_result = evaluate_extraction(response, ground_truth, expected_fields)

    elif task_type == TaskType.SUMMARIZATION:
        det_result = evaluate_summarization(response, source)

    elif task_type == TaskType.QA:
        det_result = evaluate_classification(response, ground_truth)
        judge_result = await evaluate_qa(prompt, response, ground_truth)

    elif task_type == TaskType.TOOL_CALLING:
        judge_result = await evaluate_tool_calling(prompt, response, tool_used, tool_succeeded)

    det_score = det_result["score"] if det_result else None
    judge_score = judge_result["score"] if judge_result else None

    if det_score is not None and judge_score is not None:
        quality_score = 0.6 * det_score + 0.4 * judge_score
    elif det_score is not None:
        quality_score = det_score
    elif judge_score is not None:
        quality_score = judge_score
    else:
        quality_score = 0.75

    quality_score = max(0.0, min(1.0, quality_score))

    metrics = {}
    if det_result:
        metrics.update(det_result.get("metrics", {}))
    if judge_result:
        metrics.update(judge_result.get("metrics", {}))

    return {
        "task_type": task_type.value,
        "quality_score": quality_score,
        "deterministic_score": det_score,
        "llm_judge_score": judge_score,
        "metrics": metrics,
    }
