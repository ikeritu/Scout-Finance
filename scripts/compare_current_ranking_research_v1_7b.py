from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ACTIVE = ROOT / "outputs" / "scouting" / "active_real_universe_top_candidates.csv"
RESEARCH_DIR = ROOT / "outputs" / "research" / "current_ranking"
RESEARCH_INDEX = RESEARCH_DIR / "current_ranking_research_index.json"

OUT_DIR = ROOT / "outputs" / "research" / "current_ranking_compare"
OUT_CSV = OUT_DIR / "current_ranking_compare_v1_7b.csv"
OUT_JSON = OUT_DIR / "current_ranking_compare_v1_7b.json"
OUT_REPORT = OUT_DIR / "current_ranking_compare_v1_7b.md"

PHASE = "v1.7B"
METHOD = "compare_current_ranking_local_research_v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_float(value: object, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: object, default: int | None = None) -> int | None:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def research_decision_status(research_status: str, manual_review_status: str) -> str:
    research_status = (research_status or "").upper()
    manual_review_status = (manual_review_status or "").upper()

    if research_status in {"APPROVED", "REVIEWED"} and manual_review_status in {"DONE", "REVIEWED", "APPROVED"}:
        return "REVIEWED"
    if research_status in {"IN_PROGRESS"} or manual_review_status in {"IN_PROGRESS"}:
        return "IN_PROGRESS"
    if research_status in {"REJECTED", "DISCARDED"}:
        return "REJECTED"
    return "PENDING_REVIEW"


def priority_flag(score: float | None, research_status: str) -> str:
    if score is None:
        return "UNKNOWN_SCORE"
    if score >= 85 and research_status == "PENDING_REVIEW":
        return "HIGH_SCORE_PENDING_REVIEW"
    if score >= 70 and research_status == "PENDING_REVIEW":
        return "MEDIUM_SCORE_PENDING_REVIEW"
    if research_status == "REVIEWED":
        return "REVIEWED"
    return "WATCH"


def main() -> int:
    active_rows = load_csv(ACTIVE)
    if not active_rows:
        raise SystemExit(f"No active ranking rows found: {ACTIVE}")

    if not RESEARCH_INDEX.exists():
        raise SystemExit(f"Missing research index: {RESEARCH_INDEX}")

    research_index = load_json(RESEARCH_INDEX)
    cards = research_index.get("cards", [])
    if not isinstance(cards, list):
        raise SystemExit("Invalid research index: cards is not a list")

    research_by_ticker: dict[str, dict[str, object]] = {}
    missing_cards: list[str] = []

    for card in cards:
        if not isinstance(card, dict):
            continue
        ticker = str(card.get("ticker", "")).strip().upper()
        path = str(card.get("path", "")).strip()
        if not ticker or not path:
            continue

        card_path = ROOT / path
        if not card_path.exists():
            missing_cards.append(ticker)
            continue

        research_by_ticker[ticker] = load_json(card_path)

    comparison_rows: list[dict[str, object]] = []

    for current_rank, row in enumerate(active_rows, start=1):
        ticker = str(row.get("ticker", "")).strip().upper()
        research = research_by_ticker.get(ticker, {})

        ranking_snapshot = research.get("ranking_snapshot", {}) if isinstance(research, dict) else {}
        local_research = research.get("local_research", {}) if isinstance(research, dict) else {}

        if not isinstance(ranking_snapshot, dict):
            ranking_snapshot = {}
        if not isinstance(local_research, dict):
            local_research = {}

        previous_rank = safe_int(research.get("rank")) if isinstance(research, dict) else None
        current_score = safe_float(row.get("score"))
        snapshot_score = safe_float(ranking_snapshot.get("score"))

        research_status = str(local_research.get("research_status", "MISSING_RESEARCH_CARD"))
        manual_review_status = str(local_research.get("manual_review_status", "MISSING_RESEARCH_CARD"))
        decision_status = research_decision_status(research_status, manual_review_status)

        rank_delta = None
        if previous_rank is not None:
            rank_delta = previous_rank - current_rank

        score_delta = None
        if current_score is not None and snapshot_score is not None:
            score_delta = round(current_score - snapshot_score, 4)

        comparison_rows.append(
            {
                "ticker": ticker,
                "current_rank": current_rank,
                "research_snapshot_rank": previous_rank,
                "rank_delta": rank_delta,
                "current_score": current_score,
                "research_snapshot_score": snapshot_score,
                "score_delta": score_delta,
                "combined_score_v1": safe_float(row.get("combined_score_v1")),
                "fundamentals_granular_score_v1_6e": safe_float(row.get("fundamentals_granular_score_v1_6e")),
                "tie_status": row.get("tie_status", ""),
                "calibration_warning": row.get("calibration_warning", ""),
                "research_status": research_status,
                "manual_review_status": manual_review_status,
                "decision_status": decision_status,
                "priority_flag": priority_flag(current_score, decision_status),
                "company_name": row.get("company_name") or row.get("name") or "",
                "sector": row.get("sector", ""),
                "industry": row.get("industry", ""),
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(comparison_rows[0].keys()))
        writer.writeheader()
        writer.writerows(comparison_rows)

    pending = [r for r in comparison_rows if r["decision_status"] == "PENDING_REVIEW"]
    high_pending = [r for r in comparison_rows if r["priority_flag"] == "HIGH_SCORE_PENDING_REVIEW"]

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "inputs": {
            "active_ranking": str(ACTIVE.relative_to(ROOT)).replace("\\", "/"),
            "research_index": str(RESEARCH_INDEX.relative_to(ROOT)).replace("\\", "/"),
        },
        "rows": len(comparison_rows),
        "pending_review": len(pending),
        "high_score_pending_review": len(high_pending),
        "missing_cards": missing_cards,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "financial_advice": False,
        },
        "comparison": comparison_rows,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report: list[str] = []
    report.append("# Scout Finance ? v1.7B Compare Current Ranking")
    report.append("")
    report.append(f"- Phase: {PHASE}")
    report.append(f"- Method: {METHOD}")
    report.append(f"- Created at: {payload['created_at']}")
    report.append(f"- Rows compared: {len(comparison_rows)}")
    report.append(f"- Pending review: {len(pending)}")
    report.append(f"- High score pending review: {len(high_pending)}")
    report.append("")
    report.append("## Controls")
    report.append("")
    report.append("- OpenAI called: false")
    report.append("- Broker called: false")
    report.append("- Market data recalculated: false")
    report.append("- Scoring recalculated: false")
    report.append("- Financial advice: false")
    report.append("")
    report.append("## Current comparison")
    report.append("")

    for row in comparison_rows:
        report.append(
            f"{row['current_rank']}. **{row['ticker']}** ? score {row['current_score']} ? "
            f"{row['decision_status']} ? {row['priority_flag']}"
        )
        if row.get("tie_status") == "EXACT_COMPONENT_TIE":
            report.append(f"   - Calibration: {row.get('calibration_warning', '')}")

    report.append("")
    report.append("## Next manual review queue")
    report.append("")

    for row in high_pending:
        report.append(
            f"- **{row['ticker']}** ? high score pending review ? "
            f"score {row['current_score']}"
        )

    if not high_pending:
        report.append("- No high-score pending reviews.")

    OUT_REPORT.write_text("\n".join(report), encoding="utf-8")

    print("Scout Finance ? v1.7B Compare Current Ranking")
    print("=" * 92)
    print(f"OK   Active ranking: {ACTIVE}")
    print(f"OK   Research index: {RESEARCH_INDEX}")
    print(f"OK   Rows compared: {len(comparison_rows)}")
    print(f"OK   Pending review: {len(pending)}")
    print(f"OK   High score pending review: {len(high_pending)}")
    print(f"OK   CSV written: {OUT_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_REPORT}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
