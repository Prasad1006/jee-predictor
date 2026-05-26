"""Weighted recommendation scoring for college-program options."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoringContext:
    student_rank: int
    home_state: str = ""
    branch_preference: str = ""
    student_goals: str = ""


def compute_recommendation_score(
    *,
    tier: str,
    closing_rank: int,
    student_rank: int,
    quota: str,
    college_category: str,
    college_state: str,
    rating: float | None,
    avg_package_inr: int | None,
    placement_rate: float | None,
    fees_inr: int | None,
    ctx: ScoringContext,
) -> tuple[float, list[str]]:
    """Return score 0–100 and short 'why recommended' bullets."""
    score = 0.0
    why: list[str] = []

    # Placement & outcomes (30%)
    if avg_package_inr and avg_package_inr > 0:
        pkg_pts = min(avg_package_inr / 2_500_000, 1.0) * 30
        score += pkg_pts
        if avg_package_inr >= 1_800_000:
            why.append("Strong avg package trend (typically ₹18L+)")
        elif avg_package_inr >= 1_000_000:
            why.append("Solid placement outcomes for this tier")
    elif rating:
        score += (min(rating, 10) / 10) * 22
    if placement_rate and placement_rate >= 0.85:
        score += 8
        why.append(f"High placement rate (~{int(placement_rate * 100)}%)")

    # Institute quality (25%)
    if rating:
        score += (min(rating, 10) / 10) * 25
        if rating >= 8.5:
            why.append("Top-tier institute rating in our data")
        elif rating >= 7.5:
            why.append("Good academic & placement reputation")

    # Rank fit / tier (25%)
    margin = closing_rank - student_rank
    tier_bonus = {"TARGET": 22, "SAFE": 14, "DREAM": 8}.get(tier, 10)
    score += tier_bonus
    if tier == "TARGET":
        why.append("Closing rank is a realistic upgrade for your rank")
    elif tier == "SAFE":
        why.append("Comfortable buffer — strong backup choice")
    elif tier == "DREAM":
        why.append("Stretch option — may open in later rounds")

    if 0 < margin <= 2000:
        score += 5
        why.append("Cutoff is close to your rank — good round movement potential")

    # Location & quota (10%)
    hs = ctx.home_state.strip().lower()
    if hs and college_state and hs in college_state.lower():
        score += 5
    if quota == "HOME_STATE" and hs and college_state and hs in college_state.lower():
        score += 8
        why.append("Home state quota — often better cutoffs for you")

    # Coding / branch culture heuristics (10%)
    goals = (ctx.student_goals + " " + ctx.branch_preference).lower()
    coding_focus = any(w in goals for w in ("coding", "cse", "cs", "software", "tech"))
    if college_category == "IIIT" or (coding_focus and college_category in ("IIIT", "IIT")):
        score += 6
        if "coding" not in " ".join(why).lower():
            why.append("Strong coding culture fit for tech-focused goals")

    # ROI hint
    if fees_inr and avg_package_inr and fees_inr > 0:
        roi = avg_package_inr / fees_inr
        if roi >= 3:
            score += 4
            why.append("Good ROI (package vs fees)")

    return round(min(score, 100), 1), why[:4]
