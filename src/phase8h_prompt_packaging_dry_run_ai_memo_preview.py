from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "scouting"
PROMPT_DIR = OUTPUT_DIR / "research_memo_ai_prompts"

DEFAULT_TOP_N = 3
MAX_TOP_N = 3

PHASE = "8H"
PHASE_NAME = "Prompt Packaging and Dry-run AI Memo Preview"

CONTROL_FLAGS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "app_modified": False,
    "filters_modified": False,
    "release_modified": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S%z")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_memos() -> tuple[List[Dict[str, Any]], Optional[str]]:
    candidates = [
        OUTPUT_DIR / "phase8f_research_memo_export.json",
        OUTPUT_DIR / "phase8e_persisted_equity_research_memos.json",
        OUTPUT_DIR / "phase8d_candidate_source_bound_memos.json",
    ]
    for path in candidates:
        data = read_json(path, default=None)
        if isinstance(data, list) and data:
            return data[:MAX_TOP_N], str(path)
    return [], None


def safe_get(memo: Dict[str, Any], key: str, default: Any = None) -> Any:
    return memo.get(key, default)


def build_prompt_package(memo: Dict[str, Any], index: int, gate_decision: Dict[str, Any]) -> Dict[str, Any]:
    ticker = str(safe_get(memo, "ticker", "UNKNOWN")).upper()
    company_name = safe_get(memo, "company_name", "")
    ranking_position = safe_get(memo, "ranking_position", index)
    quant_score = safe_get(memo, "quant_score", None)
    memo_status = safe_get(memo, "memo_status", "data_insufficient")
    objective_data = safe_get(memo, "objective_data", safe_get(memo, "objective_data_json", {}))
    data_gaps = safe_get(memo, "data_gaps", [])
    scores = safe_get(memo, "scores", {})
    sources = safe_get(memo, "sources", [])

    system_prompt = (
        "You are Scout Finance AI Equity Research Memo Assistant. "
        "You must not invent data. Separate objective data from interpretation. "
        "If data is missing, explicitly mark data_insufficient. "
        "Do not provide personalized financial advice. "
        "Do not claim real-time market knowledge unless supplied in the input."
    )

    user_prompt = {
        "task": "Create an AI interpretation layer for an equity research memo using only the supplied data.",
        "constraints": [
            "Do not invent facts.",
            "Use only supplied objective_data, scores, sources and data_gaps.",
            "Separate bull_case, base_case, bear_case, final_verdict and confidence.",
            "Mention uncertainty and data gaps clearly.",
            "Return JSON compatible with equity_research_memo_schema_v0_1.",
        ],
        "ticker": ticker,
        "company_name": company_name,
        "ranking_position": ranking_position,
        "quant_score": quant_score,
        "memo_status": memo_status,
        "scores": scores,
        "objective_data": objective_data,
        "data_gaps": data_gaps,
        "sources": sources,
    }

    dry_run_preview = {
        "ticker": ticker,
        "company_name": company_name,
        "ai_interpretation_status": "dry_run_only",
        "openai_called": False,
        "estimated_cost": 0.0,
        "model_used": None,
        "preview_sections": {
            "bull_case": "DRY RUN PLACEHOLDER — would be generated only if AI gate is open.",
            "base_case": "DRY RUN PLACEHOLDER — would be generated only if AI gate is open.",
            "bear_case": "DRY RUN PLACEHOLDER — would be generated only if AI gate is open.",
            "final_verdict": "DRY RUN PLACEHOLDER — no investment recommendation generated.",
            "confidence": "data_insufficient",
        },
        "data_gaps": data_gaps,
    }

    package = {
        "phase": PHASE,
        "prompt_version": "research_memo_ai_interpretation_v0_1",
        "schema_version": "equity_research_memo_schema_v0_1",
        "ticker": ticker,
        "company_name": company_name,
        "ranking_position": ranking_position,
        "quant_score": quant_score,
        "memo_status": memo_status,
        "ai_gate_status": gate_decision.get("gate_status", "unknown"),
        "ai_allowed": bool(gate_decision.get("ai_allowed", False)),
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "dry_run_preview": dry_run_preview,
        "openai_called": False,
        "estimated_cost": 0.0,
        "model_used": None,
    }
    package["prompt_sha256"] = sha256_text(json.dumps({"system_prompt": system_prompt, "user_prompt": user_prompt}, ensure_ascii=False, sort_keys=True))
    return package


def write_prompt_markdown(package: Dict[str, Any], path: Path) -> None:
    md = f"""# Scout Finance — AI Research Memo Prompt Package

## Ticker
{package.get("ticker")}

## Company
{package.get("company_name")}

## Phase
{PHASE} — {PHASE_NAME}

## Gate
- AI gate status: {package.get("ai_gate_status")}
- AI allowed: {package.get("ai_allowed")}
- OpenAI called: False
- Estimated cost: 0.0
- Model used: null

## System prompt

```text
{package.get("system_prompt")}
```

## User prompt payload

```json
{json.dumps(package.get("user_prompt"), ensure_ascii=False, indent=2)}
```

## Dry-run preview

```json
{json.dumps(package.get("dry_run_preview"), ensure_ascii=False, indent=2)}
```

## Safety notes

- No inventar datos.
- data_insufficient debe mantenerse cuando falten datos.
- Objective data and AI interpretation remain separated.
- This file is a dry-run package only; no API/OpenAI call was made.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)

    gate_decision = read_json(OUTPUT_DIR / "phase8g_ai_interpretation_gate_decision.json", default={})
    memos, source_path = load_memos()

    packages: List[Dict[str, Any]] = []
    index_rows: List[Dict[str, Any]] = []
    audit_reports: List[Dict[str, Any]] = []

    for idx, memo in enumerate(memos[:MAX_TOP_N], start=1):
        pkg = build_prompt_package(memo, idx, gate_decision)
        ticker = pkg["ticker"]
        json_path = PROMPT_DIR / f"ai_prompt_package_{idx:02d}_{ticker}.json"
        md_path = PROMPT_DIR / f"ai_prompt_package_{idx:02d}_{ticker}.md"

        write_json(json_path, pkg)
        write_prompt_markdown(pkg, md_path)

        pkg["prompt_package_json_path"] = str(json_path)
        pkg["prompt_package_md_path"] = str(md_path)
        packages.append(pkg)

        index_rows.append({
            "ranking_position": pkg.get("ranking_position"),
            "ticker": ticker,
            "company_name": pkg.get("company_name"),
            "quant_score": pkg.get("quant_score"),
            "memo_status": pkg.get("memo_status"),
            "ai_gate_status": pkg.get("ai_gate_status"),
            "ai_allowed": pkg.get("ai_allowed"),
            "openai_called": False,
            "estimated_cost": 0.0,
            "model_used": "",
            "prompt_sha256": pkg.get("prompt_sha256"),
            "json_path": str(json_path),
            "md_path": str(md_path),
        })

        audit_reports.append({
            "ticker": ticker,
            "json_path": str(json_path),
            "json_exists": json_path.exists(),
            "json_sha256": hashlib.sha256(json_path.read_bytes()).hexdigest() if json_path.exists() else None,
            "md_path": str(md_path),
            "md_exists": md_path.exists(),
            "md_sha256": hashlib.sha256(md_path.read_bytes()).hexdigest() if md_path.exists() else None,
            "openai_called": False,
            "estimated_cost": 0.0,
        })

    write_json(OUTPUT_DIR / "phase8h_ai_prompt_packages.json", packages)

    csv_path = OUTPUT_DIR / "phase8h_ai_prompt_packages_index.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "ranking_position", "ticker", "company_name", "quant_score", "memo_status",
            "ai_gate_status", "ai_allowed", "openai_called", "estimated_cost", "model_used",
            "prompt_sha256", "json_path", "md_path",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in index_rows:
            writer.writerow(row)

    audit = {
        "phase": PHASE,
        "status": "OK",
        "source": source_path,
        "packages_created": len(packages),
        "reports": audit_reports,
        **CONTROL_FLAGS,
    }
    write_json(OUTPUT_DIR / "phase8h_prompt_packaging_dry_run_audit.json", audit)

    summary = {
        "phase": PHASE,
        "phase_name": PHASE_NAME,
        "status": "OK",
        "default_top_n": DEFAULT_TOP_N,
        "max_top_n": MAX_TOP_N,
        "source": source_path,
        "memos_loaded": len(memos),
        "prompt_packages_created": len(packages),
        "prompt_dir": str(PROMPT_DIR),
        "ai_gate_status": gate_decision.get("gate_status", "unknown"),
        "ai_allowed": bool(gate_decision.get("ai_allowed", False)),
        "estimated_total_cost": 0.0,
        "next": "8I — Optional AI memo execution sandbox",
        **CONTROL_FLAGS,
    }
    write_json(OUTPUT_DIR / "phase8h_prompt_packaging_dry_run_summary.json", summary)

    report = f"""# Scout Finance — Phase 8H Prompt Packaging and Dry-run AI Memo Preview

## Status
OK

## Source
{source_path}

## Results
- Memos loaded: {len(memos)}
- Prompt packages created: {len(packages)}
- Default TOP N: {DEFAULT_TOP_N}
- MAX TOP N: {MAX_TOP_N}
- AI gate status: {summary["ai_gate_status"]}
- AI allowed: {summary["ai_allowed"]}
- Estimated total cost: 0.0

## Controls
- OpenAI called: False
- API called: False
- yfinance called: False
- Pipeline recalculated: False
- app.py modified: False
- filters.py modified: False
- release modified: False

## Safety
- No inventar datos.
- data_insufficient remains valid when data is missing.
- Objective data remains separated from AI interpretation.
- This phase creates prompts and dry-run previews only.
- No OpenAI/API call is made.

## Outputs
- outputs/scouting/phase8h_ai_prompt_packages.json
- outputs/scouting/phase8h_ai_prompt_packages_index.csv
- outputs/scouting/phase8h_prompt_packaging_dry_run_audit.json
- outputs/scouting/research_memo_ai_prompts/

## Next
8I — Optional AI memo execution sandbox
"""
    (OUTPUT_DIR / "phase8h_prompt_packaging_dry_run_report.md").write_text(report, encoding="utf-8")

    print("Scout Finance — Phase 8H Prompt Packaging and Dry-run AI Memo Preview")
    print("=" * 92)
    print()
    print("Prompt packaging")
    print("-" * 92)
    print("Status: OK")
    print(f"Source: {source_path}")
    print(f"Memos loaded: {len(memos)}")
    print(f"Default TOP N: {DEFAULT_TOP_N}")
    print(f"Prompt packages created: {len(packages)}")
    print(f"AI gate status: {summary['ai_gate_status']}")
    print(f"AI allowed: {summary['ai_allowed']}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 8H prompt packaging and dry-run AI memo preview is complete.")


if __name__ == "__main__":
    main()
