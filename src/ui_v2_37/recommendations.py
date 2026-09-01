"""Deterministic research-candidate selection for the local product."""
from __future__ import annotations

MIN_INTEREST_SCORE = 60.0
MAX_REASONS = 3


def select_interesting_companies(assets: tuple[dict, ...] | list[dict]) -> list[dict]:
    """Return every asset that passes the predeclared research-interest gate."""
    selected = [
        asset for asset in assets
        if asset.get("eligibility_status") == "ELIGIBLE_PARTIAL"
        and asset.get("confidence") == "HIGH"
        and asset.get("total_score") is not None
        and float(asset["total_score"]) >= MIN_INTEREST_SCORE
    ]
    return sorted(selected, key=lambda asset: (-float(asset["total_score"]), asset["asset_id"]))


def candidate_explanation(asset: dict) -> dict[str, list[str] | str]:
    """Build traceable reasons from the existing phase-6 explanation only."""
    pillars = asset.get("pillar_scores") or {}
    strongest = sorted(pillars.items(), key=lambda item: (-float(item[1]), item[0]))[:2]
    weakest = sorted(pillars.items(), key=lambda item: (float(item[1]), item[0]))[:1]
    strengths = list(asset.get("strength_factors") or [])
    weak_factors = list(asset.get("weakness_factors") or [])
    reasons = [f"pillar:{name}:{float(value):.2f}" for name, value in strongest]
    reasons.extend(f"factor:{name}" for name in strengths[: max(0, MAX_REASONS - len(reasons))])
    if not reasons:
        reasons = ["criterion:high_confidence", f"criterion:score_above:{MIN_INTEREST_SCORE:.0f}"]
    cautions = [f"pillar:{name}:{float(value):.2f}" for name, value in weakest]
    cautions.extend(f"factor:{name}" for name in weak_factors[:1])
    if not cautions:
        cautions = ["limitation:aggregate_detail_unavailable"]
    return {
        "summary": f'Score experimental {float(asset["total_score"]):.2f}/100 con confianza alta.',
        "reasons": reasons[:MAX_REASONS],
        "cautions": cautions,
    }
