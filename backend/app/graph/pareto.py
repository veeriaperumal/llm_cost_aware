from dataclasses import dataclass
from typing import List, Optional
from config.settings import settings


@dataclass
class ModelCandidate:
    model_id: str
    provider_name: str
    model_name: str
    display_name: str
    quality: float
    latency_ms: int
    cost_per_million: float
    has_api_key: bool = True


@dataclass
class ParetoWeights:
    quality: float = 0.4
    latency: float = 0.3
    cost: float = 0.3


def _dominates(a: ModelCandidate, b: ModelCandidate) -> bool:
    """Returns True if model A dominates model B on the Pareto front."""
    better_in_any = False

    if a.quality < b.quality:
        return False
    if a.quality > b.quality:
        better_in_any = True

    if a.latency_ms > b.latency_ms:
        return False
    if a.latency_ms < b.latency_ms:
        better_in_any = True

    if a.cost_per_million > b.cost_per_million:
        return False
    if a.cost_per_million < b.cost_per_million:
        better_in_any = True

    return better_in_any


def pareto_filter(candidates: List[ModelCandidate]) -> List[ModelCandidate]:
    """Remove dominated models. Returns the non-dominated subset."""
    if len(candidates) <= 1:
        return list(candidates)

    non_dominated = []
    for i, candidate in enumerate(candidates):
        dominated = False
        for j, other in enumerate(candidates):
            if i == j:
                continue
            if _dominates(other, candidate):
                dominated = True
                break
        if not dominated:
            non_dominated.append(candidate)

    return non_dominated


def weighted_score(model: ModelCandidate, weights: ParetoWeights) -> float:
    """Compute a composite score for a non-dominated model.

    Dimensions are normalized relative to the candidate set extremes.
    Lower latency and cost are better (inverted), higher quality is better.
    """
    return model.quality * weights.quality + (1.0 / max(model.latency_ms, 1)) * weights.latency + (1.0 / max(model.cost_per_million, 0.0001)) * weights.cost


def select_best(candidates: List[ModelCandidate], weights: Optional[ParetoWeights] = None) -> Optional[ModelCandidate]:
    """Full pipeline: filter dominated models, then score and pick the best."""
    if not candidates:
        return None

    if weights is None:
        weights = ParetoWeights(
            quality=settings.pareto_quality_weight,
            latency=settings.pareto_latency_weight,
            cost=settings.pareto_cost_weight,
        )

    non_dominated = pareto_filter(candidates)

    best = None
    best_score = -1.0
    for model in non_dominated:
        score = weighted_score(model, weights)
        if score > best_score:
            best_score = score
            best = model

    return best


def get_pareto_scores(candidates: List[ModelCandidate], weights: Optional[ParetoWeights] = None) -> List[tuple]:
    """Return (model_id, score, rank) for all non-dominated models, ranked best-first."""
    if not candidates:
        return []

    if weights is None:
        weights = ParetoWeights(
            quality=settings.pareto_quality_weight,
            latency=settings.pareto_latency_weight,
            cost=settings.pareto_cost_weight,
        )

    non_dominated = pareto_filter(candidates)
    scored = [(m, weighted_score(m, weights)) for m in non_dominated]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [(m.model_id, score, rank + 1) for rank, (m, score) in enumerate(scored)]
