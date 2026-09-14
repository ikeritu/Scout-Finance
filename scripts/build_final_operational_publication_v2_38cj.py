#!/usr/bin/env python3
"""v2.38CJ final operational publication handoff builder."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CJ-final-operational-publication"
CONTRACT = ROOT / "config/final_operational_publication_contract_v2_38cj.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cj_final_operational_publication"

CI_SUMMARY = ROOT / "outputs/full_universe_source_acquisition/v2_38ci_freeze_candidate_version/freeze_candidate_summary_v2_38ci.json"
CI_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38ci_freeze_candidate_version/freeze_candidate_matrix_v2_38ci.csv"
CI_TRACE = ROOT / "outputs/full_universe_source_acquisition/v2_38ci_freeze_candidate_version/freeze_candidate_traceability_v2_38ci.csv"
CI_MANIFEST = ROOT / "outputs/full_universe_source_acquisition/v2_38ci_freeze_candidate_version/freeze_candidate_manifest_v2_38ci.json"
CI_REPORT = ROOT / "outputs/full_universe_source_acquisition/v2_38ci_freeze_candidate_version/FREEZE_CANDIDATE_VERSION_v2_38ci.md"

INPUTS = {
    "operator_guide": ROOT / "outputs/full_universe_source_acquisition/v2_38ca_release_candidate_local/OPERATOR_GUIDE_LOCAL_v2_38ca.md",
    "user_guide": ROOT / "outputs/full_universe_source_acquisition/v2_38cc_user_guide_dummy_friendly/USER_GUIDE_DUMMY_FRIENDLY_v2_38cc.md",
    "windows_packaging": ROOT / "outputs/full_universe_source_acquisition/v2_38ce_windows_reproducible_packaging/windows_reproducible_packaging_summary_v2_38ce.json",
    "streamlit_smoke": ROOT / "outputs/full_universe_source_acquisition/v2_38cf_streamlit_visual_smoke_test/streamlit_visual_smoke_test_summary_v2_38cf.json",
    "risk_register": ROOT / "outputs/full_universe_source_acquisition/v2_38cg_limitations_backlog_product_risk_register/product_risk_register_v2_38cg.csv",
    "release_audit": ROOT / "outputs/full_universe_source_acquisition/v2_38ch_release_candidate_audit/release_candidate_audit_summary_v2_38ch.json",
}

GUARDRAILS = {
    "network_allowed": False,
    "network_used": False,
    "scoring_recomputed": False,
    "weights_changed": False,
    "ranking_changed": False,
    "methodology_changed": False,
    "datasets_mutated": False,
    "ui_changed": False,
    "financial_advice_created": False,
    "recommendations_created": False,
    "broker_actions_allowed": False,
    "final_publication_declared": True,
}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def handoff_row(check_id: str, category: str, item: str, expected: Any, actual: Any, evidence_path: Path, note: str = "") -> dict[str, Any]:
    ok = actual == expected
    return {
        "check_id": check_id,
        "category": category,
        "item": item,
        "expected": expected,
        "actual": actual,
        "status": "PASS" if ok else "FAIL",
        "evidence_path": rel(evidence_path),
        "note": "No action required." if ok else note,
    }


def checklist_rows() -> list[dict[str, Any]]:
    steps = [
        ("01", "Enter the local repository", "cd \"D:\\Proyectos\\Scout Finance\"", "Required"),
        ("02", "Confirm the branch", "git status on phase9b-global-enrichment-v2-38b", "Required"),
        ("03", "Install dependencies", "pip install -r requirements.txt", "Required when environment is new"),
        ("04", "Optionally run freeze QA", "python tests/qa_freeze_candidate_version_full_suite_v2_38ci.py", "Optional verification"),
        ("05", "Optionally run final handoff QA", "python tests/qa_final_operational_publication_v2_38cj.py", "Optional verification"),
        ("06", "Start the local app", "run_local_ui_v2_37.bat", "Required"),
        ("07", "Open Streamlit", "http://localhost:8501", "Required"),
        ("08", "Open Global experimental ranking", "Use the Ranking global experimental screen", "Required"),
        ("09", "Review limitations", "Read v2.38CG and v2.38CJ reports before interpretation", "Required"),
        ("10", "Export CSV when needed", "Use the filtered export as a research artifact only", "Optional"),
        ("11", "Keep scope clear", "Treat outputs as local research, not financial advice", "Required"),
        ("12", "Do not use broker workflows", "No automated trading or broker action is part of this release", "Required"),
    ]
    return [
        {"step_id": step_id, "operator_step": title, "command_or_action": action, "requirement_level": level, "status": "READY"}
        for step_id, title, action, level in steps
    ]


def build_matrix(contract: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        handoff_row("HANDOFF-001", "SOURCE_FREEZE", "freeze candidate summary exists", "true", str(CI_SUMMARY.exists()).lower(), CI_SUMMARY, "Run v2.38CI first."),
        handoff_row("HANDOFF-002", "SOURCE_FREEZE", "freeze status accepted", contract["required_source_status"], source.get("status"), CI_SUMMARY, "Freeze candidate must be locked."),
        handoff_row("HANDOFF-003", "SOURCE_FREEZE", "freeze qa status", "PASS", source.get("qa_status"), CI_SUMMARY, "Run v2.38CI QA."),
        handoff_row("HANDOFF-004", "SOURCE_FREEZE", "freeze failures", "0", str(source.get("fail_count")), CI_SUMMARY, "Resolve freeze failures."),
        handoff_row("HANDOFF-005", "SOURCE_FREEZE", "freeze warnings", "0", str(source.get("warn_count")), CI_SUMMARY, "Resolve freeze warnings."),
        handoff_row("HANDOFF-006", "SOURCE_FREEZE", "freeze blocking issues", "0", str(source.get("blocking_issue_count")), CI_SUMMARY, "Resolve freeze blockers."),
        handoff_row("HANDOFF-007", "MANIFEST", "freeze manifest available", "true", str(CI_MANIFEST.exists()).lower(), CI_MANIFEST, "Generate v2.38CI manifest."),
        handoff_row("HANDOFF-008", "TRACEABILITY", "freeze traceability available", "true", str(CI_TRACE.exists()).lower(), CI_TRACE, "Generate v2.38CI traceability."),
        handoff_row("HANDOFF-009", "LOCAL_GUIDE", "operator guide available", "true", str(INPUTS["operator_guide"].exists()).lower(), INPUTS["operator_guide"], "Run v2.38CA."),
        handoff_row("HANDOFF-010", "LOCAL_GUIDE", "dummy-friendly guide available", "true", str(INPUTS["user_guide"].exists()).lower(), INPUTS["user_guide"], "Run v2.38CC."),
        handoff_row("HANDOFF-011", "PACKAGING", "Windows packaging summary available", "true", str(INPUTS["windows_packaging"].exists()).lower(), INPUTS["windows_packaging"], "Run v2.38CE."),
        handoff_row("HANDOFF-012", "SMOKE_TEST", "Streamlit smoke evidence available", "true", str(INPUTS["streamlit_smoke"].exists()).lower(), INPUTS["streamlit_smoke"], "Run v2.38CF."),
        handoff_row("HANDOFF-013", "RISK_REGISTER", "risk register available", "true", str(INPUTS["risk_register"].exists()).lower(), INPUTS["risk_register"], "Run v2.38CG."),
        handoff_row("HANDOFF-014", "RELEASE_AUDIT", "release audit available", "true", str(INPUTS["release_audit"].exists()).lower(), INPUTS["release_audit"], "Run v2.38CH."),
        handoff_row("HANDOFF-015", "PUBLICATION_SCOPE", "publication scope", "local_research_tool_only", contract["publication_scope"], CONTRACT, "Scope must remain local research only."),
        handoff_row("HANDOFF-016", "CYCLE", "cycle status", "V2_38_LOCAL_CYCLE_CLOSED", contract["cycle_status"], CONTRACT, "Declare cycle closure."),
    ]
    for key, expected in contract["expected_ranking_counts"].items():
        rows.append(handoff_row(f"RANKING-{key}", "RANKING_COUNTS", key, str(expected), str(source.get(key)), CI_SUMMARY, "Frozen ranking count drift detected."))
    for key, expected in GUARDRAILS.items():
        actual = contract["guardrails"].get(key, source.get(key, expected))
        rows.append(handoff_row(f"GUARDRAIL-{key}", "GUARDRAILS", key, str(expected).lower(), str(actual).lower(), CONTRACT, f"Keep {key}={str(expected).lower()}."))
    return rows


def report(summary: dict[str, Any], checklist: list[dict[str, Any]]) -> str:
    checklist_text = "\n".join(
        f"- {row['step_id']}. {row['operator_step']}: `{row['command_or_action']}` ({row['requirement_level']})."
        for row in checklist
    )
    return f"""# Final Operational Publication v2.38CJ

Decision: `{summary['status']}`.

Cycle status: `{summary['cycle_status']}`.

Publication scope: herramienta local de investigacion (`{summary['publication_scope']}`).

This closes the local v2.38 cycle. The final publication is operational only inside the local/repository package. It is not financial advice, does not create recommendations, does not include a broker workflow, and does not create automated trading signals.

## Frozen Operational State

- Source phase: `v2.38CI-freeze-candidate-version`
- Source status: `{summary['source_status']}`
- Handoff checks: {summary['handoff_check_count']}
- Checklist steps: {summary['checklist_step_count']}
- Failures: {summary['fail_count']}
- Warnings: {summary['warn_count']}
- Blocking issues: {summary['blocking_issue_count']}
- Documented limitations preserved: {summary['documented_limitation_count']}

## Frozen Ranking Counts

- Total: {summary['ranking_total']}
- Main ranking: {summary['ranking_main_count']}
- Partial comparability: {summary['ranking_partial_count']}
- Review required: {summary['ranking_review_required_count']}
- Blocked: {summary['ranking_blocked_count']}
- No adapter: {summary['ranking_no_adapter_count']}

## Final Operator Checklist

{checklist_text}

## Guardrails

No network, no scoring recomputation, no weight changes, no ranking changes, no methodology changes, no dataset mutation, no UI changes, no broker actions and no investment recommendations are introduced by this phase.

Next decision: `POST_V2_38_DECISION`.
"""


def manifest_for(input_paths: list[Path], output_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "final_operational_publication_manifest_v2_38cj.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "cycle_status": summary["cycle_status"],
        "publication_scope": summary["publication_scope"],
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in input_paths if path.exists() and path.is_file()},
        "outputs": outputs,
        "guardrails": GUARDRAILS,
        "next_recommended_phase": summary["next_recommended_phase"],
        "completion_marker": summary["completion_marker"],
        "scripts": ["scripts/build_final_operational_publication_v2_38cj.py"],
        "tests": [
            "tests/qa_final_operational_publication_v2_38cj.py",
            "tests/qa_final_operational_publication_full_suite_v2_38cj.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_json(contract_path)
    source = load_json(CI_SUMMARY)
    matrix = build_matrix(contract, source)
    checklist = checklist_rows()
    fail_count = sum(row["status"] == "FAIL" for row in matrix)
    warn_count = 0
    status = contract["target_status"] if fail_count == 0 else "FINAL_OPERATIONAL_PUBLICATION_BLOCKED"
    summary = {
        "phase": PHASE,
        "source_phase": contract["source_phase"],
        "source_status": source.get("status"),
        "status": status,
        "cycle_status": contract["cycle_status"],
        "publication_scope": contract["publication_scope"],
        "completion_marker": contract["completion_marker"],
        "qa_status": "PASS" if status == contract["target_status"] else "FAIL",
        "handoff_check_count": len(matrix),
        "checklist_step_count": len(checklist),
        "fail_count": fail_count,
        "warn_count": warn_count,
        "blocking_issue_count": fail_count,
        "documented_limitation_count": source.get("documented_limitation_count"),
        "ranking_total": source.get("ranking_total"),
        "ranking_main_count": source.get("ranking_main_count"),
        "ranking_partial_count": source.get("ranking_partial_count"),
        "ranking_review_required_count": source.get("ranking_review_required_count"),
        "ranking_blocked_count": source.get("ranking_blocked_count"),
        "ranking_no_adapter_count": source.get("ranking_no_adapter_count"),
        "next_recommended_phase": contract["next_recommended_phase"],
        **GUARDRAILS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "final_handoff_matrix_v2_38cj.csv", matrix, ["check_id", "category", "item", "expected", "actual", "status", "evidence_path", "note"])
    write_csv(output_dir / "final_operational_checklist_v2_38cj.csv", checklist, ["step_id", "operator_step", "command_or_action", "requirement_level", "status"])
    write_text(output_dir / "final_operational_publication_summary_v2_38cj.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "FINAL_OPERATIONAL_PUBLICATION_v2_38cj.md", report(summary, checklist))
    write_text(output_dir / "README.md", "# v2.38CJ Final Operational Publication\n\nFinal local operational handoff for the v2.38 cycle. The package is a local research tool with documented limitations, no financial advice, no recommendations and no broker workflow.\n")
    input_paths = [contract_path, CI_SUMMARY, CI_MATRIX, CI_TRACE, CI_MANIFEST, CI_REPORT, *INPUTS.values()]
    write_text(output_dir / "final_operational_publication_manifest_v2_38cj.json", json.dumps(manifest_for(input_paths, output_dir, summary), indent=2, sort_keys=True) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.contract, args.output_dir), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
