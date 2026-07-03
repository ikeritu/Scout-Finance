from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "outputs" / "scouting" / "active_real_universe_top_candidates.csv"
OUT_DIR = ROOT / "outputs" / "research" / "current_ranking"
OUT_INDEX = OUT_DIR / "current_ranking_research_index.json"
OUT_REPORT = OUT_DIR / "current_ranking_research_report.md"


PHASE = "v1.7A"
METHOD = "current_ranking_local_research_json_v1"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def safe_float(value: object, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_research_card(row: dict[str, str], rank: int) -> dict[str, object]:
    ticker = str(row.get("ticker", "")).strip().upper()

    return {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "ticker": ticker,
        "rank": rank,
        "company_name": row.get("company_name") or row.get("name") or "",
        "exchange": row.get("exchange", ""),
        "country": row.get("country", ""),
        "sector": row.get("sector", ""),
        "industry": row.get("industry", ""),
        "ranking_snapshot": {
            "score": safe_float(row.get("score")),
            "combined_score_v1": safe_float(row.get("combined_score_v1")),
            "fundamentals_granular_score_v1_6e": safe_float(row.get("fundamentals_granular_score_v1_6e")),
            "category_final": row.get("category_final", ""),
            "stage3_status": row.get("stage3_status", ""),
            "status": row.get("status", ""),
            "tie_status": row.get("tie_status", ""),
            "calibration_warning": row.get("calibration_warning", ""),
        },
        "local_research": {
            "research_status": "NOT_STARTED",
            "manual_review_status": "PENDING",
            "investment_thesis": "",
            "key_positive_points": [],
            "key_risks": [],
            "questions_to_review": [],
            "sources_checked": [],
            "notes": "",
        },
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "financial_advice": False,
        },
        "disclaimer": "Local research scaffold only. Not financial advice.",
    }


def main() -> int:
    rows = load_csv(ACTIVE)
    if not rows:
        raise SystemExit(f"No rows found: {ACTIVE}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    index_cards = []
    report = []
    report.append("# Scout Finance ? v1.7A Current Ranking Local Research JSON")
    report.append("")
    report.append(f"- Phase: {PHASE}")
    report.append(f"- Method: {METHOD}")
    report.append(f"- Created at: {now_iso()}")
    report.append(f"- Input: `{ACTIVE.relative_to(ROOT)}`")
    report.append(f"- Rows: {len(rows)}")
    report.append("")
    report.append("## Controls")
    report.append("")
    report.append("- OpenAI called: false")
    report.append("- Broker called: false")
    report.append("- Market data recalculated: false")
    report.append("- Scoring recalculated: false")
    report.append("- Financial advice: false")
    report.append("")
    report.append("## Research cards")
    report.append("")

    for rank, row in enumerate(rows, start=1):
        card = build_research_card(row, rank)
        ticker = str(card["ticker"])
        if not ticker:
            continue

        out_path = OUT_DIR / f"{ticker}_research.json"
        out_path.write_text(
            json.dumps(card, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        index_cards.append(
            {
                "rank": rank,
                "ticker": ticker,
                "company_name": card["company_name"],
                "score": card["ranking_snapshot"]["score"],
                "combined_score_v1": card["ranking_snapshot"]["combined_score_v1"],
                "fundamentals_granular_score_v1_6e": card["ranking_snapshot"]["fundamentals_granular_score_v1_6e"],
                "research_status": card["local_research"]["research_status"],
                "path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
            }
        )

        report.append(
            f"{rank}. **{ticker}** ? score {card['ranking_snapshot']['score']} ? "
            f"research `{out_path.relative_to(ROOT)}`"
        )

    index = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "input": str(ACTIVE.relative_to(ROOT)).replace("\\", "/"),
        "rows": len(index_cards),
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "financial_advice": False,
        },
        "cards": index_cards,
    }

    OUT_INDEX.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    OUT_REPORT.write_text("\n".join(report), encoding="utf-8")

    print("Scout Finance ? v1.7A Current Ranking Local Research JSON")
    print("=" * 92)
    print(f"OK   Input ranking: {ACTIVE}")
    print(f"OK   Rows processed: {len(index_cards)}")
    print(f"OK   Output dir: {OUT_DIR}")
    print(f"OK   Index written: {OUT_INDEX}")
    print(f"OK   Report written: {OUT_REPORT}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
