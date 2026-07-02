from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BREAKDOWN = ROOT / "outputs" / "scoring" / "combined_score_v1_breakdown.csv"
OUT_MD = ROOT / "outputs" / "scoring" / "combined_score_tiebreaker_audit_v1_6e2.md"
OUT_CSV = ROOT / "outputs" / "scoring" / "combined_score_tiebreaker_candidates_v1_6e2.csv"


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

    enriched = []
    for row in rows:
        ticker = row.get("ticker", "")
        combined = f(row, "combined_score_v1")
        metadata = f(row, "metadata_score_component")
        market = f(row, "market_data_score_component")
        fundamentals = f(row, "fundamentals_score_component")

        # Tie-breaker candidate only. Does NOT replace production score.
        # Priority:
        # 1. Higher fundamentals
        # 2. Higher market data
        # 3. Higher metadata
        # 4. Ticker alphabetical as final deterministic fallback
        tiebreaker_rank_key = (
            round(combined, 4),
            round(fundamentals, 4),
            round(market, 4),
            round(metadata, 4),
            ticker,
        )

        enriched.append(
            {
                "ticker": ticker,
                "combined_score_v1": combined,
                "metadata_score_component": metadata,
                "market_data_score_component": market,
                "fundamentals_score_component": fundamentals,
                "tiebreaker_rank_key": str(tiebreaker_rank_key),
            }
        )

    ranked = sorted(
        enriched,
        key=lambda x: (
            float(x["combined_score_v1"]),
            float(x["fundamentals_score_component"]),
            float(x["market_data_score_component"]),
            float(x["metadata_score_component"]),
            str(x["ticker"]),
        ),
        reverse=True,
    )

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(enriched[0].keys()))
        writer.writeheader()
        writer.writerows(ranked)

    report = []
    report.append("# Scout Finance ? v1.6E2 Tie-breaker Audit")
    report.append("")
    report.append("## Purpose")
    report.append("")
    report.append("This audit checks whether tied combined scores can be separated by existing score components.")
    report.append("It does not change the production ranking formula.")
    report.append("")
    report.append("## Candidate tie-breaker order")
    report.append("")
    report.append("1. combined_score_v1")
    report.append("2. fundamentals_score_component")
    report.append("3. market_data_score_component")
    report.append("4. metadata_score_component")
    report.append("5. ticker alphabetical fallback")
    report.append("")
    report.append("## Ranking using candidate tie-breaker")
    report.append("")

    for idx, row in enumerate(ranked, start=1):
        report.append(
            f"{idx}. **{row['ticker']}** ? combined {float(row['combined_score_v1']):.2f}, "
            f"fundamentals {float(row['fundamentals_score_component']):.2f}, "
            f"market {float(row['market_data_score_component']):.2f}, "
            f"metadata {float(row['metadata_score_component']):.2f}"
        )

    report.append("")
    report.append("## Interpretation")
    report.append("")
    report.append("If tied companies have identical fundamentals, market data and metadata components,")
    report.append("weights alone cannot solve the tie. The model needs either more granular components")
    report.append("or a deterministic tie-breaker.")

    OUT_MD.write_text("\n".join(report), encoding="utf-8")

    print("Scout Finance ? v1.6E2 Tie-breaker Audit")
    print("=" * 92)
    print(f"OK   Rows analyzed: {len(rows)}")
    print(f"OK   CSV written: {OUT_CSV}")
    print(f"OK   Report written: {OUT_MD}")
    print("")
    print("Candidate ranking:")
    for idx, row in enumerate(ranked, start=1):
        print(
            f"{idx}. {row['ticker']} ? combined {float(row['combined_score_v1']):.2f}, "
            f"fundamentals {float(row['fundamentals_score_component']):.2f}, "
            f"market {float(row['market_data_score_component']):.2f}, "
            f"metadata {float(row['metadata_score_component']):.2f}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
