from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BREAKDOWN = ROOT / "outputs" / "scoring" / "combined_score_v1_breakdown.csv"
SUMMARY = ROOT / "outputs" / "scoring" / "combined_score_v1_summary.json"
OUT_DIR = ROOT / "outputs" / "scoring"
OUT_MD = OUT_DIR / "combined_score_calibration_audit_v1_6e.md"
OUT_CSV = OUT_DIR / "combined_score_weight_sensitivity_v1_6e.csv"


WEIGHT_SCENARIOS = {
    "current_20_35_45": (0.20, 0.35, 0.45),
    "balanced_25_35_40": (0.25, 0.35, 0.40),
    "market_heavier_20_45_35": (0.20, 0.45, 0.35),
    "fundamentals_heavier_15_30_55": (0.15, 0.30, 0.55),
    "metadata_lighter_10_40_50": (0.10, 0.40, 0.50),
}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def f(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0)
    except ValueError:
        return 0.0


def main() -> int:
    rows = load_csv(BREAKDOWN)
    if not rows:
        raise SystemExit(f"No rows found: {BREAKDOWN}")

    sensitivity_rows: list[dict[str, object]] = []

    for row in rows:
        ticker = row.get("ticker", "")
        metadata = f(row, "metadata_score_component")
        market = f(row, "market_data_score_component")
        fundamentals = f(row, "fundamentals_score_component")

        for scenario, weights in WEIGHT_SCENARIOS.items():
            wm, wmd, wf = weights
            score = round((metadata * wm) + (market * wmd) + (fundamentals * wf), 2)
            sensitivity_rows.append(
                {
                    "ticker": ticker,
                    "scenario": scenario,
                    "metadata_weight": wm,
                    "market_data_weight": wmd,
                    "fundamentals_weight": wf,
                    "metadata_score_component": metadata,
                    "market_data_score_component": market,
                    "fundamentals_score_component": fundamentals,
                    "scenario_score": score,
                }
            )

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(sensitivity_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sensitivity_rows)

    current_ranked = sorted(
        [
            {
                "ticker": row.get("ticker", ""),
                "score": f(row, "combined_score_v1"),
                "metadata": f(row, "metadata_score_component"),
                "market": f(row, "market_data_score_component"),
                "fundamentals": f(row, "fundamentals_score_component"),
            }
            for row in rows
        ],
        key=lambda x: x["score"],
        reverse=True,
    )

    scenario_groups: dict[str, list[dict[str, object]]] = {}
    for row in sensitivity_rows:
        scenario_groups.setdefault(str(row["scenario"]), []).append(row)

    report: list[str] = []
    report.append("# Scout Finance ? v1.6E Combined Scoring Calibration Audit")
    report.append("")
    report.append("## Scope")
    report.append("")
    report.append("- This audit does not change the production scoring formula.")
    report.append("- It compares alternative weight scenarios using the current score components.")
    report.append("- Current production weights remain 20% metadata, 35% market data, 45% fundamentals.")
    report.append("")
    report.append("## Current ranking")
    report.append("")
    for idx, item in enumerate(current_ranked, start=1):
        report.append(
            f"{idx}. **{item['ticker']}** ? {item['score']:.2f} "
            f"(metadata {item['metadata']:.2f}, market {item['market']:.2f}, fundamentals {item['fundamentals']:.2f})"
        )

    report.append("")
    report.append("## Weight sensitivity")
    report.append("")

    for scenario, scenario_rows in scenario_groups.items():
        ranked = sorted(scenario_rows, key=lambda x: float(x["scenario_score"]), reverse=True)
        report.append(f"### {scenario}")
        report.append("")
        for idx, item in enumerate(ranked, start=1):
            report.append(f"{idx}. **{item['ticker']}** ? {float(item['scenario_score']):.2f}")
        report.append("")

    if len(current_ranked) >= 2:
        top = current_ranked[0]
        second = current_ranked[1]
        gap = round(top["score"] - second["score"], 2)
        report.append("## Current top gap")
        report.append("")
        report.append(f"- Top: **{top['ticker']}** ? {top['score']:.2f}")
        report.append(f"- Second: **{second['ticker']}** ? {second['score']:.2f}")
        report.append(f"- Gap: **{gap:.2f} points**")
        report.append("")
        if abs(gap) < 0.25:
            report.append("Interpretation: the current formula produces an almost tied top ranking.")
            report.append("This suggests calibration should focus on discriminating fundamentals quality, market data, or metadata more precisely.")
        else:
            report.append("Interpretation: the current formula separates the top candidates enough for the current demo universe.")

    OUT_MD.write_text("\n".join(report), encoding="utf-8")

    print("Scout Finance ? v1.6E Combined Scoring Calibration Audit")
    print("=" * 92)
    print(f"OK   Input breakdown: {BREAKDOWN}")
    print(f"OK   Rows analyzed: {len(rows)}")
    print(f"OK   Scenarios: {len(WEIGHT_SCENARIOS)}")
    print(f"OK   CSV written: {OUT_CSV}")
    print(f"OK   Report written: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
