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
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    pricing = relationship("ModelPricing", back_populates="model", lazy="selectin")
    evaluations = relationship("ModelQualityEvaluation", back_populates="model", lazy="selectin")


class ModelPricing(Base):
    __tablename__ = "model_pricing"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_id = Column(String(36), ForeignKey("models.id"), nullable=False, index=True)
    input_price_per_million = Column(Float, nullable=False)
    output_price_per_million = Column(Float, nullable=False)
    cached_input_price_per_million = Column(Float, default=0.0)
    currency = Column(String(10), default="USD", nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    model = relationship("LLMModel", back_populates="pricing")


class ModelQualityEvaluation(Base):
    __tablename__ = "model_quality_evaluations"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_id = Column(String(36), ForeignKey("models.id"), nullable=False, index=True)
    query_id = Column(String(50), nullable=False)
    task_type = Column(String(30), nullable=False)
    quality_score = Column(Float, nullable=False)
    deterministic_score = Column(Float, nullable=True)
    llm_judge_score = Column(Float, nullable=True)
    metrics_json = Column(Text, default="{}")
    evaluated_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    model = relationship("LLMModel", back_populates="evaluations")


class ModelQualityRecovery(Base):
    __tablename__ = "model_quality_recoveries"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_id = Column(String(36), ForeignKey("models.id"), nullable=False, index=True)
    query_id = Column(String(50), nullable=False)
    original_quality_score = Column(Float, nullable=False)
    final_quality_score = Column(Float, nullable=True)
    action_taken = Column(String(20), nullable=False)
    revision_attempts = Column(Integer, default=0)
    recovery_model = Column(String(150), nullable=True)
    recovery_model_id = Column(String(36), nullable=True)
    recovery_cost_usd = Column(Float, default=0.0)
    recovery_latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
