from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PHASE = "8J"
DEFAULT_TOP_N = 3
MAX_TOP_N = 3
EXPECTED_PHASES = ["8A", "8B", "8C", "8D", "8E", "8F", "8G", "8H", "8I"]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utc_run_id() -> str:
    return "phase8j_" + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S%z")


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


def sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path, root: Path) -> Dict[str, Any]:
    return {
        "path": str(path),
        "relative_path": str(path.relative_to(root)) if path.exists() else str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "sha256": sha256_file(path),
    }


def collect_phase_status(root: Path) -> List[Dict[str, Any]]:
    out = root / "outputs" / "scouting"
    phase_files = {
        "8A": out / "phase8a_dashboard_final_design_summary.json",
        "8B": out / "phase8b_ai_equity_research_memo_blueprint_summary.json",
        "8C": out / "phase8c_deterministic_research_modules_summary.json",
        "8D": out / "phase8d_candidate_source_binding_summary.json",
        "8E": out / "phase8e_equity_research_memo_persistence_summary.json",
        "8F": out / "phase8f_research_memo_export_report_layer_summary.json",
        "8G": out / "phase8g_optional_ai_interpretation_gate_summary.json",
        "8H": out / "phase8h_prompt_packaging_dry_run_summary.json",
        "8I": out / "phase8i_optional_ai_execution_sandbox_summary.json",
    }

    rows: List[Dict[str, Any]] = []
    for phase, path in phase_files.items():
        data = read_json(path, {})
        rows.append({
            "phase": phase,
            "summary_path": str(path),
            "summary_exists": path.exists(),
            "status": data.get("status"),
            "default_top_n": data.get("default_top_n"),
            "max_top_n": data.get("max_top_n"),
            "openai_called": data.get("openai_called"),
            "api_called": data.get("api_called"),
            "yfinance_called": data.get("yfinance_called"),
            "pipeline_recalculated": data.get("pipeline_recalculated"),
            "app_modified": data.get("app_modified"),
            "filters_modified": data.get("filters_modified"),
            "release_modified": data.get("release_modified"),
        })
    return rows


def discover_key_outputs(root: Path) -> List[Path]:
    out = root / "outputs" / "scouting"
    paths = [
        out / "phase8a_dashboard_final_design_summary.json",
        out / "phase8a_dashboard_final_design_report.md",
        out / "phase8a_dashboard_final_design_matrix.csv",
        out / "phase8b_ai_equity_research_memo_blueprint_summary.json",
        out / "phase8b_ai_equity_research_memo_blueprint_report.md",
        out / "phase8b_ai_equity_research_memo_modules_matrix.csv",
        out / "phase8b_equity_research_memos_table_schema.json",
        root / "schemas" / "equity_research_memo_schema_v0_1.json",
        out / "phase8c_deterministic_research_modules_summary.json",
        out / "phase8c_deterministic_research_memos.json",
        out / "phase8d_candidate_source_binding_summary.json",
        out / "phase8d_candidate_source_bound_memos.json",
        out / "phase8d_bound_top_candidates.csv",
        out / "phase8e_equity_research_memo_persistence_summary.json",
        out / "phase8e_persisted_equity_research_memos.json",
        out / "phase8e_equity_research_memo_db_audit.json",
        out / "phase8f_research_memo_export_report_layer_summary.json",
        out / "phase8f_research_memo_export.json",
        out / "phase8f_research_memo_index.csv",
        out / "phase8f_research_memo_export_report_layer_audit.json",
        out / "phase8g_optional_ai_interpretation_gate_summary.json",
        out / "phase8g_ai_interpretation_gate_decision.json",
        out / "phase8g_ai_interpretation_plan.json",
        out / "phase8h_prompt_packaging_dry_run_summary.json",
        out / "phase8h_ai_prompt_packages.json",
        out / "phase8h_prompt_packaging_dry_run_audit.json",
        out / "phase8i_optional_ai_execution_sandbox_summary.json",
        out / "phase8i_ai_execution_sandbox_results.json",
        out / "phase8i_ai_execution_sandbox_audit.json",
        root / "data" / "demo" / "demo_signals.db",
    ]
    return paths


def write_phase_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fields = [
        "phase",
        "summary_exists",
        "status",
        "default_top_n",
        "max_top_n",
        "openai_called",
        "api_called",
        "yfinance_called",
        "pipeline_recalculated",
        "app_modified",
        "filters_modified",
        "release_modified",
        "summary_path",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def write_outputs_csv(path: Path, records: List[Dict[str, Any]]) -> None:
    fields = ["relative_path", "exists", "size_bytes", "sha256", "path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow({key: row.get(key) for key in fields})


def evaluate_readiness(phase_rows: List[Dict[str, Any]], root: Path) -> Dict[str, Any]:
    blockers: List[str] = []
    warnings: List[str] = []

    for row in phase_rows:
        phase = row["phase"]
        if not row.get("summary_exists"):
            blockers.append(f"Missing summary for phase {phase}")
        if row.get("status") != "OK":
            blockers.append(f"Phase {phase} status is not OK")
        if phase in {"8C", "8D", "8E", "8F", "8G", "8H", "8I"}:
            for flag in ["openai_called", "api_called", "yfinance_called", "pipeline_recalculated", "app_modified", "filters_modified", "release_modified"]:
                if row.get(flag) not in (False, None):
                    blockers.append(f"Phase {phase} control flag not safe: {flag}={row.get(flag)}")
        if row.get("default_top_n") not in (None, DEFAULT_TOP_N):
            warnings.append(f"Phase {phase} default_top_n differs from 3: {row.get('default_top_n')}")
        if row.get("max_top_n") not in (None, MAX_TOP_N):
            warnings.append(f"Phase {phase} max_top_n differs from 3: {row.get('max_top_n')}")

    out = root / "outputs" / "scouting"
    required_dirs = [
        out / "research_memos",
        out / "research_memo_ai_prompts",
        out / "research_memo_ai_execution_sandbox",
    ]
    for d in required_dirs:
        if not d.exists():
            blockers.append(f"Missing directory: {d}")

    top_candidates = out / "phase8d_bound_top_candidates.csv"
    if not top_candidates.exists():
        blockers.append("Missing bound TOP 3 candidates CSV from 8D")

    db_audit = read_json(out / "phase8e_equity_research_memo_db_audit.json", {})
    if db_audit and db_audit.get("table") not in (None, "equity_research_memos"):
        blockers.append("8E DB audit table is not equity_research_memos")

    gate = read_json(out / "phase8g_ai_interpretation_gate_decision.json", {})
    if gate.get("gate_status") != "closed":
        warnings.append("AI gate is not closed. Review before releasing v0.8 as no-real-AI release.")
    if gate.get("ai_allowed") not in (False, None):
        warnings.append("AI gate ai_allowed is not False. Review cost controls.")

    readiness = "ready_for_v0_8_candidate" if not blockers else "not_ready"
    recommendation = (
        "Freeze v0.8 candidate as quantitative ranking + deterministic equity research memo layer, with AI execution disabled by default."
        if not blockers
        else "Do not freeze v0.8 candidate until blockers are resolved."
    )

    return {
        "readiness": readiness,
        "blockers": blockers,
        "warnings": warnings,
        "recommendation": recommendation,
        "release_positioning": {
            "v0_8_scope": "ranking cuantitativo + AI Equity Research Memo estructurado en modo determinista/dry-run/sandbox",
            "real_ai_calls": "disabled_by_default",
            "cost_control": "explicit gate required before any future real AI execution",
            "top_n": 3,
        },
    }


def write_report(path: Path, summary: Dict[str, Any], phase_rows: List[Dict[str, Any]], readiness: Dict[str, Any]) -> None:
    lines = [
        "# Phase 8J — AI Memo Integration Readiness and v0.8 Candidate Audit",
        "",
        f"Status: **{summary['status']}**",
        "",
        "## Executive summary",
        "",
        f"- Readiness: `{readiness['readiness']}`",
        f"- Recommendation: {readiness['recommendation']}",
        f"- Default TOP N: {DEFAULT_TOP_N}",
        f"- MAX TOP N: {MAX_TOP_N}",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "- No inventar datos",
        "- `data_insufficient` remains mandatory when data is missing",
        "",
        "## Phase status",
        "",
        "| Phase | Summary | Status | OpenAI | API | yfinance | Pipeline | app.py | filters.py | release |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in phase_rows:
        lines.append(
            f"| {row['phase']} | {row.get('summary_exists')} | {row.get('status')} | "
            f"{row.get('openai_called')} | {row.get('api_called')} | {row.get('yfinance_called')} | "
            f"{row.get('pipeline_recalculated')} | {row.get('app_modified')} | {row.get('filters_modified')} | {row.get('release_modified')} |"
        )

    lines += [
        "",
        "## Blockers",
        "",
    ]
    if readiness["blockers"]:
        lines += [f"- {b}" for b in readiness["blockers"]]
    else:
        lines.append("- None")

    lines += [
        "",
        "## Warnings",
        "",
    ]
    if readiness["warnings"]:
        lines += [f"- {w}" for w in readiness["warnings"]]
    else:
        lines.append("- None")

    lines += [
        "",
        "## v0.8 candidate scope",
        "",
        "- Quantitative ranking remains the core.",
        "- Equity Research Memo layer exists for TOP 3 candidates.",
        "- Deterministic modules, persistence, exports, prompt packaging and execution sandbox are validated.",
        "- Real AI calls remain disabled by default.",
        "- This is not financial advice.",
        "",
        "## Next",
        "",
        "Recommended next step: create a v0.8 release candidate freeze package only after reviewing this audit.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    root = project_root()
    out = root / "outputs" / "scouting"
    run_id = utc_run_id()

    phase_rows = collect_phase_status(root)
    output_records = [file_record(path, root) for path in discover_key_outputs(root)]
    readiness = evaluate_readiness(phase_rows, root)

    status = "OK" if readiness["readiness"] == "ready_for_v0_8_candidate" else "REVIEW"

    summary = {
        "phase": PHASE,
        "status": status,
        "run_id": run_id,
        "default_top_n": DEFAULT_TOP_N,
        "max_top_n": MAX_TOP_N,
        "phases_audited": EXPECTED_PHASES,
        "readiness": readiness["readiness"],
        "blockers_count": len(readiness["blockers"]),
        "warnings_count": len(readiness["warnings"]),
        "recommendation": readiness["recommendation"],
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "pipeline_recalculated": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": False,
        "next": "v0.8 release candidate freeze package",
    }

    audit = {
        "phase": PHASE,
        "status": status,
        "run_id": run_id,
        "phase_status": phase_rows,
        "key_outputs": output_records,
        "readiness": readiness,
        "controls": {
            "openai_called": False,
            "api_called": False,
            "yfinance_called": False,
            "pipeline_recalculated": False,
            "app_modified": False,
            "filters_modified": False,
            "release_modified": False,
        },
    }

    write_json(out / "phase8j_v08_candidate_audit_summary.json", summary)
    write_json(out / "phase8j_v08_candidate_audit.json", audit)
    write_json(out / "phase8j_v08_candidate_readiness_decision.json", readiness)
    write_phase_csv(out / "phase8j_phase_status_matrix.csv", phase_rows)
    write_outputs_csv(out / "phase8j_key_outputs_manifest.csv", output_records)
    write_report(out / "phase8j_v08_candidate_audit_report.md", summary, phase_rows, readiness)

    print("Scout Finance — Phase 8J AI Memo Integration Readiness and v0.8 Candidate Audit")
    print("=" * 92)
    print()
    print("v0.8 candidate audit")
    print("-" * 92)
    print(f"Status: {status}")
    print(f"Readiness: {readiness['readiness']}")
    print(f"Phases audited: {', '.join(EXPECTED_PHASES)}")
    print(f"Blockers: {len(readiness['blockers'])}")
    print(f"Warnings: {len(readiness['warnings'])}")
    print(f"Recommendation: {readiness['recommendation']}")
    print(f"OpenAI called: False")
    print(f"API called: False")
    print(f"yfinance called: False")
    print(f"Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 8J v0.8 candidate audit is complete.")


if __name__ == "__main__":
    main()
