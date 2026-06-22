from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.red_flags import detect_red_flags, flags_to_dicts, summarize_flags


PHASE = "9D"
TITLE = "Deterministic Red Flags Detector"
DEFAULT_TOP_N = 3
MAX_TOP_N = 3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_SCOUTING_DIR = PROJECT_ROOT / "outputs" / "scouting"
RED_FLAGS_DIR = OUTPUTS_SCOUTING_DIR / "red_flags"

CONTROL_FLAGS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "app_modified": False,
    "filters_modified": False,
    "release_modified": False,
}

SOURCE_CANDIDATES = [
    OUTPUTS_SCOUTING_DIR / "phase9c_research_memo_v2_contract_export.json",
    OUTPUTS_SCOUTING_DIR / "phase8f_research_memo_export_report_layer_export.json",
    OUTPUTS_SCOUTING_DIR / "phase8d_candidate_source_bound_memos.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def find_source_file() -> Path | None:
    for path in SOURCE_CANDIDATES:
        if path.exists():
            return path
    return None


def extract_records(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ["memos", "records", "items", "data", "research_memos", "export"]:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    values = [value for value in payload.values() if isinstance(value, dict)]
    if values and all(("ticker" in value or "symbol" in value) for value in values):
        return values

    return []


def flatten_for_detection(record: Dict[str, Any]) -> Dict[str, Any]:
    flat: Dict[str, Any] = {}

    def visit(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, sub in value.items():
                visit(f"{prefix}_{key}" if prefix else str(key), sub)
        elif isinstance(value, list):
            flat[prefix] = json.dumps(value, ensure_ascii=False)
        else:
            flat[prefix] = value

    visit("", record)

    # Friendly aliases used by red_flags.py.
    for key in list(flat.keys()):
        low = key.lower()
        if low.endswith("risk_score") and "risk_score" not in flat:
            flat["risk_score"] = flat[key]
        if low.endswith("valuation_score") and "valuation_score" not in flat:
            flat["valuation_score"] = flat[key]
        if low.endswith("growth_score") and "growth_score" not in flat:
            flat["growth_score"] = flat[key]
        if low.endswith("data_quality_score") and "data_quality_score" not in flat:
            flat["data_quality_score"] = flat[key]
        if low.endswith("data_completeness_score") and "data_completeness_score" not in flat:
            flat["data_completeness_score"] = flat[key]
        if low.endswith("net_debt_to_ebitda") and "net_debt_to_ebitda" not in flat:
            flat["net_debt_to_ebitda"] = flat[key]
        if low.endswith("operating_margin") and "operating_margin" not in flat:
            flat["operating_margin"] = flat[key]
        if low.endswith("fcf_margin") and "fcf_margin" not in flat:
            flat["fcf_margin"] = flat[key]
        if low.endswith("shares_dilution_3y") and "shares_dilution_3y" not in flat:
            flat["shares_dilution_3y"] = flat[key]

    return flat


def get_ticker(record: Dict[str, Any], index: int) -> str:
    ticker = record.get("ticker") or record.get("symbol") or f"UNKNOWN_{index}"
    return str(ticker).upper()


def get_company_name(record: Dict[str, Any], ticker: str) -> str:
    return str(record.get("company_name") or record.get("name") or record.get("company") or ticker)


def write_flag_markdown(path: Path, item: Dict[str, Any]) -> None:
    lines = [
        f"# Red Flags — {item['ticker']}",
        "",
        f"- Company: **{item['company_name']}**",
        f"- Red flag count: `{item['summary']['red_flag_count']}`",
        f"- Max severity: **{item['summary']['max_severity']}**",
        f"- Has high or critical: `{item['summary']['has_high_or_critical']}`",
        "- OpenAI called: `False`",
        "- API called: `False`",
        "- yfinance called: `False`",
        "- Pipeline recalculated: `False`",
        "",
        "## Flags",
        "",
    ]
    if item["red_flags"]:
        for flag in item["red_flags"]:
            lines.extend([
                f"### {flag['severity']} — {flag['title']}",
                "",
                f"- Category: `{flag['category']}`",
                f"- Code: `{flag['code']}`",
                f"- Detail: {flag['detail']}",
                f"- Source: `{flag['source']}`",
                "",
                "```json",
                json.dumps(flag["evidence"], indent=2, ensure_ascii=False),
                "```",
                "",
            ])
    else:
        lines.append("No deterministic red flags detected from available local data.")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_index_csv(path: Path, items: List[Dict[str, Any]]) -> None:
    fields = [
        "ticker",
        "company_name",
        "red_flag_count",
        "max_severity",
        "has_high_or_critical",
        "critical_count",
        "high_count",
        "medium_count",
        "low_count",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for item in items:
            sev = item["summary"]["by_severity"]
            writer.writerow({
                "ticker": item["ticker"],
                "company_name": item["company_name"],
                "red_flag_count": item["summary"]["red_flag_count"],
                "max_severity": item["summary"]["max_severity"],
                "has_high_or_critical": item["summary"]["has_high_or_critical"],
                "critical_count": sev.get("CRITICAL", 0),
                "high_count": sev.get("HIGH", 0),
                "medium_count": sev.get("MEDIUM", 0),
                "low_count": sev.get("LOW", 0),
            })


def write_report(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# Phase 9D — Deterministic Red Flags Detector",
        "",
        "Status: **OK**",
        "",
        "## Summary",
        "",
        f"- Source file: `{summary['source_file']}`",
        f"- Records loaded: {summary['records_loaded']}",
        f"- Records analyzed: {summary['records_analyzed']}",
        f"- Total red flags: {summary['total_red_flags']}",
        f"- High/Critical records: {summary['records_with_high_or_critical']}",
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
        "## Notes",
        "",
        "- This detector is deterministic.",
        "- It reuses available local phase outputs.",
        "- It does not replace the Research Memo v2 contract.",
        "- It should be integrated into Memo v2 in a later phase.",
        "",
        "## Next",
        "",
        "Proceed to Phase 9E — Integrate Red Flags into Research Memo v2.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUTS_SCOUTING_DIR.mkdir(parents=True, exist_ok=True)
    RED_FLAGS_DIR.mkdir(parents=True, exist_ok=True)

    source_file = find_source_file()
    payload = read_json(source_file, []) if source_file else []
    records = extract_records(payload)[:MAX_TOP_N]

    analyzed: List[Dict[str, Any]] = []
    for idx, record in enumerate(records, start=1):
        ticker = get_ticker(record, idx)
        company_name = get_company_name(record, ticker)
        flat = flatten_for_detection(record)
        flags = detect_red_flags(flat)
        summary = summarize_flags(flags)
        item = {
            "ticker": ticker,
            "company_name": company_name,
            "source_file": str(source_file.relative_to(PROJECT_ROOT)) if source_file else None,
            "summary": summary,
            "red_flags": flags_to_dicts(flags),
            "safety": {
                "openai_called": False,
                "api_called": False,
                "yfinance_called": False,
                "pipeline_recalculated": False,
            },
        }
        analyzed.append(item)
        write_json(RED_FLAGS_DIR / f"red_flags_{idx:02d}_{ticker}.json", item)
        write_flag_markdown(RED_FLAGS_DIR / f"red_flags_{idx:02d}_{ticker}.md", item)

    total_flags = sum(item["summary"]["red_flag_count"] for item in analyzed)
    high_critical = sum(1 for item in analyzed if item["summary"]["has_high_or_critical"])

    export_json = OUTPUTS_SCOUTING_DIR / "phase9d_red_flags_detector_export.json"
    index_csv = OUTPUTS_SCOUTING_DIR / "phase9d_red_flags_detector_index.csv"
    summary_json = OUTPUTS_SCOUTING_DIR / "phase9d_red_flags_detector_summary.json"
    audit_json = OUTPUTS_SCOUTING_DIR / "phase9d_red_flags_detector_audit.json"
    report_md = OUTPUTS_SCOUTING_DIR / "phase9d_red_flags_detector_report.md"

    write_json(export_json, analyzed)
    write_index_csv(index_csv, analyzed)

    summary = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": utc_now(),
        "default_top_n": DEFAULT_TOP_N,
        "max_top_n": MAX_TOP_N,
        "source_file": str(source_file.relative_to(PROJECT_ROOT)) if source_file else None,
        "records_loaded": len(records),
        "records_analyzed": len(analyzed),
        "total_red_flags": total_flags,
        "records_with_high_or_critical": high_critical,
        "red_flags_dir": str(RED_FLAGS_DIR),
        "export_json": str(export_json),
        "index_csv": str(index_csv),
        **CONTROL_FLAGS,
        "next": "Phase 9E — Integrate Red Flags into Research Memo v2",
    }

    audit = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": summary["created_at"],
        "summary": summary,
        "records": analyzed,
        "detector": "src/red_flags.py",
    }

    write_json(summary_json, summary)
    write_json(audit_json, audit)
    write_report(report_md, summary)

    print("Scout Finance — Phase 9D Deterministic Red Flags Detector")
    print("=" * 92)
    print()
    print("Red Flags")
    print("-" * 92)
    print("Status: OK")
    print(f"Source file: {summary['source_file']}")
    print(f"Records loaded: {summary['records_loaded']}")
    print(f"Records analyzed: {summary['records_analyzed']}")
    print(f"Total red flags: {summary['total_red_flags']}")
    print(f"Records with high/critical: {summary['records_with_high_or_critical']}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 9D Deterministic Red Flags Detector is complete.")


if __name__ == "__main__":
    main()
