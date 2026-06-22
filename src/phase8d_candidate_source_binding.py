"""
Scout Finance — Phase 8D Candidate Source Binding

Purpose:
- Bind Phase 8C deterministic memo modules to an existing Scout Finance candidate/ranking output.
- Do not recalculate the pipeline.
- Do not call OpenAI, APIs or yfinance.
- Do not modify app.py, filters.py or releases/v0.7.
- Create TOP 3 deterministic research memo drafts from already available local data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PHASE = "8D"
STATUS_OK = "OK"
DEFAULT_TOP_N = 3
BASE_RELEASE = "v0.7.0-candidate"
SCHEMA_VERSION = "0.1"
PROMPT_VERSION = "deterministic-no-ai-v0.1"

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "scouting"
DOCS_DIR = ROOT / "docs" / "phase8"
SCHEMAS_DIR = ROOT / "schemas"
SRC_DIR = ROOT / "src"
RELEASES_DIR = ROOT / "releases"

SUMMARY_PATH = OUTPUT_DIR / "phase8d_candidate_source_binding_summary.json"
REPORT_PATH = OUTPUT_DIR / "phase8d_candidate_source_binding_report.md"
MEMOS_JSON_PATH = OUTPUT_DIR / "phase8d_candidate_source_bound_memos.json"
MEMOS_CSV_PATH = OUTPUT_DIR / "phase8d_candidate_source_bound_memos.csv"
CANDIDATES_CSV_PATH = OUTPUT_DIR / "phase8d_bound_top_candidates.csv"
DISCOVERY_JSON_PATH = OUTPUT_DIR / "phase8d_candidate_source_discovery.json"

FORBIDDEN_FILENAME_PARTS = (
    "phase8",
    "module",
    "matrix",
    "schema",
    "summary",
    "report",
    "memo",
    "freeze",
    "lock",
    "manifest",
)

PREFERRED_FILENAME_PARTS = (
    "ranking",
    "ranked",
    "candidate",
    "candidates",
    "stage3",
    "stage_3",
    "funnel",
    "final",
    "scored",
    "scores",
)

TICKER_KEYS = ("ticker", "symbol", "Ticker", "Symbol")
COMPANY_KEYS = ("company_name", "company", "name", "Company", "Name", "shortName", "longName")
SCORE_KEYS = (
    "quant_score",
    "score",
    "final_score",
    "ranking_score",
    "total_score",
    "composite_score",
    "Score",
)
RANK_KEYS = ("ranking_position", "rank", "position", "Rank", "Position")


@dataclass
class CandidateSource:
    path: Path
    source_type: str
    rows: List[Dict[str, Any]]
    ticker_key: str
    score_key: Optional[str]
    score: int
    reason: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _csv_value(row.get(k)) for k in fieldnames})


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _flatten_json_records(payload: Any) -> List[Dict[str, Any]]:
    """Extract plausible list-of-records from several common JSON output shapes."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []

    direct_keys = (
        "candidates",
        "top_candidates",
        "ranked_candidates",
        "ranking",
        "results",
        "rows",
        "data",
        "stage3_candidates",
        "final_candidates",
    )
    for key in direct_keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]

    # Last resort: inspect first nested list of dicts.
    for value in payload.values():
        if isinstance(value, list) and value and all(isinstance(x, dict) for x in value):
            return value
    return []


def _read_csv_records(path: Path) -> List[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with path.open("r", encoding="latin-1", newline="") as f:
            return list(csv.DictReader(f))


def _find_key(row: Dict[str, Any], options: Iterable[str]) -> Optional[str]:
    lowered = {str(k).lower(): k for k in row.keys()}
    for option in options:
        if option in row:
            return option
        low = option.lower()
        if low in lowered:
            return lowered[low]
    return None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    if not text:
        return None
    # Spanish decimal comma fallback, but avoid thousands separators where possible.
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _clean_ticker(value: Any) -> str:
    return str(value or "").strip().upper()


def _is_probably_ticker(value: Any) -> bool:
    ticker = _clean_ticker(value)
    if not ticker:
        return False
    if len(ticker) > 12:
        return False
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")
    return all(ch in allowed for ch in ticker)


def _score_records(path: Path, source_type: str, rows: List[Dict[str, Any]]) -> Optional[CandidateSource]:
    if not rows:
        return None
    first = rows[0]
    ticker_key = _find_key(first, TICKER_KEYS)
    if not ticker_key:
        # Try rows beyond the first in case first row is sparse.
        for row in rows[:20]:
            ticker_key = _find_key(row, TICKER_KEYS)
            if ticker_key:
                break
    if not ticker_key:
        return None

    valid_ticker_rows = [r for r in rows if _is_probably_ticker(r.get(ticker_key))]
    if not valid_ticker_rows:
        return None

    score_key = None
    for row in valid_ticker_rows[:20]:
        score_key = _find_key(row, SCORE_KEYS)
        if score_key and _to_float(row.get(score_key)) is not None:
            break
    if score_key and not any(_to_float(r.get(score_key)) is not None for r in valid_ticker_rows[:20]):
        score_key = None

    name = path.name.lower()
    score = 10
    reason_bits = []
    if score_key:
        score += 30
        reason_bits.append(f"score column: {score_key}")
    score += min(len(valid_ticker_rows), 50)
    reason_bits.append(f"valid ticker rows: {len(valid_ticker_rows)}")
    for part in PREFERRED_FILENAME_PARTS:
        if part in name:
            score += 15
            reason_bits.append(f"preferred filename token: {part}")
            break
    if any(part in name for part in FORBIDDEN_FILENAME_PARTS):
        score -= 80
        reason_bits.append("excluded/low-priority phase or metadata filename")

    if len(valid_ticker_rows) < 3:
        score -= 15
        reason_bits.append("less than 3 ticker rows")

    return CandidateSource(
        path=path,
        source_type=source_type,
        rows=valid_ticker_rows,
        ticker_key=ticker_key,
        score_key=score_key,
        score=score,
        reason="; ".join(reason_bits),
    )


def discover_candidate_sources() -> List[CandidateSource]:
    search_roots = [OUTPUT_DIR, ROOT / "data"]
    found: List[CandidateSource] = []
    for base in search_roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".csv", ".json"}:
                continue
            if path.name.startswith("."):
                continue
            try:
                if path.suffix.lower() == ".csv":
                    rows = _read_csv_records(path)
                    candidate = _score_records(path, "csv", rows)
                else:
                    payload = _read_json(path)
                    rows = _flatten_json_records(payload)
                    candidate = _score_records(path, "json", rows)
                if candidate is not None:
                    found.append(candidate)
            except Exception:
                # Discovery should be robust; the checker will verify final artefacts.
                continue
    found.sort(key=lambda item: item.score, reverse=True)
    return found


def _normalize_candidate(row: Dict[str, Any], ticker_key: str, score_key: Optional[str], idx: int) -> Dict[str, Any]:
    company_key = _find_key(row, COMPANY_KEYS)
    rank_key = _find_key(row, RANK_KEYS)
    ticker = _clean_ticker(row.get(ticker_key))
    quant_score = _to_float(row.get(score_key)) if score_key else None
    ranking_position = int(_to_float(row.get(rank_key)) or idx) if rank_key else idx
    return {
        "ticker": ticker,
        "company_name": str(row.get(company_key) or ticker).strip(),
        "ranking_position": ranking_position,
        "quant_score": quant_score,
        "source_row": row,
    }


def _sort_candidates(rows: List[Dict[str, Any]], score_key: Optional[str]) -> List[Dict[str, Any]]:
    if score_key:
        return sorted(rows, key=lambda r: (_to_float(r.get(score_key)) is not None, _to_float(r.get(score_key)) or -10**9), reverse=True)
    return rows


def _safe_call(module_name: str, function_names: Tuple[str, ...], candidate: Dict[str, Any]) -> Dict[str, Any]:
    try:
        module = __import__(f"src.{module_name}", fromlist=["dummy"])
        for function_name in function_names:
            fn = getattr(module, function_name, None)
            if callable(fn):
                result = fn(candidate)
                if isinstance(result, dict):
                    return result
    except Exception as exc:
        return {
            "status": "data_insufficient",
            "score": None,
            "objective_data": {},
            "interpretation": None,
            "data_gaps": [f"{module_name} error: {exc}"],
        }
    return {
        "status": "data_insufficient",
        "score": None,
        "objective_data": {},
        "interpretation": None,
        "data_gaps": [f"{module_name} callable not found"],
    }


def _build_memo(candidate: Dict[str, Any], source_path: Path) -> Dict[str, Any]:
    # 8C modules may expose different function names depending on package version. Try common ones.
    fundamentals = _safe_call("fundamentals", ("analyze_fundamentals", "build_fundamentals", "evaluate_fundamentals"), candidate)
    valuation = _safe_call("valuation", ("analyze_valuation", "build_valuation", "evaluate_valuation"), candidate)
    risk = _safe_call("risk_analysis", ("analyze_risk", "build_risk_analysis", "evaluate_risk"), candidate)
    moat = _safe_call("moat_analysis", ("analyze_moat", "build_moat_analysis", "evaluate_moat"), candidate)
    growth = _safe_call("growth_analysis", ("analyze_growth", "build_growth_analysis", "evaluate_growth"), candidate)
    institutional = _safe_call("institutional_view", ("analyze_institutional_view", "build_institutional_view", "evaluate_institutional_view"), candidate)
    earnings = _safe_call("earnings_analysis", ("analyze_earnings", "build_earnings_analysis", "evaluate_earnings"), candidate)

    blocks = {
        "financial_health": fundamentals,
        "valuation_analysis": valuation,
        "risk_analysis": risk,
        "moat_analysis": moat,
        "growth_analysis": growth,
        "institutional_view": institutional,
        "earnings_analysis": earnings,
    }
    all_gaps: List[str] = []
    for name, block in blocks.items():
        for gap in block.get("data_gaps") or []:
            all_gaps.append(f"{name}: {gap}")

    objective_data = {
        "ticker": candidate["ticker"],
        "company_name": candidate["company_name"],
        "ranking_position": candidate["ranking_position"],
        "quant_score": candidate.get("quant_score"),
        "source_file": str(source_path),
        "source_row": candidate.get("source_row", {}),
        "module_outputs": blocks,
    }

    memo_status = "data_insufficient" if all_gaps else "deterministic_complete"
    confidence = "low" if all_gaps else "medium"

    return {
        "ticker": candidate["ticker"],
        "company_name": candidate["company_name"],
        "ranking_position": candidate["ranking_position"],
        "quant_score": candidate.get("quant_score"),
        "memo_status": memo_status,
        "business_model": {
            "status": "data_insufficient",
            "objective_data": {},
            "interpretation": None,
            "data_gaps": ["Business model requires external/company description data not available in local ranking rows."],
        },
        "financial_health": fundamentals,
        "moat_analysis": moat,
        "valuation_analysis": valuation,
        "growth_analysis": growth,
        "risk_analysis": risk,
        "institutional_view": institutional,
        "earnings_analysis": earnings,
        "bull_case": {"status": "not_generated", "reason": "AI/opinion layer deferred."},
        "base_case": {"status": "not_generated", "reason": "AI/opinion layer deferred."},
        "bear_case": {"status": "not_generated", "reason": "AI/opinion layer deferred."},
        "final_verdict": {"status": "not_generated", "reason": "AI/opinion layer deferred."},
        "confidence": confidence,
        "data_gaps": all_gaps + ["business_model: local ranking rows do not provide enough company narrative data."],
        "sources": [{"type": "local_file", "path": str(source_path)}],
        "objective_data_json": objective_data,
        "ai_interpretation_json": {},
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "model_used": None,
        "estimated_cost": 0.0,
    }


def run_phase8d(top_n: int = DEFAULT_TOP_N) -> Dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    discovery = discover_candidate_sources()
    discovery_payload = [
        {
            "path": str(item.path),
            "source_type": item.source_type,
            "rows": len(item.rows),
            "ticker_key": item.ticker_key,
            "score_key": item.score_key,
            "discovery_score": item.score,
            "reason": item.reason,
        }
        for item in discovery[:25]
    ]
    _write_json(DISCOVERY_JSON_PATH, discovery_payload)

    selected = discovery[0] if discovery else None
    normalized: List[Dict[str, Any]] = []
    memos: List[Dict[str, Any]] = []

    if selected:
        sorted_rows = _sort_candidates(selected.rows, selected.score_key)
        seen = set()
        for row in sorted_rows:
            candidate = _normalize_candidate(row, selected.ticker_key, selected.score_key, len(normalized) + 1)
            if not candidate["ticker"] or candidate["ticker"] in seen:
                continue
            seen.add(candidate["ticker"])
            normalized.append(candidate)
            if len(normalized) >= top_n:
                break
        memos = [_build_memo(candidate, selected.path) for candidate in normalized]

    _write_json(MEMOS_JSON_PATH, memos)
    _write_csv(
        MEMOS_CSV_PATH,
        [
            {
                "ticker": memo.get("ticker"),
                "company_name": memo.get("company_name"),
                "ranking_position": memo.get("ranking_position"),
                "quant_score": memo.get("quant_score"),
                "memo_status": memo.get("memo_status"),
                "confidence": memo.get("confidence"),
                "estimated_cost": memo.get("estimated_cost"),
                "model_used": memo.get("model_used"),
                "data_gaps_count": len(memo.get("data_gaps") or []),
            }
            for memo in memos
        ],
    )
    _write_csv(
        CANDIDATES_CSV_PATH,
        [
            {
                "ranking_position": candidate.get("ranking_position"),
                "ticker": candidate.get("ticker"),
                "company_name": candidate.get("company_name"),
                "quant_score": candidate.get("quant_score"),
                "source_file": str(selected.path) if selected else None,
            }
            for candidate in normalized
        ],
    )

    controls = {
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "pipeline_recalculated": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": False,
        "enable_openai_env": _truthy_env("ENABLE_OPENAI"),
    }

    signatures = {
        "app_py_sha256": _sha256(ROOT / "app.py"),
        "filters_py_sha256": _sha256(SRC_DIR / "filters.py"),
        "release_zip_sha256": _sha256(RELEASES_DIR / "Scout_Finance_v0.7.0_candidate_FREEZE.zip"),
    }

    summary = {
        "phase": PHASE,
        "status": STATUS_OK,
        "created_at": _now_iso(),
        "base_release": BASE_RELEASE,
        "default_top_n": top_n,
        "candidate_source": str(selected.path) if selected else None,
        "candidate_source_type": selected.source_type if selected else None,
        "candidate_source_rows": len(selected.rows) if selected else 0,
        "discovered_sources": len(discovery),
        "memos_created": len(memos),
        "top_tickers": [memo.get("ticker") for memo in memos],
        "controls": controls,
        "signatures": signatures,
        "outputs": {
            "summary": str(SUMMARY_PATH),
            "report": str(REPORT_PATH),
            "memos_json": str(MEMOS_JSON_PATH),
            "memos_csv": str(MEMOS_CSV_PATH),
            "top_candidates_csv": str(CANDIDATES_CSV_PATH),
            "discovery_json": str(DISCOVERY_JSON_PATH),
        },
        "next": "8E — Persist equity_research_memos and prepare UI/export integration",
    }
    _write_json(SUMMARY_PATH, summary)
    _write_report(summary, discovery_payload, memos)
    return summary


def _write_report(summary: Dict[str, Any], discovery_payload: List[Dict[str, Any]], memos: List[Dict[str, Any]]) -> None:
    lines = [
        "# Scout Finance — Phase 8D Candidate Source Binding",
        "",
        "## Status",
        "",
        f"- Status: {summary['status']}",
        f"- Base release: {summary['base_release']}",
        f"- Default TOP N: {summary['default_top_n']}",
        f"- Candidate source: {summary['candidate_source']}",
        f"- Candidate source rows: {summary['candidate_source_rows']}",
        f"- Memos created: {summary['memos_created']}",
        "",
        "## Controls",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "- app.py modified: False",
        "- src/filters.py modified: False",
        "- releases/v0.7 modified: False",
        "",
        "## Design rule",
        "",
        "Phase 8D does not invent data. It binds deterministic Phase 8C memo modules to existing local candidate/ranking outputs only.",
        "Missing values remain marked as `data_insufficient`.",
        "",
        "## Top candidates bound",
        "",
    ]
    if memos:
        lines.append("| Rank | Ticker | Company | Quant score | Memo status |")
        lines.append("|---:|---|---|---:|---|")
        for memo in memos:
            score = memo.get("quant_score")
            score_text = "" if score is None else f"{score:.2f}"
            lines.append(
                f"| {memo.get('ranking_position')} | {memo.get('ticker')} | {memo.get('company_name')} | {score_text} | {memo.get('memo_status')} |"
            )
    else:
        lines.append("No TOP candidates were bound. Candidate discovery found no suitable local ranking/candidate file.")
    lines.extend([
        "",
        "## Candidate discovery preview",
        "",
        "| Discovery score | Rows | Type | File | Reason |",
        "|---:|---:|---|---|---|",
    ])
    for item in discovery_payload[:10]:
        lines.append(
            f"| {item.get('discovery_score')} | {item.get('rows')} | {item.get('source_type')} | `{item.get('path')}` | {item.get('reason')} |"
        )
    lines.extend([
        "",
        "## Next",
        "",
        summary["next"],
        "",
    ])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    summary = run_phase8d(DEFAULT_TOP_N)
    print("Scout Finance — Phase 8D Candidate Source Binding")
    print("=" * 92)
    print()
    print("Candidate binding")
    print("-" * 92)
    print(f"Status: {summary['status']}")
    print(f"Candidate source: {summary['candidate_source']}")
    print(f"Rows available: {summary['candidate_source_rows']}")
    print(f"Default TOP N: {summary['default_top_n']}")
    print(f"Memos created: {summary['memos_created']}")
    print(f"Top tickers: {', '.join(summary['top_tickers']) if summary['top_tickers'] else 'None'}")
    print(f"OpenAI called: {summary['controls']['openai_called']}")
    print(f"API called: {summary['controls']['api_called']}")
    print(f"yfinance called: {summary['controls']['yfinance_called']}")
    print(f"Pipeline recalculated: {summary['controls']['pipeline_recalculated']}")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 8D candidate source binding is complete.")


if __name__ == "__main__":
    main()
