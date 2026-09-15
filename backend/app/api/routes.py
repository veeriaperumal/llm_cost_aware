from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from config.settings import settings
from app.models.schemas import ChatRequest, ChatResponse, QueryHistoryItem, AnalyticsSummary, ModelInfo, ModelPricingInfo
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


@router.get("/models", response_model=List[ModelInfo], summary="Get All Registered LLM Models")
async def get_models():
    """Returns all registered models with their active pricing from the database."""
    try:
        from sqlalchemy import select
        from app.database import async_session
        from app.models.db_models import LLMModel, ModelPricing as DBModelPricing

        async with async_session() as session:
            stmt = select(LLMModel).where(LLMModel.active == True).order_by(LLMModel.provider_name, LLMModel.tier)
            result = await session.execute(stmt)
            models = result.scalars().all()

            model_list = []
            for m in models:
                pricing_stmt = (
                    select(DBModelPricing)
                    .where(
                        DBModelPricing.model_id == m.id,
                        DBModelPricing.effective_to.is_(None),
                    )
                    .limit(1)
                )
                pricing_result = await session.execute(pricing_stmt)
                pricing = pricing_result.scalars().first()

                active_pricing = None
                if pricing:
                    active_pricing = ModelPricingInfo(
                        id=pricing.id,
                        input_price_per_million=pricing.input_price_per_million,
                        output_price_per_million=pricing.output_price_per_million,
                        cached_input_price_per_million=pricing.cached_input_price_per_million,
                        currency=pricing.currency,
                        effective_from=pricing.effective_from.isoformat(),
                        effective_to=pricing.effective_to.isoformat() if pricing.effective_to else None,
                    )

                model_list.append(ModelInfo(
                    id=m.id,
                    provider_name=m.provider_name,
                    model_name=m.model_name,
                    display_name=m.display_name,
                    tier=m.tier,
                    active=m.active,
                    context_window=m.context_window,
                    supports_tools=m.supports_tools,
                    supports_json=m.supports_json,
                    supports_streaming=m.supports_streaming,
                    supports_prompt_cache=m.supports_prompt_cache,
                    base_quality_score=m.base_quality_score,
                    expected_latency_ms=m.expected_latency_ms,
                    active_pricing=active_pricing,
                ))

            return model_list
    except Exception:
        return []


@router.get("/providers", summary="Get Available Providers and Pricing Catalog")
async def get_providers():
    """Returns list of supported providers and whether their API keys are configured."""
    providers_meta = {
        "gemini": {
            "name": "Google Gemini (Free Tier Available)",
            "is_configured": bool(settings.gemini_api_key),
            "free_tier": True,
            "key_url": "https://aistudio.google.com/app/apikey",
        },
        "groq": {
            "name": "Groq LPU (Free Tier Available)",
            "is_configured": bool(settings.groq_api_key),
            "free_tier": True,
            "key_url": "https://console.groq.com/keys",
        },
        "mistral": {
            "name": "Mistral AI (Free Tier Available)",
            "is_configured": bool(settings.mistral_api_key),
            "free_tier": True,
            "key_url": "https://console.mistral.ai/",
        },
        "anthropic": {
            "name": "Anthropic Claude (Paid Only)",
            "is_configured": bool(settings.anthropic_api_key),
            "free_tier": False,
            "key_url": "https://console.anthropic.com/",
        },
        "openai": {
            "name": "OpenAI (Paid Only)",
            "is_configured": bool(settings.openai_api_key),
            "free_tier": False,
            "key_url": "https://platform.openai.com/api-keys",
        },
        "mock": {
            "name": "Simulated Haiku & Sonnet (Zero-Cost / Offline)",
            "is_configured": True,
            "free_tier": True,
            "key_url": None,
        },
    }

    try:
        from sqlalchemy import select
        from app.database import async_session
        from app.models.db_models import LLMModel

        async with async_session() as session:
            for provider_name, meta in providers_meta.items():
                stmt = (
                    select(LLMModel)
                    .where(LLMModel.provider_name == provider_name, LLMModel.active == True)
                    .order_by(LLMModel.tier)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                for m in models:
                    if m.tier == "tier1":
                        meta["tier1_model"] = m.display_name
                    elif m.tier == "tier2":
                        meta["tier2_model"] = m.display_name
    except Exception:
        for provider_name, meta in providers_meta.items():
            fallback = settings.pricing_catalog.get(provider_name, {})
            meta["tier1_model"] = fallback.get("tier1", fallback.get("tier1", type("", (), {"name": "Unknown"})())).name if hasattr(fallback.get("tier1", ""), "name") else "Unknown"
            meta["tier2_model"] = fallback.get("tier2", fallback.get("tier2", type("", (), {"name": "Unknown"})())).name if hasattr(fallback.get("tier2", ""), "name") else "Unknown"

    return {
        "default_provider": settings.default_provider,
        "default_threshold": settings.confidence_threshold,
        "pricing_catalog": settings.pricing_catalog,
        "providers": providers_meta,
    }
