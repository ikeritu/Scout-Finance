#!/usr/bin/env python3
"""v2.38CI freeze candidate version builder."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CI-freeze-candidate-version"
CONTRACT = ROOT / "config/freeze_candidate_version_contract_v2_38ci.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ci_freeze_candidate_version"

SOURCE_SUMMARY = ROOT / "outputs/full_universe_source_acquisition/v2_38ch_release_candidate_audit/release_candidate_audit_summary_v2_38ch.json"
SOURCE_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38ch_release_candidate_audit/release_candidate_audit_matrix_v2_38ch.csv"
SOURCE_TRACE = ROOT / "outputs/full_universe_source_acquisition/v2_38ch_release_candidate_audit/release_candidate_traceability_v2_38ch.csv"
SOURCE_REPORT = ROOT / "outputs/full_universe_source_acquisition/v2_38ch_release_candidate_audit/RELEASE_CANDIDATE_AUDIT_v2_38ch.md"
SOURCE_MANIFEST = ROOT / "outputs/full_universe_source_acquisition/v2_38ch_release_candidate_audit/release_candidate_audit_manifest_v2_38ch.json"

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
    "final_publication_declared": False,
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


def freeze_row(freeze_id: str, category: str, item: str, expected: Any, actual: Any, evidence_path: Path, severity: str = "FAIL", note: str = "") -> dict[str, Any]:
    ok = actual == expected
    return {
        "freeze_id": freeze_id,
        "category": category,
        "item": item,
        "expected": expected,
        "actual": actual,
        "severity": severity,
        "status": "PASS" if ok else severity,
        "evidence_path": rel(evidence_path),
        "note": "No action required." if ok else note,
    }


def build_matrix(contract: dict[str, Any], source: dict[str, Any], audit_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = [
        freeze_row("FREEZE-001", "SOURCE_AUDIT", "source audit summary exists", "true", str(SOURCE_SUMMARY.exists()).lower(), SOURCE_SUMMARY, note="Run v2.38CH first."),
        freeze_row("FREEZE-002", "SOURCE_AUDIT", "source audit status accepted", contract["required_source_status"], source.get("status"), SOURCE_SUMMARY, note="v2.38CH must pass before freeze."),
        freeze_row("FREEZE-003", "SOURCE_AUDIT", "source qa status", "PASS", source.get("qa_status"), SOURCE_SUMMARY, note="Run v2.38CH QA."),
        freeze_row("FREEZE-004", "SOURCE_AUDIT", "source fail count", "0", str(source.get("fail_count")), SOURCE_SUMMARY, note="Resolve failed audit rows."),
        freeze_row("FREEZE-005", "SOURCE_AUDIT", "source warning count", "0", str(source.get("warn_count")), SOURCE_SUMMARY, note="Resolve warnings before freeze."),
        freeze_row("FREEZE-006", "SOURCE_AUDIT", "source blocking issue count", "0", str(source.get("blocking_issue_count")), SOURCE_SUMMARY, note="Resolve blocking issues before freeze."),
        freeze_row("FREEZE-007", "LIMITATIONS", "documented limitations preserved", "true", str(int(source.get("documented_limitation_count", 0)) > 0).lower(), SOURCE_SUMMARY, note="Freeze must preserve known limitations."),
        freeze_row("FREEZE-008", "TRACEABILITY", "source traceability exists", "true", str(SOURCE_TRACE.exists()).lower(), SOURCE_TRACE, note="v2.38CH traceability is required."),
        freeze_row("FREEZE-009", "TRACEABILITY", "source matrix exists", "true", str(SOURCE_MATRIX.exists()).lower(), SOURCE_MATRIX, note="v2.38CH matrix is required."),
        freeze_row("FREEZE-010", "REPORTING", "source report exists", "true", str(SOURCE_REPORT.exists()).lower(), SOURCE_REPORT, note="v2.38CH report is required."),
        freeze_row("FREEZE-011", "MANIFEST", "source manifest exists", "true", str(SOURCE_MANIFEST.exists()).lower(), SOURCE_MANIFEST, note="v2.38CH manifest is required."),
    ]
    for key, expected in contract["expected_ranking_counts"].items():
        rows.append(freeze_row(f"RANKING-{key}", "RANKING_COUNTS", key, str(expected), str(source.get(key)), SOURCE_SUMMARY, note="Ranking count drift detected."))
    for key, expected in GUARDRAILS.items():
        actual = source.get(key, expected)
        rows.append(freeze_row(f"GUARDRAIL-{key}", "GUARDRAILS", key, str(expected).lower(), str(actual).lower(), SOURCE_SUMMARY, note=f"Keep {key}=false."))
    categories = {row.get("category") for row in audit_rows}
    for category in ["SOURCE_PHASE_STATUS", "RANKING_COUNTS", "GUARDRAILS", "DOCUMENTATION", "TRACEABILITY", "RISK_REGISTER", "ENVIRONMENT_WARNINGS", "PACKAGING", "FREEZE_READINESS"]:
        rows.append(freeze_row(f"TRACE-CATEGORY-{category}", "SOURCE_COVERAGE", category, "present", "present" if category in categories else "missing", SOURCE_MATRIX, note="Source audit category missing."))
    rows.append(freeze_row("NEXT-001", "HANDOFF", "next phase declared", contract["next_recommended_phase"], contract.get("next_recommended_phase"), CONTRACT, note="Declare v2.38CJ handoff."))
    rows.append(freeze_row("PUBLICATION-001", "PUBLICATION", "final publication not declared", "false", str(source.get("final_publication_declared", False)).lower(), SOURCE_SUMMARY, note="Final publication belongs to v2.38CJ."))
    return rows


def build_traceability(contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    inputs = [
        ("v2.38CH", SOURCE_SUMMARY, "Freeze source state"),
        ("v2.38CH", SOURCE_MATRIX, "Freeze audit checks"),
        ("v2.38CH", SOURCE_TRACE, "Freeze traceability chain"),
        ("v2.38CH", SOURCE_REPORT, "Operator-readable audit evidence"),
        ("v2.38CH", SOURCE_MANIFEST, "Input hashes and source manifest"),
        ("v2.38CG", ROOT / "outputs/full_universe_source_acquisition/v2_38cg_limitations_backlog_product_risk_register/product_risk_register_v2_38cg.csv", "Documented limitations source"),
        ("v2.38CE", ROOT / "outputs/full_universe_source_acquisition/v2_38ce_windows_reproducible_packaging/windows_reproducible_packaging_summary_v2_38ce.json", "Packaging readiness source"),
        ("v2.38BV", ROOT / "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json", "Frozen experimental ranking population"),
    ]
    for index, (phase, path, usage) in enumerate(inputs, start=1):
        rows.append({
            "trace_id": f"CI-TR-{index:03d}",
            "source_phase": phase,
            "source_artifact": rel(path),
            "downstream_usage": usage,
            "required_for_freeze": str(phase in contract["allowed_input_phases"]).lower(),
            "status": "PASS" if path.exists() else "FAIL",
            "sha256": sha256(path) if path.exists() and path.is_file() else "",
        })
    return rows


def report(summary: dict[str, Any]) -> str:
    return f"""# Freeze Candidate Version v2.38CI

Decision: `{summary['status']}`.

This phase freezes the release candidate audited by `v2.38CH`. It does not publish the final product and does not alter ranking, scoring, methodology, weights, datasets, UI, broker workflows or financial-advice guardrails.

## Frozen State

- Source phase: `v2.38CH-release-candidate-audit`
- Source status: `{summary['source_status']}`
- Freeze checks: {summary['freeze_check_count']}
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

## Guardrails

All freeze guardrails remain closed: no network, no scoring recomputation, no weight change, no methodology change, no dataset mutation, no UI change, no recommendations, no financial advice, no broker action and no final publication.

Next recommended phase: `v2.38CJ-release-handoff`.
"""


def manifest_for(input_paths: list[Path], output_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "freeze_candidate_manifest_v2_38ci.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in input_paths if path.exists() and path.is_file()},
        "outputs": outputs,
        "guardrails": GUARDRAILS,
        "next_recommended_phase": summary["next_recommended_phase"],
        "scripts": ["scripts/build_freeze_candidate_version_v2_38ci.py"],
        "tests": [
            "tests/qa_freeze_candidate_version_v2_38ci.py",
            "tests/qa_freeze_candidate_version_full_suite_v2_38ci.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_json(contract_path)
    source = load_json(SOURCE_SUMMARY)
    audit_rows = load_csv(SOURCE_MATRIX)
    matrix = build_matrix(contract, source, audit_rows)
    traces = build_traceability(contract)
    fail_count = sum(row["status"] == "FAIL" for row in matrix + traces)
    warn_count = sum(row["status"] == "WARN" for row in matrix)
    blocking_issue_count = fail_count
    status = contract["target_status"] if fail_count == 0 and warn_count == 0 else "FREEZE_CANDIDATE_VERSION_BLOCKED"
    summary = {
        "phase": PHASE,
        "source_phase": contract["source_phase"],
        "source_status": source.get("status"),
        "status": status,
        "qa_status": "PASS" if status == contract["target_status"] else "FAIL",
        "freeze_check_count": len(matrix),
        "traceability_count": len(traces),
        "fail_count": fail_count,
        "warn_count": warn_count,
        "blocking_issue_count": blocking_issue_count,
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
    write_csv(output_dir / "freeze_candidate_matrix_v2_38ci.csv", matrix, ["freeze_id", "category", "item", "expected", "actual", "severity", "status", "evidence_path", "note"])
    write_csv(output_dir / "freeze_candidate_traceability_v2_38ci.csv", traces, ["trace_id", "source_phase", "source_artifact", "downstream_usage", "required_for_freeze", "status", "sha256"])
    write_text(output_dir / "freeze_candidate_summary_v2_38ci.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "FREEZE_CANDIDATE_VERSION_v2_38ci.md", report(summary))
    write_text(output_dir / "README.md", "# v2.38CI Freeze Candidate Version\n\nFormal release-candidate freeze over the v2.38CH audit. No network, scoring, ranking, methodology, UI, dataset, recommendation, broker, or final publication changes.\n")
    input_paths = [contract_path, SOURCE_SUMMARY, SOURCE_MATRIX, SOURCE_TRACE, SOURCE_REPORT, SOURCE_MANIFEST]
    write_text(output_dir / "freeze_candidate_manifest_v2_38ci.json", json.dumps(manifest_for(input_paths, output_dir, summary), indent=2, sort_keys=True) + "\n")
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
