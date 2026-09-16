import os
from typing import Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv(override=True)

class ModelPricing(BaseModel):
    input_cost_per_million: float
    output_cost_per_million: float
    name: str
    tier: str  # "tier1" (fast/cheap) or "tier2" (frontier)
    description: str

class Settings(BaseModel):
    @property
    def default_provider(self) -> str:
        load_dotenv(override=True)
        explicit = os.getenv("DEFAULT_PROVIDER", "").strip().lower()
        if explicit in ["gemini", "groq", "openai", "anthropic", "mistral"]:
            return explicit
        if self.gemini_api_key:
            return "gemini"
        if self.groq_api_key:
            return "groq"
        if self.openai_api_key:
            return "openai"
        if self.anthropic_api_key:
            return "anthropic"
        if self.mistral_api_key:
            return "mistral"
        return "mock"

    @property
    def confidence_threshold(self) -> float:
        load_dotenv(override=True)
        try:
            return float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
        except Exception:
            return 0.75

    @property
    def host(self) -> str:
        return os.getenv("HOST", "127.0.0.1")

    @property
    def port(self) -> int:
        return int(os.getenv("PORT", "8000"))

    @property
    def gemini_api_key(self) -> str:
        load_dotenv(override=True)
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def groq_api_key(self) -> str:
        load_dotenv(override=True)
        return os.getenv("GROQ_API_KEY", "").strip()

    @property
    def mistral_api_key(self) -> str:
        load_dotenv(override=True)
        return os.getenv("MISTRAL_API_KEY", "").strip()

    @property
    def anthropic_api_key(self) -> str:
        load_dotenv(override=True)
        return os.getenv("ANTHROPIC_API_KEY", "").strip()

    @property
    def openai_api_key(self) -> str:
        load_dotenv(override=True)
        return os.getenv("OPENAI_API_KEY", "").strip()

    @property
    def database_url(self) -> str:
        load_dotenv(override=True)
        raw_url = (
            os.getenv("DATABASE_URL")
            or os.getenv("POSTGRES_URL")
            or os.getenv("POSTGRESQL_URL")
            or os.getenv("PG_URL")
            or ""
        ).strip()
        if not raw_url:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "cost_aware.db").replace("\\", "/")
            return f"sqlite+aiosqlite:///{db_path}"
        # Normalize postgres protocol for async SQLAlchemy
        if raw_url.startswith("postgres://"):
            raw_url = "postgresql+asyncpg://" + raw_url[len("postgres://"):]
        elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+"):
            raw_url = "postgresql+asyncpg://" + raw_url[len("postgresql://"):]
        elif raw_url.startswith("sqlite://") and not raw_url.startswith("sqlite+"):
            raw_url = "sqlite+aiosqlite://" + raw_url[len("sqlite://"):]
        return raw_url

    @property
    def pareto_quality_weight(self) -> float:
        load_dotenv(override=True)
        try:
            return float(os.getenv("PARETO_QUALITY_WEIGHT", "0.45"))
        except Exception:
            return 0.45

    @property
    def pareto_latency_weight(self) -> float:
        load_dotenv(override=True)
        try:
            return float(os.getenv("PARETO_LATENCY_WEIGHT", "0.30"))
        except Exception:
            return 0.30

    @property
    def pareto_cost_weight(self) -> float:
        load_dotenv(override=True)
        try:
            return float(os.getenv("PARETO_COST_WEIGHT", "0.25"))
        except Exception:
            return 0.25

    @property
    def judge_model_provider(self) -> str:
        load_dotenv(override=True)
        return os.getenv("JUDGE_MODEL_PROVIDER", "anthropic").strip().lower()

    @property
    def judge_model_name(self) -> str:
        load_dotenv(override=True)
        return os.getenv("JUDGE_MODEL_NAME", "claude-3-5-haiku-20241022").strip()

    @property
    def quality_evaluation_enabled(self) -> bool:
        load_dotenv(override=True)
        return os.getenv("QUALITY_EVALUATION_ENABLED", "true").strip().lower() in ("true", "1", "yes")

    # Pricing catalog in USD per 1 Million Tokens (fallback if DB unavailable)
    pricing_catalog: Dict[str, Dict[str, ModelPricing]] = {
        "anthropic": {
            "tier1": ModelPricing(
                name="Claude 3.5 Haiku",
                tier="tier1",
                input_cost_per_million=0.80,
                output_cost_per_million=4.00,
                description="Fast, cost-efficient model for standard tasks & preliminary evaluation"
            ),
            "tier2": ModelPricing(
                name="Claude 3.5 Sonnet",
                tier="tier2",
                input_cost_per_million=3.00,
                output_cost_per_million=15.00,
                description="Frontier intelligence model for complex reasoning and escalation"
            )
        },
        "gemini": {
            "tier1": ModelPricing(
                name="Gemini 2.5 Flash",
                tier="tier1",
                input_cost_per_million=0.075,
                output_cost_per_million=0.30,
                description="High-frequency lightweight multimodal model (Google AI Studio Free Tier available)"
            ),
            "tier2": ModelPricing(
                name="Gemini 2.5 Flash (Deep Synthesis)",
                tier="tier2",
                input_cost_per_million=0.075,
                output_cost_per_million=0.30,
                description="Authoritative verified synthesis (Google AI Studio Free Tier available)"
            )
        },
        "groq": {
            "tier1": ModelPricing(
                name="Llama 3.1 8B Instant",
                tier="tier1",
                input_cost_per_million=0.05,
                output_cost_per_million=0.08,
                description="Ultra-fast LPU inference (Groq Free Tier available)"
            ),
            "tier2": ModelPricing(
                name="Llama 3.3 70B Versatile",
                tier="tier2",
                input_cost_per_million=0.59,
                output_cost_per_million=0.79,
                description="High-capacity 70B open model for complex problem solving"
            )
        },
        "mistral": {
            "tier1": ModelPricing(
                name="Mistral Small",
                tier="tier1",
                input_cost_per_million=0.20,
                output_cost_per_million=0.60,
                description="Lightweight fast reasoning model"
            ),
            "tier2": ModelPricing(
                name="Mistral Large",
                tier="tier2",
                input_cost_per_million=2.00,
                output_cost_per_million=6.00,
                description="Top-tier flagship reasoning model"
            )
        },
        "openai": {
            "tier1": ModelPricing(
                name="GPT-4o-mini",
                tier="tier1",
                input_cost_per_million=0.15,
                output_cost_per_million=0.60,
                description="Cost-effective intelligence for fast routing"
            ),
            "tier2": ModelPricing(
                name="GPT-4o",
                tier="tier2",
                input_cost_per_million=2.50,
                output_cost_per_million=10.00,
                description="Flagship multimodal frontier model"
            )
        },
        "mock": {
            "tier1": ModelPricing(
                name="Claude 3.5 Haiku (Simulated)",
                tier="tier1",
                input_cost_per_million=0.80,
                output_cost_per_million=4.00,
                description="Simulated Haiku for zero-cost instant demonstration"
            ),
            "tier2": ModelPricing(
                name="Claude 3.5 Sonnet (Simulated)",
                tier="tier2",
                input_cost_per_million=3.00,
                output_cost_per_million=15.00,
                description="Simulated Sonnet with realistic tokens & spend tracking"
            )
        }
    }

settings = Settings()
