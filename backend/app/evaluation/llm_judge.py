import json
import re
from typing import Dict, Any, Optional


async def _call_judge_llm(prompt: str) -> Optional[Dict]:
    """Call a cheap LLM as judge. Returns parsed JSON or None."""
    try:
        from config.settings import settings
        from app.router.provider_client import LLMProviderClient

        provider = settings.judge_model_provider

        if provider == "mock":
            return _mock_judge_evaluate(prompt)

        import httpx

        if provider == "anthropic" and settings.anthropic_api_key:
            return await _call_anthropic_judge(prompt, settings)
        elif provider == "groq" and settings.groq_api_key:
            return await _call_groq_judge(prompt, settings)
        elif provider == "gemini" and settings.gemini_api_key:
            return await _call_gemini_judge(prompt, settings)
        elif provider == "openai" and settings.openai_api_key:
            return await _call_openai_judge(prompt, settings)

        return _mock_judge_evaluate(prompt)
    except Exception:
        return _mock_judge_evaluate(prompt)


async def _call_anthropic_judge(prompt: str, settings) -> Optional[Dict]:
    import httpx
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": settings.judge_model_name,
        "max_tokens": 512,
        "system": "You are a quality evaluator. Rate the answer on a 0.0-1.0 scale. Return JSON: {\"score\": float, \"reasoning\": \"string\"}",
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            text = data["content"][0]["text"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
    return None


async def _call_groq_judge(prompt: str, settings) -> Optional[Dict]:
    import httpx
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.judge_model_name,
        "messages": [
            {"role": "system", "content": "You are a quality evaluator. Rate the answer on a 0.0-1.0 scale. Return JSON: {\"score\": float, \"reasoning\": \"string\"}"},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
    return None


async def _call_gemini_judge(prompt: str, settings) -> Optional[Dict]:
    import httpx
    model_name = settings.judge_model_name
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={settings.gemini_api_key}"
    system = "You are a quality evaluator. Rate the answer on a 0.0-1.0 scale. Return JSON: {\"score\": float, \"reasoning\": \"string\"}"
    payload = {
        "contents": [{"parts": [{"text": f"{system}\n\n{prompt}"}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
    return None


async def _call_openai_judge(prompt: str, settings) -> Optional[Dict]:
    import httpx
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.judge_model_name,
        "messages": [
            {"role": "system", "content": "You are a quality evaluator. Rate the answer on a 0.0-1.0 scale. Return JSON: {\"score\": float, \"reasoning\": \"string\"}"},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
    return None


def _mock_judge_evaluate(prompt: str) -> Dict[str, Any]:
    """Rule-based mock judge for zero-cost evaluation."""
    lower = prompt.lower()
    if any(w in lower for w in ["rate", "score", "quality", "relevance", "faithfulness"]):
        return {"score": 0.80, "reasoning": "Mock judge: heuristic evaluation of quality prompt"}
    if any(w in lower for w in ["correct", "accurate", "right", "wrong"]):
        return {"score": 0.75, "reasoning": "Mock judge: accuracy-focused evaluation"}
    return {"score": 0.78, "reasoning": "Mock judge: default quality assessment"}


async def evaluate_qa(prompt: str, response: str, ground_truth: Optional[str] = None) -> Dict[str, Any]:
    """Evaluate Q&A quality using LLM judge."""
    judge_prompt = (
        f"Evaluate this Q&A pair:\n\n"
        f"Question: {prompt}\n\n"
        f"Answer: {response}\n\n"
    )
    if ground_truth:
        judge_prompt += f"Expected: {ground_truth}\n\n"

    judge_prompt += (
        "Rate the answer on: relevance (0-1), accuracy (0-1), faithfulness (0-1).\n"
        "Return JSON: {\"relevance\": float, \"accuracy\": float, \"faithfulness\": float, \"score\": float, \"reasoning\": string}\n"
        "The 'score' should be the average of relevance, accuracy, and faithfulness."
    )

    result = await _call_judge_llm(judge_prompt)
    if result:
        score = result.get("score", 0.75)
        return {
            "score": max(0.0, min(1.0, float(score))),
            "metrics": {
                "relevance": result.get("relevance", score),
                "accuracy": result.get("accuracy", score),
                "faithfulness": result.get("faithfulness", score),
                "reasoning": result.get("reasoning", ""),
            },
        }

    return {"score": 0.75, "metrics": {"reasoning": "Judge call failed, using default"}}


async def evaluate_tool_calling(prompt: str, response: str,
                                 tool_used: bool = False,
                                 tool_succeeded: bool = False) -> Dict[str, Any]:
    """Evaluate tool-calling quality."""
    metrics = {
        "tool_used_correctly": 1.0 if tool_used else 0.0,
        "tool_succeeded": 1.0 if tool_succeeded else 0.0,
    }

    if tool_used and tool_succeeded:
        judge_prompt = (
            f"Does this final answer properly incorporate the tool result?\n\n"
            f"Question: {prompt}\n"
            f"Answer: {response}\n\n"
            "Rate 0.0-1.0. Return JSON: {\"uses_tool_result\": float, \"score\": float, \"reasoning\": string}"
        )
        result = await _call_judge_llm(judge_prompt)
        if result:
            metrics["uses_tool_result"] = result.get("uses_tool_result", 0.8)
            metrics["reasoning"] = result.get("reasoning", "")
            score = result.get("score", 0.8)
        else:
            metrics["uses_tool_result"] = 0.8
            score = 0.8
    else:
        metrics["uses_tool_result"] = 0.0
        score = 0.3 if not tool_used else 0.5

    return {"score": max(0.0, min(1.0, float(score))), "metrics": metrics}
