from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from config.settings import settings
from app.models.schemas import ChatRequest, ChatResponse, QueryHistoryItem, AnalyticsSummary
from app.graph.cascading_router import CascadingRouter
from app.persistence.history_store import history_store

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, summary="Execute Cost-Aware Cascading LLM Pipeline")
async def chat_endpoint(request: ChatRequest):
    """
    Submits a prompt to the Cascading Router.
    Flow: User Prompt -> Tier 1 (Haiku) -> Confidence Evaluation -> If < threshold, ESCALATE to Tier 2 (Sonnet).
    Records why extra money was spent in the Cost Audit breakdown.
    """
    try:
        response = await CascadingRouter.process_query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing cascading router: {str(e)}")

@router.get("/history", response_model=List[QueryHistoryItem], summary="Get Query & Escalation Audit History")
async def get_history():
    """Returns the historical queries, escalation reasons, and financial savings logs."""
    return history_store.get_all()

@router.delete("/history", summary="Clear Query & Escalation Audit History")
async def clear_history():
    """Clears all historical queries and reset analytics."""
    history_store.clear()
    return {"message": "Audit history successfully cleared"}

@router.get("/analytics", response_model=AnalyticsSummary, summary="Get Aggregate Cost & Escalation Analytics")
async def get_analytics():
    """Returns aggregated ROI metrics, total savings, escalation rates, and reason breakdowns."""
    return history_store.get_analytics()

@router.get("/providers", summary="Get Available Providers and Pricing Catalog")
async def get_providers():
    """Returns list of supported providers and whether their API keys are configured."""
    providers_status = {
        "gemini": {
            "name": "Google Gemini (Free Tier Available)",
            "tier1_model": "Gemini 1.5 Flash",
            "tier2_model": "Gemini 1.5 Pro",
            "is_configured": bool(settings.gemini_api_key),
            "free_tier": True,
            "key_url": "https://aistudio.google.com/app/apikey"
        },
        "groq": {
            "name": "Groq LPU (Free Tier Available)",
            "tier1_model": "Llama 3.1 8B Instant",
            "tier2_model": "Llama 3.3 70B Versatile",
            "is_configured": bool(settings.groq_api_key),
            "free_tier": True,
            "key_url": "https://console.groq.com/keys"
        },
        "mistral": {
            "name": "Mistral AI (Free Tier Available)",
            "tier1_model": "Mistral Small",
            "tier2_model": "Mistral Large",
            "is_configured": bool(settings.mistral_api_key),
            "free_tier": True,
            "key_url": "https://console.mistral.ai/"
        },
        "anthropic": {
            "name": "Anthropic Claude (Paid Only)",
            "tier1_model": "Claude 3.5 Haiku",
            "tier2_model": "Claude 3.5 Sonnet",
            "is_configured": bool(settings.anthropic_api_key),
            "free_tier": False,
            "key_url": "https://console.anthropic.com/"
        },
        "openai": {
            "name": "OpenAI (Paid Only)",
            "tier1_model": "GPT-4o-mini",
            "tier2_model": "GPT-4o",
            "is_configured": bool(settings.openai_api_key),
            "free_tier": False,
            "key_url": "https://platform.openai.com/api-keys"
        },
        "mock": {
            "name": "Simulated Haiku & Sonnet (Zero-Cost / Offline)",
            "tier1_model": "Claude 3.5 Haiku (Simulated)",
            "tier2_model": "Claude 3.5 Sonnet (Simulated)",
            "is_configured": True,
            "free_tier": True,
            "key_url": None
        }
    }
    return {
        "default_provider": settings.default_provider,
        "default_threshold": settings.confidence_threshold,
        "pricing_catalog": settings.pricing_catalog,
        "providers": providers_status
    }
