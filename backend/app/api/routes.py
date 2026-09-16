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
    """Returns all registered models with their active pricing and Pareto scores from the database."""
    try:
        from sqlalchemy import select
        from app.database import async_session
        from app.models.db_models import LLMModel, ModelPricing as DBModelPricing
        from app.graph.pareto import ModelCandidate, get_pareto_scores

        async with async_session() as session:
            stmt = select(LLMModel).where(LLMModel.active == True).order_by(LLMModel.provider_name, LLMModel.tier)
            result = await session.execute(stmt)
            models = result.scalars().all()

            # Build candidates per tier for Pareto scoring
            tier_candidates = {"tier1": [], "tier2": []}
            model_pricing_map = {}
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
                model_pricing_map[m.id] = pricing

                if pricing:
                    cost = pricing.input_price_per_million * 0.75 + pricing.output_price_per_million * 0.25
                    tier_candidates[m.tier].append(ModelCandidate(
                        model_id=m.id,
                        provider_name=m.provider_name,
                        model_name=m.model_name,
                        display_name=m.display_name,
                        quality=m.base_quality_score,
                        latency_ms=m.expected_latency_ms,
                        cost_per_million=cost,
                    ))

            # Compute Pareto scores per tier
            pareto_scores = {}
            for tier, candidates in tier_candidates.items():
                for model_id, score, rank in get_pareto_scores(candidates):
                    pareto_scores[model_id] = (score, rank)

            model_list = []
            for m in models:
                pricing = model_pricing_map.get(m.id)

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

                pareto_score, pareto_rank = pareto_scores.get(m.id, (None, None))

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
                    pareto_score=pareto_score,
                    pareto_rank=pareto_rank,
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


@router.get("/quality", summary="Get Quality Evaluation History")
async def get_quality_evaluations(
    model_id: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 50,
):
    """Returns recent quality evaluation records, optionally filtered by model_id and task_type."""
    try:
        from sqlalchemy import select
        from app.database import async_session
        from app.models.db_models import ModelQualityEvaluation, LLMModel

        async with async_session() as session:
            stmt = select(ModelQualityEvaluation).order_by(ModelQualityEvaluation.evaluated_at.desc()).limit(limit)
            if model_id:
                stmt = stmt.where(ModelQualityEvaluation.model_id == model_id)
            if task_type:
                stmt = stmt.where(ModelQualityEvaluation.task_type == task_type)
            result = await session.execute(stmt)
            evals = result.scalars().all()

            items = []
            for e in evals:
                model_stmt = select(LLMModel).where(LLMModel.id == e.model_id)
                model_result = await session.execute(model_stmt)
                model = model_result.scalars().first()
                items.append({
                    "id": e.id,
                    "model_id": e.model_id,
                    "model_name": model.display_name if model else "Unknown",
                    "provider_name": model.provider_name if model else "Unknown",
                    "query_id": e.query_id,
                    "task_type": e.task_type,
                    "quality_score": e.quality_score,
                    "deterministic_score": e.deterministic_score,
                    "llm_judge_score": e.llm_judge_score,
                    "metrics_json": e.metrics_json,
                    "evaluated_at": e.evaluated_at.isoformat() if e.evaluated_at else "",
                })

            return {"evaluations": items, "count": len(items)}
    except Exception:
        return {"evaluations": [], "count": 0}


@router.get("/quality/recovery", summary="Get Quality Recovery History")
async def get_quality_recovery(
    model_id: Optional[str] = None,
    action_taken: Optional[str] = None,
    limit: int = 50,
):
    """Returns quality recovery records from model_quality_recoveries table."""
    try:
        from sqlalchemy import select
        from app.database import async_session
        from app.models.db_models import ModelQualityRecovery, LLMModel

        async with async_session() as session:
            stmt = select(ModelQualityRecovery).order_by(ModelQualityRecovery.created_at.desc()).limit(limit)
            if model_id:
                stmt = stmt.where(ModelQualityRecovery.model_id == model_id)
            if action_taken:
                stmt = stmt.where(ModelQualityRecovery.action_taken == action_taken)
            result = await session.execute(stmt)
            recoveries = result.scalars().all()

            items = []
            for r in recoveries:
                model_stmt = select(LLMModel).where(LLMModel.id == r.model_id)
                model_result = await session.execute(model_stmt)
                model = model_result.scalars().first()
                items.append({
                    "id": r.id,
                    "model_id": r.model_id,
                    "model_name": model.display_name if model else "Unknown",
                    "provider_name": model.provider_name if model else "Unknown",
                    "query_id": r.query_id,
                    "original_quality_score": r.original_quality_score,
                    "final_quality_score": r.final_quality_score,
                    "action_taken": r.action_taken,
                    "revision_attempts": r.revision_attempts,
                    "recovery_model": r.recovery_model,
                    "recovery_model_id": r.recovery_model_id,
                    "recovery_cost_usd": r.recovery_cost_usd,
                    "recovery_latency_ms": r.recovery_latency_ms,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                })

            return {"recoveries": items, "count": len(items)}
    except Exception:
        return {"recoveries": [], "count": 0}
