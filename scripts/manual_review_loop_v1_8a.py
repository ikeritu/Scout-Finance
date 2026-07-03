from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "outputs" / "research" / "current_ranking"
COMPARE_JSON = ROOT / "outputs" / "research" / "current_ranking_compare" / "current_ranking_compare_v1_7b.json"
OUT_LOG = ROOT / "outputs" / "research" / "current_ranking" / "manual_review_log_v1_8a.json"

PHASE = "v1.8A"
METHOD = "manual_review_loop_v2"


VALID_RESEARCH_STATUS = {"NOT_STARTED", "IN_PROGRESS", "REVIEWED", "REJECTED"}
VALID_MANUAL_STATUS = {"PENDING", "IN_PROGRESS", "DONE", "REJECTED"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def load_review_log() -> dict:
    if OUT_LOG.exists():
        return load_json(OUT_LOG)

    return {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "financial_advice": False,
        },
        "events": [],
    }


def ensure_compare_exists() -> None:
    if not COMPARE_JSON.exists():
        raise SystemExit(f"Missing v1.7B comparison JSON: {COMPARE_JSON}")


def update_card(
    ticker: str,
    research_status: str,
    manual_review_status: str,
    thesis: str,
    positives: list[str],
    risks: list[str],
    questions: list[str],
    sources: list[str],
    notes: str,
) -> dict:
    ticker = ticker.strip().upper()
    card_path = RESEARCH_DIR / f"{ticker}_research.json"

    if not card_path.exists():
        raise SystemExit(f"Missing research card for {ticker}: {card_path}")

    card = load_json(card_path)

    if research_status not in VALID_RESEARCH_STATUS:
        raise SystemExit(f"Invalid research_status: {research_status}. Valid: {sorted(VALID_RESEARCH_STATUS)}")

    if manual_review_status not in VALID_MANUAL_STATUS:
        raise SystemExit(f"Invalid manual_review_status: {manual_review_status}. Valid: {sorted(VALID_MANUAL_STATUS)}")

    local = card.setdefault("local_research", {})
    previous = {
        "research_status": local.get("research_status"),
        "manual_review_status": local.get("manual_review_status"),
    }

    local["research_status"] = research_status
    local["manual_review_status"] = manual_review_status
    local["investment_thesis"] = thesis
    local["key_positive_points"] = positives
    local["key_risks"] = risks
    local["questions_to_review"] = questions
    local["sources_checked"] = sources
    local["notes"] = notes
    local["last_manual_review_at"] = now_iso()
    local["review_method"] = METHOD

    card["updated_at"] = now_iso()
    card.setdefault("controls", {})
    card["controls"]["openai_called"] = False
    card["controls"]["broker_called"] = False
    card["controls"]["market_data_recalculated"] = False
    card["controls"]["scoring_recalculated"] = False
    card["controls"]["financial_advice"] = False

    write_json(card_path, card)

    log = load_review_log()
    log["updated_at"] = now_iso()
    log["events"].append(
        {
            "timestamp": now_iso(),
            "ticker": ticker,
            "previous": previous,
            "new": {
                "research_status": research_status,
                "manual_review_status": manual_review_status,
                "investment_thesis": thesis,
                "key_positive_points": positives,
                "key_risks": risks,
                "questions_to_review": questions,
                "sources_checked": sources,
                "notes": notes,
            },
            "controls": {
                "openai_called": False,
                "broker_called": False,
                "market_data_recalculated": False,
                "scoring_recalculated": False,
                "financial_advice": False,
            },
        }
    )
    write_json(OUT_LOG, log)

    return card


def main() -> int:
    parser = argparse.ArgumentParser(description="Scout Finance v1.8A manual review loop v2")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--research-status", required=True, choices=sorted(VALID_RESEARCH_STATUS))
    parser.add_argument("--manual-review-status", required=True, choices=sorted(VALID_MANUAL_STATUS))
    parser.add_argument("--thesis", default="")
    parser.add_argument("--positives", default="", help="Separate items with |")
    parser.add_argument("--risks", default="", help="Separate items with |")
    parser.add_argument("--questions", default="", help="Separate items with |")
    parser.add_argument("--sources", default="", help="Separate items with |")
    parser.add_argument("--notes", default="")

    args = parser.parse_args()

    ensure_compare_exists()

    card = update_card(
        ticker=args.ticker,
        research_status=args.research_status,
        manual_review_status=args.manual_review_status,
        thesis=args.thesis,
        positives=normalize_list(args.positives),
        risks=normalize_list(args.risks),
        questions=normalize_list(args.questions),
        sources=normalize_list(args.sources),
        notes=args.notes,
    )

    print("Scout Finance ? v1.8A Manual Review Loop v2")
    print("=" * 92)
    print(f"OK   Ticker updated: {card.get('ticker')}")
    print(f"OK   Research status: {card['local_research'].get('research_status')}")
    print(f"OK   Manual review status: {card['local_research'].get('manual_review_status')}")
    print(f"OK   Card updated: {RESEARCH_DIR / (str(card.get('ticker')) + '_research.json')}")
    print(f"OK   Review log: {OUT_LOG}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
