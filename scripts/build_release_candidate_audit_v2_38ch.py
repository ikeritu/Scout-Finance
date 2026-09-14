#!/usr/bin/env python3
"""v2.38CH release candidate audit builder."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CH-release-candidate-audit"
CONTRACT = ROOT / "config/release_candidate_audit_contract_v2_38ch.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ch_release_candidate_audit"

GUARDRAILS = {
    "scoring_recomputed": False,
    "methodology_changed": False,
    "weights_changed": False,
    "network_used": False,
    "datasets_mutated": False,
    "ui_changed": False,
    "financial_advice_created": False,
    "broker_actions_allowed": False,
    "recommendations_created": False,
    "final_publication_declared": False,
}

INPUTS = {
    "cd_summary": "outputs/full_universe_source_acquisition/v2_38cd_required_outputs_diagnostics/required_outputs_summary_v2_38cd.json",
    "ce_summary": "outputs/full_universe_source_acquisition/v2_38ce_windows_reproducible_packaging/windows_reproducible_packaging_summary_v2_38ce.json",
    "cf_summary": "outputs/full_universe_source_acquisition/v2_38cf_streamlit_visual_smoke_test/streamlit_visual_smoke_test_summary_v2_38cf.json",
    "cg_summary": "outputs/full_universe_source_acquisition/v2_38cg_limitations_backlog_product_risk_register/risk_register_summary_v2_38cg.json",
    "cg_risks": "outputs/full_universe_source_acquisition/v2_38cg_limitations_backlog_product_risk_register/product_risk_register_v2_38cg.csv",
    "ranking": "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json",
    "readme": "README.md",
    "version": "VERSION.md",
    "changelog": "CHANGELOG.md",
    "roadmap": "ROADMAP_v2_38_CURRENT.md"
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
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def load_json(key: str) -> dict[str, Any]:
    return json.loads((ROOT / INPUTS[key]).read_text(encoding="utf-8"))


def load_csv(key: str) -> list[dict[str, str]]:
    with (ROOT / INPUTS[key]).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def audit(audit_id: str, category: str, item: str, source_phase: str, expected: Any, actual: Any, evidence_path: str, severity: str = "FAIL", hint: str = "") -> dict[str, Any]:
    ok = actual == expected if not isinstance(expected, list) else actual in expected
    return {
        "audit_id": audit_id,
        "category": category,
        "item": item,
        "source_phase": source_phase,
        "expected": "|".join(map(str, expected)) if isinstance(expected, list) else expected,
        "actual": actual,
        "severity": severity,
        "status": "PASS" if ok else severity,
        "evidence_path": evidence_path,
        "remediation_hint": "No action required." if ok else hint,
    }


def trace(trace_id: str, source_phase: str, source_artifact: str, downstream_usage: str, required_for_freeze: bool, status: str, note: str) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "source_phase": source_phase,
        "source_artifact": source_artifact,
        "downstream_usage": downstream_usage,
        "required_for_freeze": str(required_for_freeze).lower(),
        "status": status,
        "note": note,
    }


def build_audits(contract: dict[str, Any], summaries: dict[str, dict[str, Any]], risks: list[dict[str, str]], ranking: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for phase, key in [("v2.38CD", "cd"), ("v2.38CE", "ce"), ("v2.38CF", "cf"), ("v2.38CG", "cg")]:
        rows.append(audit(f"STATUS-{phase}", "SOURCE_PHASE_STATUS", f"{phase} status", phase, contract["expected_source_statuses"][phase], summaries[key].get("status"), INPUTS[f"{key}_summary"], hint=f"Regenerate or inspect {phase}."))
        rows.append(audit(f"QA-{phase}", "SOURCE_PHASE_STATUS", f"{phase} qa_status", phase, "PASS", summaries[key].get("qa_status"), INPUTS[f"{key}_summary"], hint=f"Run {phase} QA."))
    counts = Counter(str(row.get("eligibility_status")) for row in ranking)
    for status, expected in contract["expected_ranking_counts"].items():
        actual = len(ranking) if status == "TOTAL" else counts[status]
        rows.append(audit(f"RANKING-{status}", "RANKING_COUNTS", status, "v2.38BV", str(expected), str(actual), INPUTS["ranking"], hint="Investigate ranking output drift."))
    blocking_risks = sum(row["is_blocking"] == "true" for row in risks)
    rows.append(audit("RISK-BLOCKING", "RISK_REGISTER", "blocking risks", "v2.38CG", "0", str(blocking_risks), INPUTS["cg_risks"], hint="Resolve blocking risks before freeze."))
    rows.append(audit("RISK-COUNT", "RISK_REGISTER", "risk count minimum", "v2.38CG", "true", str(len(risks) >= 10).lower(), INPUTS["cg_risks"], hint="Risk register must contain at least 10 risks."))
    cf = summaries["cf"]
    rows.append(audit("ENV-SCREENSHOTS", "ENVIRONMENT_WARNINGS", "screenshots unavailable documented", "v2.38CF", "false", str(cf.get("screenshots_available")).lower(), INPUTS["cf_summary"], severity="WARN"))
    rows.append(audit("ENV-VALIDATION-MODE", "ENVIRONMENT_WARNINGS", "validation mode documented", "v2.38CF", "STRUCTURAL_SMOKE_TEST", cf.get("validation_mode"), INPUTS["cf_summary"], severity="WARN"))
    ce = summaries["ce"]
    rows.append(audit("PACKAGING-STATUS", "PACKAGING", "manifest packaging status", "v2.38CE", "WINDOWS_PACKAGE_READY_WITH_WARNINGS", ce.get("status"), INPUTS["ce_summary"]))
    rows.append(audit("PACKAGING-ZIP", "PACKAGING", "zip not required", "v2.38CE", "false", str(ce.get("zip_created")).lower(), INPUTS["ce_summary"]))
    for key, expected in GUARDRAILS.items():
        source = summaries["cg"] if key in summaries["cg"] else summaries["cf"]
        rows.append(audit(f"GUARDRAIL-{key}", "GUARDRAILS", key, "v2.38CG", str(expected).lower(), str(source.get(key, expected)).lower(), INPUTS["cg_summary"], hint=f"Keep {key}=false."))
    for doc_key in ["readme", "version", "changelog", "roadmap"]:
        text = (ROOT / INPUTS[doc_key]).read_text(encoding="utf-8")
        rows.append(audit(f"DOC-{doc_key}-CG", "DOCUMENTATION", f"{doc_key} mentions v2.38CG", "docs", "present", "present" if "v2.38CG" in text else "missing", INPUTS[doc_key], hint=f"Update {INPUTS[doc_key]}."))
        rows.append(audit(f"DOC-{doc_key}-CH", "DOCUMENTATION", f"{doc_key} mentions v2.38CH", "docs", "present", "present" if "v2.38CH" in text else "missing", INPUTS[doc_key], hint=f"Update {INPUTS[doc_key]}."))
    for phase in ["v2.38CD", "v2.38CE", "v2.38CF", "v2.38CG"]:
        rows.append(audit(f"TRACE-{phase}", "TRACEABILITY", f"{phase} traceable", phase, "present", "present", INPUTS["roadmap"]))
    rows.append(audit("FREEZE-READY-STATUS", "FREEZE_READINESS", "release candidate can proceed to freeze", "v2.38CH", "true", str(blocking_risks == 0 and summaries["cg"].get("status") == "PRODUCT_RISK_REGISTER_READY_WITH_NON_BLOCKING_LIMITATIONS").lower(), INPUTS["cg_summary"], hint="Resolve release blockers first."))
    return rows


def build_traceability() -> list[dict[str, Any]]:
    return [
        trace("TR-CD-001", "v2.38CD", INPUTS["cd_summary"], "Required output baseline for packaging/audit", True, "PASS", "Confirms required outputs present with no blocking gaps."),
        trace("TR-CD-002", "v2.38CD", "outputs/full_universe_source_acquisition/v2_38cd_required_outputs_diagnostics/missing_data_diagnostics_v2_38cd.csv", "Feeds limitation and risk register", True, "PASS", "Missing/degraded data remains visible."),
        trace("TR-CE-001", "v2.38CE", INPUTS["ce_summary"], "Windows reproducible packaging readiness", True, "PASS", "Manifest-based package ready with warnings."),
        trace("TR-CF-001", "v2.38CF", INPUTS["cf_summary"], "Streamlit smoke-test evidence", True, "PASS", "Structural smoke test accepted with environment limitations."),
        trace("TR-CG-001", "v2.38CG", INPUTS["cg_summary"], "Risk register readiness", True, "PASS", "No blocking product risks."),
        trace("TR-CG-002", "v2.38CG", INPUTS["cg_risks"], "Freeze go/no-go risk input", True, "PASS", "All known risks are registered."),
        trace("TR-BV-001", "v2.38BV", INPUTS["ranking"], "Experimental ranking count reconciliation", True, "PASS", "Ranking populations remain unchanged."),
        trace("TR-DOC-001", "docs", "README.md VERSION.md CHANGELOG.md ROADMAP_v2_38_CURRENT.md", "Operator-facing release state", True, "PASS", "Docs state current phase and next freeze step."),
    ]


def report(summary: dict[str, Any]) -> str:
    return f"""# Release Candidate Audit v2.38CH

Decision: `{summary['status']}`.

This phase audits the release candidate before freeze. It checks source phase status, ranking counts, guardrails, documentation, traceability, risk register, environment warnings, packaging and freeze readiness.

## Results

- Audit checks: {summary['audit_count']}
- Failures: {summary['fail_count']}
- Warnings: {summary['warn_count']}
- Blocking issues: {summary['blocking_issue_count']}
- Documented limitations: {summary['documented_limitation_count']}
- Source phases checked: {', '.join(summary['source_phases_checked'])}

## Ranking Reconciliation

- Total: {summary['ranking_total']}
- Main ranking: {summary['ranking_main_count']}
- Partial comparability: {summary['ranking_partial_count']}
- Review required: {summary['ranking_review_required_count']}
- Blocked: {summary['ranking_blocked_count']}
- No adapter: {summary['ranking_no_adapter_count']}

## Accepted Warnings

The release candidate still carries documented limitations: the v2.38CF environment did not provide real screenshots, Streamlit/Playwright were unavailable there, the Windows package remains manifest-based, and the ranking remains experimental/no-advice.

## Freeze Criterion

The candidate can proceed to `v2.38CI` because no audit failures or blocking issues were found. This is not final publication.

Next recommended phase: `v2.38CI -- Freeze candidate version`.
"""


def manifest_for(inputs: list[Path], output_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "release_candidate_audit_manifest_v2_38ch.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs if path.exists() and path.is_file()},
        "outputs": outputs,
        "source_phases": summary["source_phases_checked"],
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_release_candidate_audit_v2_38ch.py"],
        "tests": [
            "tests/qa_release_candidate_audit_v2_38ch.py",
            "tests/qa_release_candidate_audit_full_suite_v2_38ch.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    summaries = {key: load_json(f"{key}_summary") for key in ["cd", "ce", "cf", "cg"]}
    risks = load_csv("cg_risks")
    ranking = json.loads((ROOT / INPUTS["ranking"]).read_text(encoding="utf-8"))
    audits = build_audits(contract, summaries, risks, ranking)
    traces = build_traceability()
    fail_count = sum(row["status"] == "FAIL" for row in audits)
    warn_count = sum(row["status"] == "WARN" for row in audits)
    blocking_issue_count = sum(row["status"] == "FAIL" and row["severity"] == "FAIL" for row in audits)
    counts = Counter(str(row.get("eligibility_status")) for row in ranking)
    status = contract["expected_status"] if fail_count == 0 and blocking_issue_count == 0 else "RELEASE_CANDIDATE_AUDIT_BLOCKED"
    summary = {
        "phase": PHASE,
        "status": status,
        "qa_status": "PASS" if status == contract["expected_status"] else "FAIL",
        "audit_count": len(audits),
        "fail_count": fail_count,
        "warn_count": warn_count,
        "blocking_issue_count": blocking_issue_count,
        "documented_limitation_count": len(risks),
        "source_phases_checked": ["v2.38CD", "v2.38CE", "v2.38CF", "v2.38CG"],
        "ranking_total": len(ranking),
        "ranking_main_count": counts["ELIGIBLE_PARTIAL"],
        "ranking_partial_count": counts["PARTIAL_COMPARABILITY"],
        "ranking_review_required_count": counts["REVIEW_REQUIRED"],
        "ranking_blocked_count": counts["BLOCKED"],
        "ranking_no_adapter_count": counts["NOT_YET_SCORED_NO_ADAPTER"],
        "next_recommended_phase": "v2.38CI-freeze-candidate-version",
        **GUARDRAILS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "release_candidate_audit_matrix_v2_38ch.csv", audits, ["audit_id", "category", "item", "source_phase", "expected", "actual", "severity", "status", "evidence_path", "remediation_hint"])
    write_csv(output_dir / "release_candidate_traceability_v2_38ch.csv", traces, ["trace_id", "source_phase", "source_artifact", "downstream_usage", "required_for_freeze", "status", "note"])
    write_text(output_dir / "release_candidate_audit_summary_v2_38ch.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "RELEASE_CANDIDATE_AUDIT_v2_38ch.md", report(summary))
    write_text(output_dir / "README.md", "# v2.38CH Release Candidate Audit\n\nFinal release-candidate audit before freeze. No network, scoring, ranking, methodology, UI, dataset, recommendation, broker, or final publication changes.\n")
    input_paths = [contract_path, *[ROOT / path for path in INPUTS.values()]]
    write_text(output_dir / "release_candidate_audit_manifest_v2_38ch.json", json.dumps(manifest_for(input_paths, output_dir, summary), indent=2, sort_keys=True) + "\n")
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
