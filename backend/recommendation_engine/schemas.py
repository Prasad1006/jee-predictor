"""Response shapes for prediction API."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CollegePrediction:
    college_id: int
    college_name: str
    category: str
    state: str
    program_id: int
    program_name: str
    branch: str
    year: int
    round: int
    seat_category: str
    quota: str
    gender: str
    opening_rank: int | None
    closing_rank: int
    tier: str
    margin: int
    probability_score: float
    rating: float | None = None
    recommendation_score: float | None = None
    why_recommended: list[str] | None = None
    avg_package_inr: int | None = None
    fees_inr: int | None = None
    placement_rate: float | None = None
    ug_fee: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if d.get("why_recommended") is None:
            d["why_recommended"] = []
        return d


@dataclass
class PredictionResponse:
    rank: int
    seat_category: str
    rank_type: str
    gender: str
    year: int
    home_state: str
    total_eligible: int
    all: list[CollegePrediction] = field(default_factory=list)
    dream: list[CollegePrediction] = field(default_factory=list)
    target: list[CollegePrediction] = field(default_factory=list)
    safe: list[CollegePrediction] = field(default_factory=list)
    unlikely: list[CollegePrediction] = field(default_factory=list)
    trace: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "seat_category": self.seat_category,
            "rank_type": self.rank_type,
            "gender": self.gender,
            "year": self.year,
            "home_state": self.home_state,
            "total_eligible": self.total_eligible,
            "all": [p.to_dict() for p in self.all],
            "dream": [p.to_dict() for p in self.dream],
            "target": [p.to_dict() for p in self.target],
            "safe": [p.to_dict() for p in self.safe],
            "unlikely": [p.to_dict() for p in self.unlikely],
            "trace": self.trace,
            "session_id": self.session_id,
        }
