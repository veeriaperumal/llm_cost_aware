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
    quality: float = 0.45
    latency: float = 0.30
    cost: float = 0.25


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


def _min_max_normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to [0, 1] using min-max scaling."""
    if max_val == min_val:
        return 1.0
    return (value - min_val) / (max_val - min_val)


def weighted_score(model: ModelCandidate, weights: ParetoWeights,
                   min_max: tuple) -> float:
    """Compute a composite score for a non-dominated model.

    All three dimensions are min-max normalized to [0, 1] before weighting.
    min_max = (min_q, max_q, min_lat, max_lat, min_cost, max_cost)
    """
    min_q, max_q, min_lat, max_lat, min_cost, max_cost = min_max

    quality_norm = _min_max_normalize(model.quality, min_q, max_q)
    latency_norm = _min_max_normalize(model.latency_ms, min_lat, max_lat)
    cost_norm = 1.0 - _min_max_normalize(model.cost_per_million, min_cost, max_cost)

    return (
        quality_norm * weights.quality
        + latency_norm * weights.latency
        + cost_norm * weights.cost
    )


def _compute_min_max(candidates: List[ModelCandidate]) -> tuple:
    """Compute min/max for each dimension across all candidates."""
    qualities = [c.quality for c in candidates]
    latencies = [c.latency_ms for c in candidates]
    costs = [c.cost_per_million for c in candidates]
    return (
        min(qualities), max(qualities),
        min(latencies), max(latencies),
        min(costs), max(costs),
    )


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
    min_max = _compute_min_max(non_dominated)

    best = None
    best_score = -1.0
    for model in non_dominated:
        score = weighted_score(model, weights, min_max)
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
    min_max = _compute_min_max(non_dominated)
    scored = [(m, weighted_score(m, weights, min_max)) for m in non_dominated]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [(m.model_id, score, rank + 1) for rank, (m, score) in enumerate(scored)]
