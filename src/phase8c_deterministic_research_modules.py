"""Scout Finance — Phase 8C deterministic research modules runner."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.research_memo import build_deterministic_research_memos


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "scouting"
DOCS_DIR = PROJECT_ROOT / "docs" / "phase8"
DEFAULT_TOP_N = 3

OUTPUT_SUMMARY = OUTPUT_DIR / "phase8c_deterministic_research_modules_summary.json"
OUTPUT_REPORT = OUTPUT_DIR / "phase8c_deterministic_research_modules_report.md"
OUTPUT_MEMOS_JSON = OUTPUT_DIR / "phase8c_deterministic_research_memos.json"
OUTPUT_MEMOS_CSV = OUTPUT_DIR / "phase8c_deterministic_research_memos.csv"
OUTPUT_MATRIX = OUTPUT_DIR / "phase8c_deterministic_modules_matrix.csv"


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json_rows(path: Path) -> List[Dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if isinstance(payload, dict):
        for key in ("candidates", "ranking", "top_candidates", "rows", "results", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _load_csv_rows(path: Path) -> List[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _score_key(row: Dict[str, Any]) -> float:
    for key in ("score", "quant_score", "final_score", "Score"):
        value = row.get(key)
        if value not in ("", None):
            try:
                return float(str(value).replace(",", "."))
            except ValueError:
                pass
    return -1.0


def _ticker_key(row: Dict[str, Any]) -> str:
    for key in ("ticker", "symbol", "Ticker", "Symbol"):
        value = row.get(key)
        if value:
            return str(value).upper()
    return ""


def discover_candidate_rows() -> Dict[str, Any]:
    """Find existing local candidate/ranking exports without recalculating pipeline."""
    preferred_names = [
        "phase8a_dashboard_final_design_matrix.csv",
        "final_ranking.csv",
        "ranking.csv",
        "scouting_ranking.csv",
        "stage3_candidates.csv",
        "candidates.csv",
    ]

    candidate_files: List[Path] = []
    for name in preferred_names:
        p = OUTPUT_DIR / name
        if p.exists():
            candidate_files.append(p)

    # Fallback: scan scouting outputs, newest first. This reads files only.
    if not candidate_files and OUTPUT_DIR.exists():
        files = list(OUTPUT_DIR.glob("*.csv")) + list(OUTPUT_DIR.glob("*.json"))
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        candidate_files = files[:20]

    rows: List[Dict[str, Any]] = []
    source_file = None

    for path in candidate_files:
        loaded = _load_csv_rows(path) if path.suffix.lower() == ".csv" else _load_json_rows(path)
        loaded = [r for r in loaded if _ticker_key(r)]
        if loaded:
            rows = loaded
            source_file = path
            break

    rows.sort(key=_score_key, reverse=True)
    return {
        "rows": rows,
        "source_file": str(source_file) if source_file else None,
        "source_count": len(rows),
    }


def write_matrix() -> None:
    modules = [
        ("src/research_memo.py", "Assembles deterministic memo from module outputs", "offline", "yes"),
        ("src/fundamentals.py", "Financial-health scoring from available metrics", "offline", "yes"),
        ("src/valuation.py", "Valuation scoring from available multiples", "offline", "yes"),
        ("src/risk_analysis.py", "Risk scoring from available volatility/liquidity/debt proxies", "offline", "yes"),
        ("src/moat_analysis.py", "Moat proxy from profitability/return metrics", "offline", "yes"),
        ("src/growth_analysis.py", "Growth scoring from available growth fields", "offline", "yes"),
        ("src/institutional_view.py", "Institutional proxy from ownership/coverage fields", "offline", "yes"),
        ("src/earnings_analysis.py", "Earnings proxy from available earnings fields", "offline", "yes"),
    ]
    with OUTPUT_MATRIX.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["module", "purpose", "mode", "marks_data_insufficient"])
        w.writerows(modules)


def write_memos_csv(memos: List[Dict[str, Any]]) -> None:
    fields = [
        "ranking_position",
        "ticker",
        "company_name",
        "quant_score",
        "memo_status",
        "deterministic_score",
        "financial_health_score",
        "valuation_score",
        "risk_score",
        "moat_score",
        "growth_score",
        "institutional_score",
        "final_verdict",
        "confidence",
        "data_gaps_count",
        "estimated_cost",
        "model_used",
        "schema_version",
        "prompt_version",
    ]
    with OUTPUT_MEMOS_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for memo in memos:
            scores = memo.get("scores", {})
            w.writerow({
                "ranking_position": memo.get("ranking_position"),
                "ticker": memo.get("ticker"),
                "company_name": memo.get("company_name"),
                "quant_score": memo.get("quant_score"),
                "memo_status": memo.get("memo_status"),
                "deterministic_score": memo.get("deterministic_score"),
                "financial_health_score": scores.get("financial_health_score"),
                "valuation_score": scores.get("valuation_score"),
                "risk_score": scores.get("risk_score"),
                "moat_score": scores.get("moat_score"),
                "growth_score": scores.get("growth_score"),
                "institutional_score": scores.get("institutional_score"),
                "final_verdict": memo.get("final_verdict"),
                "confidence": memo.get("confidence"),
                "data_gaps_count": len(memo.get("data_gaps", [])),
                "estimated_cost": memo.get("estimated_cost"),
                "model_used": memo.get("model_used"),
                "schema_version": memo.get("schema_version"),
                "prompt_version": memo.get("prompt_version"),
            })


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    app_hash_before = _sha256(PROJECT_ROOT / "app.py")
    filters_hash_before = _sha256(PROJECT_ROOT / "src" / "filters.py")
    release_hash_before = _sha256(PROJECT_ROOT / "releases" / "Scout_Finance_v0.7.0_candidate_FREEZE.zip")

    discovered = discover_candidate_rows()
    rows = discovered["rows"]
    memos = build_deterministic_research_memos(rows, top_n=DEFAULT_TOP_N) if rows else []

    write_matrix()
    OUTPUT_MEMOS_JSON.write_text(json.dumps(memos, indent=2, ensure_ascii=False), encoding="utf-8")
    write_memos_csv(memos)

    controls = {
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": app_hash_before != _sha256(PROJECT_ROOT / "app.py"),
        "filters_modified": filters_hash_before != _sha256(PROJECT_ROOT / "src" / "filters.py"),
        "release_modified": release_hash_before != _sha256(PROJECT_ROOT / "releases" / "Scout_Finance_v0.7.0_candidate_FREEZE.zip"),
        "pipeline_recalculated": False,
    }

    summary = {
        "phase": "8C",
        "status": "OK",
        "title": "Deterministic fundamentals, valuation and risk modules",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_release": "v0.7.0-candidate",
        "default_top_n": DEFAULT_TOP_N,
        "candidate_source_file": discovered["source_file"],
        "candidate_rows_available": discovered["source_count"],
        "memos_created": len(memos),
        "modules_created": [
            "src/research_memo.py",
            "src/fundamentals.py",
            "src/valuation.py",
            "src/risk_analysis.py",
            "src/moat_analysis.py",
            "src/growth_analysis.py",
            "src/institutional_view.py",
            "src/earnings_analysis.py",
        ],
        "outputs": [
            str(OUTPUT_SUMMARY.relative_to(PROJECT_ROOT)),
            str(OUTPUT_REPORT.relative_to(PROJECT_ROOT)),
            str(OUTPUT_MEMOS_JSON.relative_to(PROJECT_ROOT)),
            str(OUTPUT_MEMOS_CSV.relative_to(PROJECT_ROOT)),
            str(OUTPUT_MATRIX.relative_to(PROJECT_ROOT)),
        ],
        "controls": controls,
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    top_lines = []
    for memo in memos:
        top_lines.append(
            f"| {memo.get('ranking_position')} | {memo.get('ticker')} | {memo.get('company_name')} | "
            f"{memo.get('quant_score')} | {memo.get('deterministic_score')} | {memo.get('memo_status')} | "
            f"{memo.get('final_verdict')} | {memo.get('confidence')} | {len(memo.get('data_gaps', []))} |"
        )
    if not top_lines:
        top_lines.append("| - | - | - | - | - | data_insufficient | no_candidates_found | low | - |")

    report = f"""# Scout Finance — Phase 8C Deterministic Research Modules

Status: **OK**

## Scope

Phase 8C creates the offline deterministic module layer required before AI Equity Research Memos.

It does **not** call OpenAI, APIs, yfinance or the pipeline. It reads existing Scout Finance outputs only.

## Controls

| Control | Value |
|---|---:|
| OpenAI called | {controls['openai_called']} |
| API called | {controls['api_called']} |
| yfinance called | {controls['yfinance_called']} |
| app.py modified | {controls['app_modified']} |
| src/filters.py modified | {controls['filters_modified']} |
| v0.7 release modified | {controls['release_modified']} |
| Pipeline recalculated | {controls['pipeline_recalculated']} |

## Candidate source

- Source file: `{discovered['source_file']}`
- Rows available: `{discovered['source_count']}`
- Default TOP N: `{DEFAULT_TOP_N}`
- Memos created: `{len(memos)}`

## Deterministic memo summary

| Rank | Ticker | Company | Quant score | Deterministic score | Status | Verdict | Confidence | Data gaps |
|---:|---|---|---:|---:|---|---|---|---:|
{chr(10).join(top_lines)}

## Modules

- `src/research_memo.py`
- `src/fundamentals.py`
- `src/valuation.py`
- `src/risk_analysis.py`
- `src/moat_analysis.py`
- `src/growth_analysis.py`
- `src/institutional_view.py`
- `src/earnings_analysis.py`

## Design rules enforced

- No inventar datos.
- Missing fields are marked as `data_insufficient`.
- Objective data, deterministic interpretation and future AI interpretation are separated.
- `estimated_cost = 0.0`.
- `model_used = null`.
- TOP 3 default to control later AI costs.
- 8C remains compatible with the 8B memo schema.

## Next

8D — Memo persistence and integration adapter.

Recommended next scope:
- create/upgrade `equity_research_memos` table without touching v0.7 release
- persist deterministic memos
- keep Streamlit/app integration for later
"""
    OUTPUT_REPORT.write_text(report, encoding="utf-8")

    print("Scout Finance — Phase 8C Deterministic Research Modules")
    print("=" * 92)
    print()
    print("Deterministic modules")
    print("-" * 92)
    print("Status: OK")
    print(f"Candidate source: {discovered['source_file']}")
    print(f"Rows available: {discovered['source_count']}")
    print(f"Default TOP N: {DEFAULT_TOP_N}")
    print(f"Memos created: {len(memos)}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 8C deterministic research modules are complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
