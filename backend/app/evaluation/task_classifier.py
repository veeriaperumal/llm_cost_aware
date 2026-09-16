import re
from enum import Enum


class TaskType(str, Enum):
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    QA = "qa"
    TOOL_CALLING = "tool_calling"


CLASSIFICATION_KEYWORDS = [
    "classify", "categorize", "category", "label", "sentiment",
    "positive", "negative", "neutral", "spam", "not spam",
    "true or false", "yes or no", "which of the following",
    "type of", "class of",
]

EXTRACTION_KEYWORDS = [
    "extract", "parse", "structured", "json", "csv", "table",
    "fields", "entities", "named entities", "key-value",
    "format as", "return as json", "return as csv",
]

SUMMARIZATION_KEYWORDS = [
    "summarize", "summary", "tldr", "tl;dr", "brief", "briefly",
    "short version", "condensed", "overview", "executive summary",
    "key points", "main ideas", "in a nutshell",
]

TOOL_CALLING_KEYWORDS = [
    "search", "lookup", "look up", "find", "query", "api",
    "calculate", "compute", "fetch", "retrieve", "call",
    "use a tool", "use an api", "web search", "database",
]


def classify_task(prompt: str) -> TaskType:
    """Classify a prompt into a task type using keyword matching."""
    lower = prompt.lower().strip()

    scores = {
        TaskType.CLASSIFICATION: 0,
        TaskType.EXTRACTION: 0,
        TaskType.SUMMARIZATION: 0,
        TaskType.TOOL_CALLING: 0,
    }

    for kw in CLASSIFICATION_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
            scores[TaskType.CLASSIFICATION] += 1

    for kw in EXTRACTION_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
            scores[TaskType.EXTRACTION] += 1

    for kw in SUMMARIZATION_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
            scores[TaskType.SUMMARIZATION] += 1

    for kw in TOOL_CALLING_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
            scores[TaskType.TOOL_CALLING] += 1

    max_score = max(scores.values())
    if max_score == 0:
        return TaskType.QA

    for task_type, score in scores.items():
        if score == max_score:
            return task_type

    return TaskType.QA
