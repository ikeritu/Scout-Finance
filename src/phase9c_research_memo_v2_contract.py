from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PHASE = "9C"
TITLE = "Research Memo v2 Contract Hardening"
SCHEMA_VERSION = "equity_research_memo_schema_v0_2"
DEFAULT_TOP_N = 3
MAX_TOP_N = 3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_SCOUTING_DIR = PROJECT_ROOT / "outputs" / "scouting"
MEMO_V2_DIR = OUTPUTS_SCOUTING_DIR / "research_memos_v2"

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
    OUTPUTS_SCOUTING_DIR / "phase8f_research_memo_export_report_layer_export.json",
    OUTPUTS_SCOUTING_DIR / "phase8e_persisted_equity_research_memos.json",
    OUTPUTS_SCOUTING_DIR / "phase8d_candidate_source_bound_memos.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_read_json(path: Path, default: Any = None) -> Any:
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


def find_source_file() -> Optional[Path]:
    for path in SOURCE_CANDIDATES:
        if path.exists():
            return path
    return None


def extract_memos(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ["memos", "research_memos", "export", "records", "items", "data"]:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    # Some phase outputs may be keyed by ticker.
    dict_values = [value for value in payload.values() if isinstance(value, dict)]
    if dict_values and all(("ticker" in item or "symbol" in item) for item in dict_values):
        return dict_values

    return []


def first_present(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for key in keys:
        if key in data and data.get(key) not in (None, ""):
            return data.get(key)
    return default


def normalize_verdict(raw: Any, memo_status: Any, data_gaps: List[Any]) -> str:
    value = str(raw or memo_status or "").strip().lower()

    if data_gaps:
        # If the memo already says data is insufficient, do not pretend certainty.
        if any("insufficient" in str(gap).lower() or "missing" in str(gap).lower() for gap in data_gaps):
            return "NEEDS_MORE_DATA"

    if value in {"data_insufficient", "insufficient_data", "needs_more_data", "need_more_data"}:
        return "NEEDS_MORE_DATA"
    if value in {"avoid", "reject", "rejected", "not_candidate", "weak", "red_flag"}:
        return "REJECT"
    if value in {"watchlist", "watchlist_only", "research_candidate", "strong_research_candidate", "candidate", "ok", "active"}:
        return "WATCHLIST"

    # Conservative default: if unclear, require more data.
    return "NEEDS_MORE_DATA"


def normalize_sources(raw_sources: Any, source_file: Optional[Path]) -> List[Any]:
    sources: List[Any] = []
    if isinstance(raw_sources, list):
        sources.extend(raw_sources)
    elif raw_sources:
        sources.append(raw_sources)

    if source_file is not None:
        sources.append({
            "source_type": "local_phase_output",
            "path": str(source_file.relative_to(PROJECT_ROOT)),
            "note": "Source memo package from previous validated phase.",
        })

    # Deduplicate while preserving order.
    seen = set()
    out = []
    for source in sources:
        key = json.dumps(source, sort_keys=True, ensure_ascii=False) if isinstance(source, (dict, list)) else str(source)
        if key not in seen:
            seen.add(key)
            out.append(source)
    return out


def as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def build_v2_memo(raw: Dict[str, Any], source_file: Optional[Path], position: int) -> Dict[str, Any]:
    ticker = str(first_present(raw, ["ticker", "symbol"], f"UNKNOWN_{position}")).upper()
    company_name = first_present(raw, ["company_name", "name", "company"], ticker)
    ranking_position = first_present(raw, ["ranking_position", "rank", "position"], position)
    try:
        ranking_position = int(ranking_position) if ranking_position is not None else None
    except Exception:
        ranking_position = position

    quant_score = first_present(raw, ["quant_score", "score", "final_score"], None)
    try:
        quant_score = float(quant_score) if quant_score is not None else None
    except Exception:
        quant_score = None

    memo_status = str(first_present(raw, ["memo_status", "status"], "generated"))
    legacy_verdict = first_present(raw, ["final_verdict", "verdict", "normalized_verdict"], None)

    objective_data = as_dict(first_present(raw, ["objective_data", "objective_data_json"], {}))
    ai_interpretation = as_dict(first_present(raw, ["ai_interpretation", "ai_interpretation_json"], {}))

    deterministic_analysis = {
        "financial_health": first_present(raw, ["financial_health", "financial_health_score"], None),
        "moat": first_present(raw, ["moat_analysis", "moat_score"], None),
        "valuation": first_present(raw, ["valuation_analysis", "valuation_score"], None),
        "growth": first_present(raw, ["growth_analysis", "growth_score"], None),
        "risk": first_present(raw, ["risk_analysis", "risk_score"], None),
        "institutional": first_present(raw, ["institutional_view", "institutional_score"], None),
        "bull_case": first_present(raw, ["bull_case"], None),
        "base_case": first_present(raw, ["base_case"], None),
        "bear_case": first_present(raw, ["bear_case"], None),
        "confidence": first_present(raw, ["confidence"], None),
    }
    deterministic_analysis = {k: v for k, v in deterministic_analysis.items() if v not in (None, "", [], {})}

    data_gaps = as_list(first_present(raw, ["data_gaps", "data_gaps_json"], []))
    sources = normalize_sources(first_present(raw, ["sources", "source", "source_files"], []), source_file)

    normalized_verdict = normalize_verdict(legacy_verdict, memo_status, data_gaps)

    metadata = {
        "phase": PHASE,
        "created_at": utc_now(),
        "source_file": str(source_file.relative_to(PROJECT_ROOT)) if source_file else None,
        "source_schema_version": first_present(raw, ["schema_version"], None),
        "prompt_version": first_present(raw, ["prompt_version"], None),
        "ranking_position": ranking_position,
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "pipeline_recalculated": False,
        "estimated_cost": 0.0,
        "model_used": None,
        "manual_review_required_reason": "Financial research output requires human review before any decision.",
    }

    memo = {
        "schema_version": SCHEMA_VERSION,
        "ticker": ticker,
        "company_name": company_name,
        "ranking_position": ranking_position,
        "quant_score": quant_score,
        "memo_status": memo_status,
        "legacy_verdict": legacy_verdict,
        "normalized_verdict": normalized_verdict,
        "manual_review_required": True,
        "not_financial_advice": True,
        "objective_data": objective_data,
        "deterministic_analysis": deterministic_analysis,
        "ai_interpretation": ai_interpretation,
        "data_gaps": data_gaps,
        "sources": sources,
        "metadata": metadata,
    }

    serialized = json.dumps(memo, sort_keys=True, ensure_ascii=False)
    memo["metadata"]["memo_sha256"] = sha256_text(serialized)
    return memo


def memo_markdown(memo: Dict[str, Any]) -> str:
    lines = [
        f"# Equity Research Memo v2 — {memo['ticker']}",
        "",
        f"- Company: **{memo['company_name']}**",
        f"- Ranking position: `{memo['ranking_position']}`",
        f"- Quant score: `{memo['quant_score']}`",
        f"- Verdict: **{memo['normalized_verdict']}**",
        f"- Manual review required: **{memo['manual_review_required']}**",
        f"- Not financial advice: **{memo['not_financial_advice']}**",
        f"- OpenAI called: `{memo['metadata']['openai_called']}`",
        f"- API called: `{memo['metadata']['api_called']}`",
        f"- yfinance called: `{memo['metadata']['yfinance_called']}`",
        f"- Pipeline recalculated: `{memo['metadata']['pipeline_recalculated']}`",
        "",
        "## Safety statement",
        "",
        "This memo is a research artifact only. It is not financial advice. Manual review is required before any investment decision.",
        "",
        "## Objective data",
        "",
        "```json",
        json.dumps(memo["objective_data"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Deterministic analysis",
        "",
        "```json",
        json.dumps(memo["deterministic_analysis"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## AI interpretation",
        "",
        "```json",
        json.dumps(memo["ai_interpretation"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Data gaps",
        "",
    ]
    if memo["data_gaps"]:
        for gap in memo["data_gaps"]:
            lines.append(f"- {gap}")
    else:
        lines.append("- None recorded.")

    lines.extend(["", "## Sources", ""])
    if memo["sources"]:
        for source in memo["sources"]:
            lines.append(f"- {source}")
    else:
        lines.append("- No source recorded.")

    lines.extend([
        "",
        "## Metadata",
        "",
        "```json",
        json.dumps(memo["metadata"], indent=2, ensure_ascii=False),
        "```",
        "",
    ])
    return "\n".join(lines)


def write_csv_index(path: Path, memos: List[Dict[str, Any]]) -> None:
    fields = [
        "ticker",
        "company_name",
        "ranking_position",
        "quant_score",
        "memo_status",
        "legacy_verdict",
        "normalized_verdict",
        "manual_review_required",
        "not_financial_advice",
        "data_gap_count",
        "source_count",
        "memo_sha256",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for memo in memos:
            writer.writerow({
                "ticker": memo["ticker"],
                "company_name": memo["company_name"],
                "ranking_position": memo["ranking_position"],
                "quant_score": memo["quant_score"],
                "memo_status": memo["memo_status"],
                "legacy_verdict": memo["legacy_verdict"],
                "normalized_verdict": memo["normalized_verdict"],
                "manual_review_required": memo["manual_review_required"],
                "not_financial_advice": memo["not_financial_advice"],
                "data_gap_count": len(memo["data_gaps"]),
                "source_count": len(memo["sources"]),
                "memo_sha256": memo["metadata"].get("memo_sha256"),
            })


def write_report(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# Phase 9C — Research Memo v2 Contract Hardening",
        "",
        "Status: **OK**",
        "",
        "## Summary",
        "",
        f"- Source file: `{summary['source_file']}`",
        f"- Memos loaded: {summary['memos_loaded']}",
        f"- Memos exported v2: {summary['memos_exported_v2']}",
        f"- Verdicts: `{summary['verdict_counts']}`",
        f"- Manual review required: `{summary['manual_review_required_all']}`",
        f"- Not financial advice: `{summary['not_financial_advice_all']}`",
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
        "## Contract",
        "",
        "- `manual_review_required = true`",
        "- `not_financial_advice = true`",
        "- `normalized_verdict` allowed values:",
        "  - `WATCHLIST`",
        "  - `REJECT`",
        "  - `NEEDS_MORE_DATA`",
        "- Keep compatibility with legacy verdicts such as `watchlist`, `avoid`, `data_insufficient`.",
        "",
        "## Next",
        "",
        "Proceed to Phase 9D — Red Flags Detector after this contract is validated.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUTS_SCOUTING_DIR.mkdir(parents=True, exist_ok=True)
    MEMO_V2_DIR.mkdir(parents=True, exist_ok=True)

    source_file = find_source_file()
    raw_payload = safe_read_json(source_file, []) if source_file else []
    raw_memos = extract_memos(raw_payload)[:MAX_TOP_N]

    v2_memos = [
        build_v2_memo(raw, source_file, idx)
        for idx, raw in enumerate(raw_memos, start=1)
    ]

    for idx, memo in enumerate(v2_memos, start=1):
        ticker = memo["ticker"]
        write_json(MEMO_V2_DIR / f"equity_research_memo_v2_{idx:02d}_{ticker}.json", memo)
        (MEMO_V2_DIR / f"equity_research_memo_v2_{idx:02d}_{ticker}.md").write_text(
            memo_markdown(memo),
            encoding="utf-8",
        )

    verdict_counts: Dict[str, int] = {}
    for memo in v2_memos:
        verdict_counts[memo["normalized_verdict"]] = verdict_counts.get(memo["normalized_verdict"], 0) + 1

    export_json = OUTPUTS_SCOUTING_DIR / "phase9c_research_memo_v2_contract_export.json"
    index_csv = OUTPUTS_SCOUTING_DIR / "phase9c_research_memo_v2_contract_index.csv"
    summary_json = OUTPUTS_SCOUTING_DIR / "phase9c_research_memo_v2_contract_summary.json"
    audit_json = OUTPUTS_SCOUTING_DIR / "phase9c_research_memo_v2_contract_audit.json"
    report_md = OUTPUTS_SCOUTING_DIR / "phase9c_research_memo_v2_contract_report.md"

    write_json(export_json, v2_memos)
    write_csv_index(index_csv, v2_memos)

    summary = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": utc_now(),
        "schema_version": SCHEMA_VERSION,
        "default_top_n": DEFAULT_TOP_N,
        "max_top_n": MAX_TOP_N,
        "source_file": str(source_file.relative_to(PROJECT_ROOT)) if source_file else None,
        "memos_loaded": len(raw_memos),
        "memos_exported_v2": len(v2_memos),
        "verdict_counts": verdict_counts,
        "manual_review_required_all": all(memo["manual_review_required"] is True for memo in v2_memos),
        "not_financial_advice_all": all(memo["not_financial_advice"] is True for memo in v2_memos),
        "allowed_verdicts": ["WATCHLIST", "REJECT", "NEEDS_MORE_DATA"],
        "export_json": str(export_json),
        "index_csv": str(index_csv),
        "memo_v2_dir": str(MEMO_V2_DIR),
        **CONTROL_FLAGS,
        "next": "Phase 9D — Red Flags Detector",
    }

    audit = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": summary["created_at"],
        "summary": summary,
        "memos": v2_memos,
        "schema_path": "schemas/equity_research_memo_schema_v0_2.json",
    }

    write_json(summary_json, summary)
    write_json(audit_json, audit)
    write_report(report_md, summary)

    print("Scout Finance — Phase 9C Research Memo v2 Contract Hardening")
    print("=" * 92)
    print()
    print("Contract")
    print("-" * 92)
    print("Status: OK")
    print(f"Schema version: {SCHEMA_VERSION}")
    print(f"Source file: {summary['source_file']}")
    print(f"Memos loaded: {summary['memos_loaded']}")
    print(f"Memos exported v2: {summary['memos_exported_v2']}")
    print(f"Verdicts: {summary['verdict_counts']}")
    print(f"Manual review required all: {summary['manual_review_required_all']}")
    print(f"Not financial advice all: {summary['not_financial_advice_all']}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 9C Research Memo v2 Contract Hardening is complete.")


if __name__ == "__main__":
    main()
