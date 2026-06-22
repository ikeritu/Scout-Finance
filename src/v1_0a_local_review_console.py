from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


PHASE = "v1.0A"
TITLE = "Local Review Console"
VERSION = "v1.0.0-candidate-review-console-a"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_SCOUTING_DIR = PROJECT_ROOT / "outputs" / "scouting"
REVIEW_DIR = OUTPUTS_SCOUTING_DIR / "manual_review"
MEMO_SOURCE = OUTPUTS_SCOUTING_DIR / "phase9e_memo_v2_red_flags_export.json"

CONTROL_FLAGS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "app_modified": False,
    "filters_modified": False,
    "release_modified": False,
}

MANUAL_STATUSES = {
    "pending_review",
    "reviewed_watchlist",
    "reviewed_reject",
    "needs_more_data",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = []
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_memos() -> List[Dict[str, Any]]:
    payload = read_json(MEMO_SOURCE, [])
    return [memo for memo in payload if isinstance(memo, dict)]


def build_rows(memos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for memo in memos:
        red = memo.get("red_flags", {}).get("summary", {})
        rows.append({
            "ticker": memo.get("ticker"),
            "company_name": memo.get("company_name"),
            "ranking_position": memo.get("ranking_position"),
            "quant_score": memo.get("quant_score"),
            "auto_verdict": memo.get("normalized_verdict"),
            "manual_review_required": memo.get("manual_review_required"),
            "not_financial_advice": memo.get("not_financial_advice"),
            "red_flag_count": red.get("red_flag_count", 0),
            "max_severity": red.get("max_severity"),
            "has_high_or_critical": red.get("has_high_or_critical"),
            "data_gap_count": len(memo.get("data_gaps", [])),
            "source_count": len(memo.get("sources", [])),
        })
    return rows


def existing_manual_reviews() -> Dict[str, Dict[str, Any]]:
    path = REVIEW_DIR / "manual_review_state.json"
    payload = read_json(path, {})
    if not isinstance(payload, dict):
        return {}
    records = payload.get("records", {})
    return records if isinstance(records, dict) else {}


def build_review_state(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    existing = existing_manual_reviews()
    records: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        ticker = str(row.get("ticker") or "").upper()
        if not ticker:
            continue
        previous = existing.get(ticker, {})
        status = previous.get("manual_status", "pending_review")
        if status not in MANUAL_STATUSES:
            status = "pending_review"

        records[ticker] = {
            "ticker": ticker,
            "company_name": row.get("company_name"),
            "auto_verdict": row.get("auto_verdict"),
            "red_flag_count": row.get("red_flag_count"),
            "max_severity": row.get("max_severity"),
            "has_high_or_critical": row.get("has_high_or_critical"),
            "manual_status": status,
            "manual_notes": previous.get("manual_notes", ""),
            "reviewed_at": previous.get("reviewed_at"),
            "reviewer": previous.get("reviewer", "local_user"),
            "manual_review_required": True,
            "not_financial_advice": True,
        }

    return {
        "phase": PHASE,
        "title": TITLE,
        "version": VERSION,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "manual_status_allowed_values": sorted(MANUAL_STATUSES),
        "records": records,
        **CONTROL_FLAGS,
    }


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def write_console_md(path: Path, rows: List[Dict[str, Any]], review_state: Dict[str, Any]) -> None:
    records = review_state.get("records", {})
    lines = [
        "# Scout Finance — Local Review Console",
        "",
        "Status: **OK**",
        "",
        "This console is generated from v0.9 experimental outputs.",
        "",
        "## Safety",
        "",
        "- OpenAI called: `False`",
        "- API called: `False`",
        "- yfinance called: `False`",
        "- Pipeline recalculated: `False`",
        "- Not financial advice.",
        "- Manual review required.",
        "",
        "## Candidates",
        "",
        "| Ticker | Company | Auto verdict | Red flags | Max severity | Manual status |",
        "|---|---|---:|---:|---:|---|",
    ]

    for row in rows:
        ticker = str(row.get("ticker") or "").upper()
        record = records.get(ticker, {})
        lines.append(
            f"| {ticker} | {row.get('company_name')} | {row.get('auto_verdict')} | "
            f"{row.get('red_flag_count')} | {row.get('max_severity')} | {record.get('manual_status')} |"
        )

    lines.extend([
        "",
        "## How to review manually",
        "",
        "Edit `outputs/scouting/manual_review/manual_review_state.json`.",
        "",
        "Allowed manual statuses:",
        "",
        "- `pending_review`",
        "- `reviewed_watchlist`",
        "- `reviewed_reject`",
        "- `needs_more_data`",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_notes_md(path: Path, rows: List[Dict[str, Any]]) -> None:
    lines = ["# Manual Review Notes", ""]
    for row in rows:
        ticker = row.get("ticker")
        lines.extend([
            f"## {ticker} — {row.get('company_name')}",
            "",
            f"- Auto verdict: `{row.get('auto_verdict')}`",
            f"- Red flags: `{row.get('red_flag_count')}`",
            f"- Max severity: `{row.get('max_severity')}`",
            "- Manual status: `pending_review`",
            "- Notes:",
            "",
            "> ",
            "",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUTS_SCOUTING_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    memos = load_memos()
    rows = build_rows(memos)
    state = build_review_state(rows)

    write_json(REVIEW_DIR / "manual_review_state.json", state)
    write_console_md(REVIEW_DIR / "local_review_console.md", rows, state)
    write_notes_md(REVIEW_DIR / "manual_review_notes.md", rows)

    fields = [
        "ticker", "company_name", "ranking_position", "quant_score", "auto_verdict",
        "manual_review_required", "not_financial_advice", "red_flag_count", "max_severity",
        "has_high_or_critical", "data_gap_count", "source_count",
    ]
    write_csv(REVIEW_DIR / "local_review_console_index.csv", rows, fields)

    summary = {
        "phase": PHASE,
        "title": TITLE,
        "version": VERSION,
        "status": "OK",
        "created_at": utc_now(),
        "source_file": str(MEMO_SOURCE.relative_to(PROJECT_ROOT)),
        "candidates_loaded": len(rows),
        "review_records": len(state.get("records", {})),
        "manual_status_allowed_values": sorted(MANUAL_STATUSES),
        "outputs": {
            "review_state": str((REVIEW_DIR / "manual_review_state.json").relative_to(PROJECT_ROOT)),
            "console_md": str((REVIEW_DIR / "local_review_console.md").relative_to(PROJECT_ROOT)),
            "notes_md": str((REVIEW_DIR / "manual_review_notes.md").relative_to(PROJECT_ROOT)),
            "index_csv": str((REVIEW_DIR / "local_review_console_index.csv").relative_to(PROJECT_ROOT)),
        },
        **CONTROL_FLAGS,
        "next": "v1.0B — Human Review Layer actions/export",
    }
    write_json(OUTPUTS_SCOUTING_DIR / "v1_0a_local_review_console_summary.json", summary)

    report = [
        "# v1.0A — Local Review Console",
        "",
        "Status: **OK**",
        "",
        f"- Candidates loaded: {summary['candidates_loaded']}",
        f"- Review records: {summary['review_records']}",
        "",
        "## Safety",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "",
        "## Outputs",
        "",
    ]
    for value in summary["outputs"].values():
        report.append(f"- `{value}`")
    (OUTPUTS_SCOUTING_DIR / "v1_0a_local_review_console_report.md").write_text("\n".join(report), encoding="utf-8")

    print("Scout Finance — v1.0A Local Review Console")
    print("=" * 92)
    print("Status: OK")
    print(f"Candidates loaded: {summary['candidates_loaded']}")
    print(f"Review records: {summary['review_records']}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print("v1.0A Local Review Console is complete.")


if __name__ == "__main__":
    main()
