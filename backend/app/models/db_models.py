import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class LLMModel(Base):
    __tablename__ = "models"

    id = Column(String(36), primary_key=True, default=_uuid)
    provider_name = Column(String(50), nullable=False, index=True)
    model_name = Column(String(150), nullable=False)
    display_name = Column(String(150), nullable=False)
    tier = Column(String(10), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    context_window = Column(Integer, default=0)
    supports_tools = Column(Boolean, default=False)
    supports_json = Column(Boolean, default=False)
    supports_streaming = Column(Boolean, default=True)
    supports_prompt_cache = Column(Boolean, default=False)
    base_quality_score = Column(Float, default=0.0)
    expected_latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now, nullable=False)

    pricing = relationship("ModelPricing", back_populates="model", lazy="selectin")


class ModelPricing(Base):
    __tablename__ = "model_pricing"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_id = Column(String(36), ForeignKey("models.id"), nullable=False, index=True)
    input_price_per_million = Column(Float, nullable=False)
    output_price_per_million = Column(Float, nullable=False)
    cached_input_price_per_million = Column(Float, default=0.0)
    currency = Column(String(10), default="USD", nullable=False)
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    model = relationship("LLMModel", back_populates="pricing")
