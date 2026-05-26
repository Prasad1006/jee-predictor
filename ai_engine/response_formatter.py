"""Format prediction data as scannable cards (no walls of text)."""
from __future__ import annotations

from recommendation_engine.schemas import CollegePrediction, PredictionResponse


def _short_branch(c: CollegePrediction) -> str:
    if c.branch:
        return c.branch.replace("_", " ").title()[:40]
    return (c.program_name or "")[:50]


def _tier_explanation(tier: str) -> str:
    notes = {
        "SAFE": "Strong backup — comfortably inside your range.",
        "TARGET": "Realistic target — this is a sensible upgrade to aim for.",
        "DREAM": "Stretch option — possible only if cutoffs move favorably.",
        "UNLIKELY": "Unrealistic this round — keep it as an aspirational idea, not a dependable choice.",
    }
    return notes.get(tier, "Reasonable option based on verified cutoff trends.")


def _card_block(emoji: str, title: str, college: CollegePrediction, extra: str = "") -> list[str]:
    lines = [
        f"### {emoji} {title}",
        f"**{college.college_name}** · {_short_branch(college)}",
        f"Closing cutoff: **{college.closing_rank:,}**",
        _tier_explanation(college.tier),
    ]
    if college.recommendation_score:
        lines.append(f"Match score: **{college.recommendation_score:.0f}/100**")
    if college.why_recommended:
        lines.append("")
        for w in college.why_recommended[:3]:
            lines.append(f"✔ {w}")
    if extra:
        lines.append("")
        lines.append(extra)
    lines.append("")
    return lines


def format_prediction_response(
    message: str,
    result: PredictionResponse,
    home_state: str = "",
) -> str:
    rank_label = (
        "Advanced"
        if getattr(result, "rank_type", "") == "JEE_ADVANCED"
        else "Main"
    )
    lines = [
        f"**Quick take** — JEE {rank_label} rank **{result.rank:,}** · "
        f"{result.seat_category}"
        + (f" · {home_state}" if home_state else "")
        + f" · JoSAA **{result.year}**\n",
        "This summary uses verified cutoff trends to keep recommendations realistic and easy to understand.\n",
    ]

    if result.total_eligible == 0:
        lines.append(
            "No eligible seats in our DB for this filter. Try another branch or verify category on josaa.nic.in.\n"
        )
        return "\n".join(lines)

    pool = result.all if result.all else result.target + result.safe + result.dream
    by_score = sorted(pool, key=lambda p: -(p.recommendation_score or 0))

    targets = [p for p in by_score if p.tier == "TARGET"][:2]
    dreams = [p for p in by_score if p.tier == "DREAM"][:1]
    safes = [p for p in by_score if p.tier == "SAFE"][:1]

    lines.append("## Recommended strategy\n")

    if targets:
        lines.extend(_card_block("🎯", "Best match", targets[0]))
    if dreams:
        lines.extend(
            _card_block("🔥", "Dream stretch", dreams[0], "Chance: *moderate — later rounds*")
        )
    if safes:
        lines.extend(_card_block("✅", "Safe backup", safes[0]))

    lines.append("---\n")
    lines.append(
        f"*{result.total_eligible} options in your list — click any college on the left for deep-dive. "
        "Ask **「Generate my preference list」** for a full JoSAA order.*\n"
    )
    lines.append("*Verify cutoffs on [josaa.nic.in](https://josaa.nic.in).*")
    return "\n".join(lines)


def format_preference_list(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return "Could not build a preference list — run **Predict** first with your rank & branch."

    lines = [
        "## 📋 Your JoSAA preference order\n",
        f"Strategy: **{payload.get('strategy', 'balanced').replace('_', ' ')}** · "
        f"**{payload.get('total_choices', len(choices))}** choices\n",
    ]
    for item in choices[:20]:
        tier = item.get("tier", "")
        emoji = {"SAFE": "✅", "TARGET": "🎯", "DREAM": "🔥"}.get(tier, "•")
        lines.append(
            f"{item.get('order')}. {emoji} **{item.get('college')}** — "
            f"{(item.get('program') or '')[:45]} "
            f"(close ~{item.get('closing_rank', 0):,})"
        )
        why = item.get("why")
        if why:
            lines.append(f"   *{why}*")
    if len(choices) > 20:
        lines.append(f"\n*…and {len(choices) - 20} more in the full list below.*")
    lines.append("\n*Drag/reorder in the panel on the right before locking on JoSAA portal.*")
    return "\n".join(lines)
