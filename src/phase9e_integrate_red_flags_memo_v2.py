from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


PHASE = "9E"
TITLE = "Integrate Red Flags into Research Memo v2"
SCHEMA_VERSION = "equity_research_memo_schema_v0_2"
DEFAULT_TOP_N = 3
MAX_TOP_N = 3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_SCOUTING_DIR = PROJECT_ROOT / "outputs" / "scouting"
MEMO_9C_EXPORT = OUTPUTS_SCOUTING_DIR / "phase9c_research_memo_v2_contract_export.json"
RED_FLAGS_9D_EXPORT = OUTPUTS_SCOUTING_DIR / "phase9d_red_flags_detector_export.json"
MEMO_9E_DIR = OUTPUTS_SCOUTING_DIR / "research_memos_v2_red_flags"

CONTROL_FLAGS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "app_modified": False,
    "filters_modified": False,
    "release_modified": False,
}

ALLOWED_VERDICTS = {"WATCHLIST", "REJECT", "NEEDS_MORE_DATA"}


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


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def by_ticker(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for record in records:
        ticker = str(record.get("ticker") or record.get("symbol") or "").upper()
        if ticker:
            result[ticker] = record
    return result


def enforce_verdict(memo: Dict[str, Any], red_summary: Dict[str, Any]) -> Tuple[str, str]:
    previous = str(memo.get("normalized_verdict") or "NEEDS_MORE_DATA").upper()
    has_high = bool(red_summary.get("has_high_or_critical"))
    count = int(red_summary.get("red_flag_count") or 0)

    if previous not in ALLOWED_VERDICTS:
        previous = "NEEDS_MORE_DATA"

    if has_high:
        return "NEEDS_MORE_DATA", "High or critical red flags detected; keeping conservative NEEDS_MORE_DATA verdict."
    if previous == "REJECT":
        return "REJECT", "Previous memo verdict was REJECT and no safer override is allowed."
    if count > 0 and previous == "WATCHLIST":
        return "WATCHLIST", "Red flags detected but none high/critical; keep WATCHLIST with manual review."
    if previous == "WATCHLIST":
        return "WATCHLIST", "No high/critical red flags detected."
    return "NEEDS_MORE_DATA", "Previous memo required more data or verdict was unclear."


def integrate_memo(memo: Dict[str, Any], red_record: Dict[str, Any] | None) -> Dict[str, Any]:
    ticker = str(memo.get("ticker") or "").upper()
    red_record = red_record or {
        "ticker": ticker,
        "summary": {
            "red_flag_count": 0,
            "by_severity": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "by_category": {},
            "max_severity": "LOW",
            "has_high_or_critical": False,
        },
        "red_flags": [],
        "safety": {
            "openai_called": False,
            "api_called": False,
            "yfinance_called": False,
            "pipeline_recalculated": False,
        },
    }

    red_summary = red_record.get("summary", {})
    normalized_verdict, verdict_reason = enforce_verdict(memo, red_summary)

    enriched = json.loads(json.dumps(memo, ensure_ascii=False))
    enriched["schema_version"] = SCHEMA_VERSION
    enriched["normalized_verdict"] = normalized_verdict
    enriched["manual_review_required"] = True
    enriched["not_financial_advice"] = True
    enriched["red_flags"] = {
        "summary": red_summary,
        "items": red_record.get("red_flags", []),
        "source": "phase9d_red_flags_detector_export.json",
        "integrated_at": utc_now(),
    }
    enriched["verdict_policy"] = {
        "previous_normalized_verdict": memo.get("normalized_verdict"),
        "final_normalized_verdict": normalized_verdict,
        "reason": verdict_reason,
        "allowed_verdicts": sorted(ALLOWED_VERDICTS),
    }

    metadata = enriched.setdefault("metadata", {})
    metadata.update({
        "phase": PHASE,
        "schema_version": SCHEMA_VERSION,
        "red_flags_integrated": True,
        "red_flags_source_file": str(RED_FLAGS_9D_EXPORT.relative_to(PROJECT_ROOT)),
        "memo_source_file": str(MEMO_9C_EXPORT.relative_to(PROJECT_ROOT)),
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "pipeline_recalculated": False,
        "estimated_cost": 0.0,
        "model_used": None,
    })
    metadata["memo_with_red_flags_sha256"] = sha256_payload(enriched)
    return enriched


def memo_markdown(memo: Dict[str, Any]) -> str:
    red = memo.get("red_flags", {})
    summary = red.get("summary", {})
    items = red.get("items", [])

    lines = [
        f"# Equity Research Memo v2 + Red Flags — {memo['ticker']}",
        "",
        f"- Company: **{memo.get('company_name')}**",
        f"- Ranking position: `{memo.get('ranking_position')}`",
        f"- Quant score: `{memo.get('quant_score')}`",
        f"- Final verdict: **{memo.get('normalized_verdict')}**",
        f"- Manual review required: **{memo.get('manual_review_required')}**",
        f"- Not financial advice: **{memo.get('not_financial_advice')}**",
        f"- Red flag count: `{summary.get('red_flag_count', 0)}`",
        f"- Max severity: **{summary.get('max_severity', 'LOW')}**",
        f"- Has high/critical: `{summary.get('has_high_or_critical', False)}`",
        f"- OpenAI called: `{memo['metadata']['openai_called']}`",
        f"- API called: `{memo['metadata']['api_called']}`",
        f"- yfinance called: `{memo['metadata']['yfinance_called']}`",
        f"- Pipeline recalculated: `{memo['metadata']['pipeline_recalculated']}`",
        "",
        "## Safety statement",
        "",
        "This memo is a research artifact only. It is not financial advice. Manual review is required before any investment decision.",
        "",
        "## Verdict policy",
        "",
        "```json",
        json.dumps(memo.get("verdict_policy", {}), indent=2, ensure_ascii=False),
        "```",
        "",
        "## Red flags",
        "",
    ]

    if items:
        for flag in items:
            lines.extend([
                f"### {flag.get('severity')} — {flag.get('title')}",
                "",
                f"- Category: `{flag.get('category')}`",
                f"- Code: `{flag.get('code')}`",
                f"- Detail: {flag.get('detail')}",
                f"- Source: `{flag.get('source')}`",
                "",
                "```json",
                json.dumps(flag.get("evidence", {}), indent=2, ensure_ascii=False),
                "```",
                "",
            ])
    else:
        lines.extend(["No deterministic red flags detected from available local data.", ""])

    for section, key in [
        ("Objective data", "objective_data"),
        ("Deterministic analysis", "deterministic_analysis"),
        ("AI interpretation", "ai_interpretation"),
        ("Data gaps", "data_gaps"),
        ("Sources", "sources"),
        ("Metadata", "metadata"),
    ]:
        lines.extend([
            f"## {section}",
            "",
            "```json",
            json.dumps(memo.get(key, {}), indent=2, ensure_ascii=False),
            "```",
            "",
        ])

    return "\n".join(lines)


def write_index(path: Path, memos: List[Dict[str, Any]]) -> None:
    fields = [
        "ticker",
        "company_name",
        "ranking_position",
        "quant_score",
        "previous_verdict",
        "final_verdict",
        "manual_review_required",
        "not_financial_advice",
        "red_flag_count",
        "max_severity",
        "has_high_or_critical",
        "memo_with_red_flags_sha256",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for memo in memos:
            red_summary = memo.get("red_flags", {}).get("summary", {})
            writer.writerow({
                "ticker": memo.get("ticker"),
                "company_name": memo.get("company_name"),
                "ranking_position": memo.get("ranking_position"),
                "quant_score": memo.get("quant_score"),
                "previous_verdict": memo.get("verdict_policy", {}).get("previous_normalized_verdict"),
                "final_verdict": memo.get("normalized_verdict"),
                "manual_review_required": memo.get("manual_review_required"),
                "not_financial_advice": memo.get("not_financial_advice"),
                "red_flag_count": red_summary.get("red_flag_count", 0),
                "max_severity": red_summary.get("max_severity"),
                "has_high_or_critical": red_summary.get("has_high_or_critical"),
                "memo_with_red_flags_sha256": memo.get("metadata", {}).get("memo_with_red_flags_sha256"),
            })


def write_report(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# Phase 9E — Integrate Red Flags into Research Memo v2",
        "",
        "Status: **OK**",
        "",
        "## Summary",
        "",
        f"- Memos loaded: {summary['memos_loaded']}",
        f"- Red flag records loaded: {summary['red_flag_records_loaded']}",
        f"- Memos exported: {summary['memos_exported']}",
        f"- Verdicts: `{summary['verdict_counts']}`",
        f"- Total red flags: {summary['total_red_flags']}",
        f"- Records with high/critical: {summary['records_with_high_or_critical']}",
        f"- Manual review required all: `{summary['manual_review_required_all']}`",
        f"- Not financial advice all: `{summary['not_financial_advice_all']}`",
        "",
        "## Safety controls",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "- app.py modified: False",
        "- filters modified: False",
        "- release modified: False",
        "",
        "## Policy",
        "",
        "- If high/critical red flags exist, final verdict remains `NEEDS_MORE_DATA`.",
        "- This phase does not produce buy/sell advice.",
        "- Manual review remains mandatory.",
        "",
        "## Next",
        "",
        "Proceed to Phase 9F — AI profiles dry-run only if the user still wants it after reviewing red flags.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUTS_SCOUTING_DIR.mkdir(parents=True, exist_ok=True)
    MEMO_9E_DIR.mkdir(parents=True, exist_ok=True)

    memos = read_json(MEMO_9C_EXPORT, [])
    red_records = read_json(RED_FLAGS_9D_EXPORT, [])

    memo_records = [m for m in memos if isinstance(m, dict)][:MAX_TOP_N]
    red_by_ticker = by_ticker([r for r in red_records if isinstance(r, dict)])

    enriched: List[Dict[str, Any]] = []
    for idx, memo in enumerate(memo_records, start=1):
        ticker = str(memo.get("ticker") or f"UNKNOWN_{idx}").upper()
        merged = integrate_memo(memo, red_by_ticker.get(ticker))
        enriched.append(merged)
        write_json(MEMO_9E_DIR / f"equity_research_memo_v2_red_flags_{idx:02d}_{ticker}.json", merged)
        (MEMO_9E_DIR / f"equity_research_memo_v2_red_flags_{idx:02d}_{ticker}.md").write_text(
            memo_markdown(merged),
            encoding="utf-8",
        )

    verdict_counts: Dict[str, int] = {}
    total_red_flags = 0
    high_critical = 0
    for memo in enriched:
        verdict = memo.get("normalized_verdict")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        red_summary = memo.get("red_flags", {}).get("summary", {})
        total_red_flags += int(red_summary.get("red_flag_count") or 0)
        if red_summary.get("has_high_or_critical"):
            high_critical += 1

    export_json = OUTPUTS_SCOUTING_DIR / "phase9e_memo_v2_red_flags_export.json"
    index_csv = OUTPUTS_SCOUTING_DIR / "phase9e_memo_v2_red_flags_index.csv"
    summary_json = OUTPUTS_SCOUTING_DIR / "phase9e_memo_v2_red_flags_summary.json"
    audit_json = OUTPUTS_SCOUTING_DIR / "phase9e_memo_v2_red_flags_audit.json"
    report_md = OUTPUTS_SCOUTING_DIR / "phase9e_memo_v2_red_flags_report.md"

    write_json(export_json, enriched)
    write_index(index_csv, enriched)

    summary = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": utc_now(),
        "schema_version": SCHEMA_VERSION,
        "default_top_n": DEFAULT_TOP_N,
        "max_top_n": MAX_TOP_N,
        "memo_source_file": str(MEMO_9C_EXPORT.relative_to(PROJECT_ROOT)),
        "red_flags_source_file": str(RED_FLAGS_9D_EXPORT.relative_to(PROJECT_ROOT)),
        "memos_loaded": len(memo_records),
        "red_flag_records_loaded": len(red_records) if isinstance(red_records, list) else 0,
        "memos_exported": len(enriched),
        "verdict_counts": verdict_counts,
        "total_red_flags": total_red_flags,
        "records_with_high_or_critical": high_critical,
        "manual_review_required_all": all(m.get("manual_review_required") is True for m in enriched),
        "not_financial_advice_all": all(m.get("not_financial_advice") is True for m in enriched),
        "allowed_verdicts": sorted(ALLOWED_VERDICTS),
        "export_json": str(export_json),
        "index_csv": str(index_csv),
        "memo_dir": str(MEMO_9E_DIR),
        **CONTROL_FLAGS,
        "next": "Phase 9F — AI profiles dry-run, optional",
    }

    audit = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": summary["created_at"],
        "summary": summary,
        "memos": enriched,
    }

    write_json(summary_json, summary)
    write_json(audit_json, audit)
    write_report(report_md, summary)

    print("Scout Finance — Phase 9E Integrate Red Flags into Research Memo v2")
    print("=" * 92)
    print()
    print("Integration")
    print("-" * 92)
    print("Status: OK")
    print(f"Memos loaded: {summary['memos_loaded']}")
    print(f"Red flag records loaded: {summary['red_flag_records_loaded']}")
    print(f"Memos exported: {summary['memos_exported']}")
    print(f"Verdicts: {summary['verdict_counts']}")
    print(f"Total red flags: {summary['total_red_flags']}")
    print(f"Records with high/critical: {summary['records_with_high_or_critical']}")
    print(f"Manual review required all: {summary['manual_review_required_all']}")
    print(f"Not financial advice all: {summary['not_financial_advice_all']}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 9E Integrate Red Flags into Research Memo v2 is complete.")


if __name__ == "__main__":
    main()
