from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.0"
METHOD = "local_research_mvp_v1"

ACTIVE = ROOT / "outputs" / "scouting" / "active_real_universe_top_candidates.csv"
RESEARCH_INDEX = ROOT / "outputs" / "research" / "current_ranking" / "current_ranking_research_index.json"
COMPARE_JSON = ROOT / "outputs" / "research" / "current_ranking_compare" / "current_ranking_compare_v1_7b.json"
MANUAL_LOG = ROOT / "outputs" / "research" / "current_ranking" / "manual_review_log_v1_8a.json"
SCALE_READINESS = ROOT / "outputs" / "scale_readiness" / "scale_readiness_audit_v1_9a.json"
LARGE_AUDIT = ROOT / "outputs" / "large_universe" / "controlled_large_universe_audit_v1_9b.json"

OUT_DIR = ROOT / "outputs" / "mvp"
OUT_JSON = OUT_DIR / "local_research_mvp_v2_0.json"
OUT_MD = OUT_DIR / "local_research_mvp_v2_0.md"
OUT_CSV = OUT_DIR / "local_research_mvp_queue_v2_0.csv"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def read_research_card(path_from_root: str) -> dict:
    path = ROOT / path_from_root
    if not path.exists():
        return {}
    return load_json(path)


def queue_status_from(research_status: str, manual_status: str) -> str:
    research_status = research_status.upper()
    manual_status = manual_status.upper()

    if research_status == "REVIEWED" or manual_status == "DONE":
        return "REVIEWED"
    if research_status == "IN_PROGRESS" or manual_status == "IN_PROGRESS":
        return "IN_PROGRESS"
    if research_status == "REJECTED" or manual_status == "REJECTED":
        return "REJECTED"
    return "PENDING_REVIEW"


def priority_from(score: float | None, queue_status: str) -> str:
    if score is None:
        return "UNKNOWN"
    if score >= 85 and queue_status == "PENDING_REVIEW":
        return "HIGH"
    if score >= 85 and queue_status == "IN_PROGRESS":
        return "HIGH_IN_PROGRESS"
    if score >= 70:
        return "MEDIUM"
    return "NORMAL"


def main() -> int:
    required = [
        ACTIVE,
        RESEARCH_INDEX,
        COMPARE_JSON,
        SCALE_READINESS,
        LARGE_AUDIT,
    ]

    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise SystemExit(f"Missing required MVP inputs: {missing}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    active_rows = load_csv(ACTIVE)
    research_index = load_json(RESEARCH_INDEX)
    compare = load_json(COMPARE_JSON)
    scale = load_json(SCALE_READINESS)
    large = load_json(LARGE_AUDIT)
    manual_log = load_json(MANUAL_LOG) if MANUAL_LOG.exists() else {"events": []}

    cards = research_index.get("cards", [])
    if not isinstance(cards, list):
        cards = []

    mvp_rows: list[dict[str, object]] = []

    for card_ref in cards:
        if not isinstance(card_ref, dict):
            continue

        ticker = str(card_ref.get("ticker", "")).upper()
        card_path = str(card_ref.get("path", ""))
        card = read_research_card(card_path)

        local = card.get("local_research", {}) if isinstance(card, dict) else {}
        snapshot = card.get("ranking_snapshot", {}) if isinstance(card, dict) else {}

        if not isinstance(local, dict):
            local = {}
        if not isinstance(snapshot, dict):
            snapshot = {}

        research_status = str(local.get("research_status", "MISSING"))
        manual_status = str(local.get("manual_review_status", "MISSING"))
        queue_status = queue_status_from(research_status, manual_status)
        score = safe_float(snapshot.get("score"))
        priority = priority_from(score, queue_status)

        mvp_rows.append(
            {
                "ticker": ticker,
                "rank": card.get("rank"),
                "company_name": card.get("company_name", ""),
                "score": score,
                "combined_score_v1": safe_float(snapshot.get("combined_score_v1")),
                "fundamentals_granular_score_v1_6e": safe_float(snapshot.get("fundamentals_granular_score_v1_6e")),
                "tie_status": snapshot.get("tie_status", ""),
                "calibration_warning": snapshot.get("calibration_warning", ""),
                "research_status": research_status,
                "manual_review_status": manual_status,
                "queue_status": queue_status,
                "priority": priority,
                "investment_thesis": local.get("investment_thesis", ""),
                "key_positive_points": " | ".join(local.get("key_positive_points", [])) if isinstance(local.get("key_positive_points", []), list) else "",
                "key_risks": " | ".join(local.get("key_risks", [])) if isinstance(local.get("key_risks", []), list) else "",
                "questions_to_review": " | ".join(local.get("questions_to_review", [])) if isinstance(local.get("questions_to_review", []), list) else "",
                "sources_checked": " | ".join(local.get("sources_checked", [])) if isinstance(local.get("sources_checked", []), list) else "",
                "notes": local.get("notes", ""),
            }
        )

    pending = [r for r in mvp_rows if r["queue_status"] == "PENDING_REVIEW"]
    in_progress = [r for r in mvp_rows if r["queue_status"] == "IN_PROGRESS"]
    reviewed = [r for r in mvp_rows if r["queue_status"] == "REVIEWED"]
    high_priority = [r for r in mvp_rows if str(r["priority"]).startswith("HIGH")]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = list(mvp_rows[0].keys()) if mvp_rows else [
            "ticker",
            "rank",
            "score",
            "queue_status",
            "priority",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mvp_rows)

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "mvp_status": "LOCAL_RESEARCH_MVP_READY",
        "inputs": {
            "active_ranking": str(ACTIVE.relative_to(ROOT)).replace("\\", "/"),
            "research_index": str(RESEARCH_INDEX.relative_to(ROOT)).replace("\\", "/"),
            "comparison": str(COMPARE_JSON.relative_to(ROOT)).replace("\\", "/"),
            "manual_review_log": str(MANUAL_LOG.relative_to(ROOT)).replace("\\", "/") if MANUAL_LOG.exists() else None,
            "scale_readiness": str(SCALE_READINESS.relative_to(ROOT)).replace("\\", "/"),
            "large_universe_audit": str(LARGE_AUDIT.relative_to(ROOT)).replace("\\", "/"),
        },
        "summary": {
            "active_rows": len(active_rows),
            "research_cards": len(cards),
            "mvp_rows": len(mvp_rows),
            "pending_review": len(pending),
            "in_progress": len(in_progress),
            "reviewed": len(reviewed),
            "high_priority": len(high_priority),
            "manual_review_events": len(manual_log.get("events", [])) if isinstance(manual_log, dict) else 0,
            "comparison_rows": compare.get("rows"),
            "scale_readiness_status": scale.get("readiness_status"),
            "scale_readiness_score": scale.get("readiness_score"),
            "large_universe_audit_status": large.get("audit_status"),
            "large_universe_readiness_score": large.get("readiness_score"),
        },
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
        },
        "queue": mvp_rows,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.0 Local Research MVP")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- MVP status: **{payload['mvp_status']}**")
    md.append("")
    md.append("## Summary")
    md.append("")
    for key, value in payload["summary"].items():
        md.append(f"- {key}: {value}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("")
    md.append("## Review queue")
    md.append("")

    for row in mvp_rows:
        md.append(
            f"{row['rank']}. **{row['ticker']}** ? score {row['score']} ? "
            f"{row['queue_status']} ? {row['priority']}"
        )
        if row.get("investment_thesis"):
            md.append(f"   - Thesis: {row['investment_thesis']}")
        if row.get("tie_status") == "EXACT_COMPONENT_TIE":
            md.append(f"   - Calibration: {row.get('calibration_warning', '')}")

    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append("Use this MVP as the local operational research layer before enabling larger scale or AI-assisted research.")
    md.append("Do not launch the full 59k universe until a larger controlled scale test has been completed.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.0 Local Research MVP")
    print("=" * 92)
    print("OK   MVP status: LOCAL_RESEARCH_MVP_READY")
    print(f"OK   Active rows: {len(active_rows)}")
    print(f"OK   Research cards: {len(cards)}")
    print(f"OK   MVP rows: {len(mvp_rows)}")
    print(f"OK   Pending review: {len(pending)}")
    print(f"OK   In progress: {len(in_progress)}")
    print(f"OK   High priority: {len(high_priority)}")
    print(f"OK   CSV written: {OUT_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
