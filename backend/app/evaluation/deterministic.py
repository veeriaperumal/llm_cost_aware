import json
import re
from typing import Dict, Any, Optional, List
from app.evaluation.task_classifier import TaskType


def _extract_json(text: str) -> Optional[Dict]:
    """Try to extract JSON from text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None


def _tokenize(text: str) -> List[str]:
    """Simple whitespace tokenizer."""
    return text.lower().split()


def _token_overlap(reference: str, hypothesis: str) -> float:
    """Compute token overlap (ROUGE-1 like) between reference and hypothesis."""
    ref_tokens = set(_tokenize(reference))
    hyp_tokens = set(_tokenize(hypothesis))
    if not ref_tokens:
        return 0.0
    overlap = ref_tokens & hyp_tokens
    return len(overlap) / len(ref_tokens)


def evaluate_classification(response: str, ground_truth: Optional[str] = None) -> Dict[str, Any]:
    """Evaluate a classification response.

    If ground_truth is provided, compute accuracy against it.
    Otherwise, check format validity (single label, reasonable length).
    """
    metrics = {}

    response_clean = response.strip().lower()
    if ground_truth:
        gt_clean = ground_truth.strip().lower()
        metrics["exact_match"] = 1.0 if response_clean == gt_clean else 0.0
        metrics["accuracy"] = metrics["exact_match"]
        metrics["precision"] = metrics["exact_match"]
        metrics["recall"] = metrics["exact_match"]
        metrics["f1"] = metrics["exact_match"]
    else:
        is_single_label = len(response_clean.split()) <= 5
        is_short = len(response_clean) < 200
        format_score = (1.0 if is_single_label else 0.5) * (1.0 if is_short else 0.7)
        metrics["format_validity"] = format_score
        metrics["accuracy"] = format_score
        metrics["precision"] = format_score
        metrics["recall"] = format_score
        metrics["f1"] = format_score

    score = metrics.get("f1", metrics.get("accuracy", 0.5))
    return {"score": score, "metrics": metrics}


def evaluate_extraction(response: str, ground_truth: Optional[str] = None,
                        expected_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Evaluate an extraction response.

    Checks JSON validity, required fields, and field-level exact match if ground truth provided.
    """
    metrics = {}
    parsed = _extract_json(response)

    if parsed is None:
        return {"score": 0.2, "metrics": {"json_valid": False, "field_match": 0.0}}

    metrics["json_valid"] = True

    if expected_fields:
        present = sum(1 for f in expected_fields if f in parsed)
        metrics["field_coverage"] = present / len(expected_fields) if expected_fields else 1.0
    else:
        metrics["field_coverage"] = 1.0 if len(parsed) > 0 else 0.5

    if ground_truth:
        gt_parsed = _extract_json(ground_truth)
        if gt_parsed and isinstance(gt_parsed, dict) and isinstance(parsed, dict):
            matching = sum(1 for k, v in gt_parsed.items() if parsed.get(k) == v)
            total = len(gt_parsed) if gt_parsed else 1
            metrics["field_exact_match"] = matching / total
        else:
            metrics["field_exact_match"] = 0.5
    else:
        metrics["field_exact_match"] = metrics["field_coverage"]

    score = (
        0.3 * (1.0 if metrics["json_valid"] else 0.0)
        + 0.3 * metrics.get("field_coverage", 0.5)
        + 0.4 * metrics.get("field_exact_match", 0.5)
    )
    return {"score": score, "metrics": metrics}


def evaluate_summarization(response: str, source: Optional[str] = None) -> Dict[str, Any]:
    """Evaluate a summarization response.

    Uses token overlap with source if available, plus format checks.
    """
    metrics = {}

    response_len = len(response.split())
    metrics["length_ratio"] = min(1.0, response_len / max(1, 50))

    if source:
        metrics["token_overlap"] = _token_overlap(source, response)
        metrics["coverage"] = metrics["token_overlap"]
    else:
        has_structure = bool(re.search(r"[\n\-•*]", response))
        metrics["has_structure"] = has_structure
        metrics["coverage"] = 0.7 if has_structure else 0.5

    is_concise = response_len < 200
    metrics["conciseness"] = 1.0 if is_concise else max(0.3, 1.0 - (response_len - 200) / 500)

    score = (
        0.4 * metrics.get("coverage", 0.5)
        + 0.3 * metrics.get("conciseness", 0.5)
        + 0.3 * min(1.0, metrics.get("length_ratio", 0.5))
    )
    return {"score": score, "metrics": metrics}
