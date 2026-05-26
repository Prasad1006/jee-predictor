"""Preference order generation (Step 9 core logic, API-ready)."""
from __future__ import annotations

from recommendation_engine.engine import PredictionEngine, PredictionRequest
from recommendation_engine.schemas import CollegePrediction, PredictionResponse


def generate_preference_order(request: PredictionRequest, max_choices: int = 50) -> dict:
    """
    Build JoSAA choice-filling order:
    1. Top safe anchors (2–3)
    2. Target colleges by closing rank
    3. Dream / borderline options
    4. Remaining safe options
    """
    engine = PredictionEngine()
    request.limit = max_choices
    result = engine.predict(request)

    ordered: list[CollegePrediction] = []
    seen: set[int] = set()

    def add(items: list[CollegePrediction], cap: int) -> None:
        for item in items:
            if item.program_id in seen:
                continue
            seen.add(item.program_id)
            ordered.append(item)
            if len(ordered) >= max_choices:
                return

    add(result.safe[:3], 3)
    add(result.target, max_choices)
    add(result.dream, max_choices)
    add(result.safe[3:], max_choices)

    return {
        "rank": result.rank,
        "seat_category": result.seat_category,
        "year": result.year,
        "total_choices": len(ordered),
        "strategy": "safe_anchors_then_target_dream_interleave",
        "choices": [
            {
                "order": idx + 1,
                "college": c.college_name,
                "program": c.program_name,
                "branch": c.branch,
                "tier": c.tier,
                "closing_rank": c.closing_rank,
                "quota": c.quota,
                "recommendation_score": c.recommendation_score,
                "why": _explain_position(idx, c),
            }
            for idx, c in enumerate(ordered)
        ],
    }


def _explain_position(index: int, choice: CollegePrediction) -> str:
    if index < 3 and choice.tier == "SAFE":
        return "Safe anchor — protects against unfavourable sliding in early rounds."
    if choice.tier == "TARGET":
        return "Balanced target — realistic upgrade with good branch/college fit."
    if choice.tier == "DREAM":
        return "Dream pick — borderline cutoff; may open in later rounds if seats remain."
    return "Backup safe option — improves admission certainty."
