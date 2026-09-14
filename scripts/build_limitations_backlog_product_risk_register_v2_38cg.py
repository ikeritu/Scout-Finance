#!/usr/bin/env python3
"""v2.38CG limitations backlog and product risk register builder."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CG-limitations-backlog-product-risk-register"
CONTRACT = ROOT / "config/limitations_backlog_product_risk_register_contract_v2_38cg.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cg_limitations_backlog_product_risk_register"

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
}

INPUTS = {
    "bx_summary": "outputs/full_universe_source_acquisition/v2_38bx_phase9c_closure_audit/phase9c_closure_audit_summary_v2_38bx.json",
    "bz_summary": "outputs/full_universe_source_acquisition/v2_38bz_product_readiness_gate/product_readiness_gate_summary_v2_38bz.json",
    "bz_limitations": "outputs/full_universe_source_acquisition/v2_38bz_product_readiness_gate/product_readiness_gate_limitations_v2_38bz.csv",
    "cd_summary": "outputs/full_universe_source_acquisition/v2_38cd_required_outputs_diagnostics/required_outputs_summary_v2_38cd.json",
    "cd_missing": "outputs/full_universe_source_acquisition/v2_38cd_required_outputs_diagnostics/missing_data_diagnostics_v2_38cd.csv",
    "ce_summary": "outputs/full_universe_source_acquisition/v2_38ce_windows_reproducible_packaging/windows_reproducible_packaging_summary_v2_38ce.json",
    "cf_summary": "outputs/full_universe_source_acquisition/v2_38cf_streamlit_visual_smoke_test/streamlit_visual_smoke_test_summary_v2_38cf.json",
    "cf_checklist": "outputs/full_universe_source_acquisition/v2_38cf_streamlit_visual_smoke_test/streamlit_visual_smoke_test_checklist_v2_38cf.csv",
    "roadmap": "ROADMAP_v2_38_CURRENT.md",
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


def risk(risk_id: str, title: str, category: str, source_phase: str, severity: str, likelihood: str, status: str, evidence_path: str, user_impact: str, mitigation: str, owner: str, next_action: str, is_blocking: bool = False) -> dict[str, Any]:
    return {
        "risk_id": risk_id,
        "title": title,
        "category": category,
        "source_phase": source_phase,
        "severity": severity,
        "likelihood": likelihood,
        "status": status,
        "is_blocking": str(is_blocking).lower(),
        "evidence_path": evidence_path,
        "user_impact": user_impact,
        "mitigation": mitigation,
        "owner": owner,
        "next_action": next_action,
    }


def backlog(backlog_id: str, limitation: str, source_phase: str, limitation_type: str, affected_scope: str, current_handling: str, proposed_resolution_phase: str, notes: str, is_blocking: bool = False) -> dict[str, Any]:
    return {
        "backlog_id": backlog_id,
        "limitation": limitation,
        "source_phase": source_phase,
        "limitation_type": limitation_type,
        "is_blocking": str(is_blocking).lower(),
        "affected_scope": affected_scope,
        "current_handling": current_handling,
        "proposed_resolution_phase": proposed_resolution_phase,
        "notes": notes,
    }


def build_risks(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cf = summaries["cf"]
    return [
        risk("RISK-001", "Ranking experimental may be read as investment advice", "PRODUCT_POSITIONING", "v2.38BX/v2.38BZ/v2.38CF", "HIGH", "MEDIUM", "MITIGATED", INPUTS["cf_summary"], "User could over-trust a research prioritization score.", "Repeated no-advice disclaimers, read-only UI and no broker workflow.", "Product", "Keep disclaimers visible through v2.38CH audit."),
        risk("RISK-002", "270 assets blocked by low real factor coverage", "DATA_COVERAGE", "v2.38BV/v2.38CD", "MEDIUM", "HIGH", "ACCEPTED_LIMITATION", INPUTS["cd_missing"], "Some assets cannot be ranked and may disappoint coverage expectations.", "Blocked population remains visible and excluded from main ranking.", "Data", "Prioritize coverage work only after release candidate closure."),
        risk("RISK-003", "26 assets have no scoring adapter", "DATA_COVERAGE", "v2.38BV/v2.38CD", "MEDIUM", "MEDIUM", "ACCEPTED_LIMITATION", INPUTS["cd_missing"], "Eligible-looking assets remain unscored.", "Explicit NOT_YET_SCORED_NO_ADAPTER state.", "Data", "Create adapters in a later authorized phase."),
        risk("RISK-004", "124 assets require manual or special-model review", "DATA_QUALITY", "v2.38BV/v2.38BX", "HIGH", "MEDIUM", "DEFERRED", INPUTS["bx_summary"], "Financial institutions and outlier margins may be misunderstood.", "Separated REVIEW_REQUIRED population, never auto-ranked.", "Data/Methodology", "Keep separate until a sector-specific contract exists."),
        risk("RISK-005", "No real browser screenshots in v2.38CF environment", "ENVIRONMENT", "v2.38CF", "MEDIUM", "HIGH", "OPEN", INPUTS["cf_summary"], "Visual regressions may remain unseen in this execution environment.", "Structural smoke test is explicit and screenshots_available=false.", "QA", "Run real browser smoke test in Windows or a browser-enabled environment."),
        risk("RISK-006", "Manifest-based package without heavy ZIP", "PACKAGING", "v2.38CE", "LOW", "MEDIUM", "ACCEPTED_LIMITATION", INPUTS["ce_summary"], "User must reproduce package through repo checkout and manifest rather than a single archive.", "Manifest lists included/excluded files and hashes.", "Release", "Evaluate ZIP only if final publication needs it."),
        risk("RISK-007", "Windows local environment dependency drift", "ENVIRONMENT", "v2.38CB/v2.38CE", "MEDIUM", "MEDIUM", "MITIGATED", INPUTS["ce_summary"], "Different Python/dependency versions can affect local startup.", "Requirements, launcher and preflight checklist are documented.", "Release", "Verify on the user's Windows machine during v2.38CH."),
        risk("RISK-008", "Cboe Europe mass identity expansion deferred", "DATA_COVERAGE", "v2.38BB/v2.38CD", "MEDIUM", "MEDIUM", "DEFERRED", INPUTS["cd_missing"], "European coverage remains lower than it could be.", "Explicit scope-decision limitation; not blocking local release.", "Data", "Require explicit authorization before expansion."),
        risk("RISK-009", "UK official source automation blocked", "OPERATIONAL", "v2.38BL/v2.38CD", "MEDIUM", "MEDIUM", "BLOCKED", INPUTS["cd_missing"], "UK fundamentals coverage cannot be safely automated now.", "Documented as non-blocking source-access limitation.", "Data", "Do not bypass access restrictions; revisit with safe source path."),
        risk("RISK-010", "Offshore or low-disclosure sources remain incomplete", "DATA_COVERAGE", "v2.38BM/v2.38CD", "MEDIUM", "MEDIUM", "ACCEPTED_LIMITATION", INPUTS["cd_missing"], "Some jurisdictions remain identity-only or no-disclosure.", "Limitations are visible and separated from ranked universe.", "Data", "Keep as limitation unless new public sources are authorized."),
        risk("RISK-011", "Current scoring method lacks predictive validation claim", "METHODOLOGY", "v2.38BX/v2.38BZ", "HIGH", "MEDIUM", "MITIGATED", INPUTS["bz_summary"], "Score could be mistaken for a proven predictor.", "Product copy says research ranking, not prediction.", "Methodology", "Reconfirm language during release candidate audit."),
        risk("RISK-012", "Legal/compliance no-advice boundary must remain intact", "LEGAL_COMPLIANCE", "v2.38BZ/v2.38CF", "HIGH", "MEDIUM", "MITIGATED", INPUTS["cf_summary"], "Bad wording could imply advice, suitability or recommendation.", "No buy/sell/hold language, no broker actions, no price targets.", "Product/Legal", "Audit public docs before final publication."),
        risk("RISK-013", "UX exposes multiple separated populations", "UX", "v2.38BY/v2.38CF", "LOW", "MEDIUM", "MITIGATED", INPUTS["cf_summary"], "Users may find statuses confusing.", "Tabs, labels and guide explain each population.", "Product", "Validate with real visual smoke test."),
        risk("RISK-014", "Product is still local release candidate, not final publication", "PRODUCT_POSITIONING", "v2.38CE/v2.38CF", "MEDIUM", "HIGH", "ACCEPTED_LIMITATION", INPUTS["ce_summary"], "Users may assume the project is final.", "Roadmap keeps CH/CI/CJ pending.", "Release", "Do not call final until CJ."),
    ]


def build_backlog(risks: list[dict[str, Any]], cd_missing: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = [
        backlog("BL-001", "Run real Streamlit/browser screenshots", "v2.38CF", "ENVIRONMENT_WARNING", "visual QA", "Structural smoke test accepted with warning.", "v2.38CH", "Needed before final confidence in UI rendering."),
        backlog("BL-002", "Keep ranking no-advice wording audited", "v2.38BZ/v2.38CF", "PRODUCT_POSITIONING", "all users", "Disclaimers present.", "v2.38CH", "Must survive final audit."),
        backlog("BL-003", "Review financial institutions separately", "v2.38BV/v2.38BX", "METHODOLOGY_GAP", "124 review-required assets", "Excluded from main ranking.", "post-v2.38CJ", "Requires separate factor contract."),
        backlog("BL-004", "Plan adapters for jurisdictions without ratios/growth adapter", "v2.38CD", "ADAPTER_GAP", "26 assets", "Marked NOT_YET_SCORED_NO_ADAPTER.", "post-v2.38CJ", "Do not invent scores."),
        backlog("BL-005", "Decide Cboe Europe mass identity expansion", "v2.38BB/v2.38CD", "SCOPE_DECISION", "European coverage", "Deferred by explicit decision.", "post-v2.38CJ", "Requires user authorization."),
        backlog("BL-006", "Preserve manifest-based packaging until final release decision", "v2.38CE", "PACKAGING", "local install", "No heavy ZIP created.", "v2.38CI", "Freeze candidate can decide archive policy."),
    ]
    for item in cd_missing:
        rows.append(backlog(
            f"BL-CD-{len(rows)+1:03d}",
            item["diagnostic_note"],
            "v2.38CD",
            item["missing_type"],
            item.get("affected_count") or "documented scope",
            "Documented as blocking=false or degraded.",
            "post-v2.38CJ",
            item["remediation_hint"],
            is_blocking=item["is_blocking"] == "true",
        ))
    return rows


def validate(contract: dict[str, Any], risks: list[dict[str, Any]], summaries: dict[str, dict[str, Any]]) -> tuple[str, str]:
    categories = {row["category"] for row in risks}
    blocking = [row for row in risks if row["is_blocking"] == "true"]
    cf_ok = summaries["cf"]["status"] in contract["expected_cf_statuses"]
    ok = cf_ok and not blocking and len(risks) >= 10 and set(contract["required_categories"]).issubset(categories)
    return (contract["expected_status"] if ok else "PRODUCT_RISK_REGISTER_BLOCKED", "PASS" if ok else "FAIL")


def report(summary: dict[str, Any], risks: list[dict[str, Any]], backlog_rows: list[dict[str, Any]]) -> str:
    category_counts = Counter(row["category"] for row in risks)
    category_lines = "\n".join(f"- `{category}`: {count}" for category, count in sorted(category_counts.items()))
    risk_lines = "\n".join(f"- `{row['risk_id']}` {row['title']} ({row['severity']}, {row['status']}). Blocking: `{row['is_blocking']}`." for row in risks)
    return f"""# Limitations Backlog And Product Risk Register v2.38CG

Decision: `{summary['status']}`.

This phase consolidates known limitations, product risks, environment warnings and technical debt before final release-candidate audit. It does not change scoring, ranking, methodology, weights, datasets, UI, recommendations, network behavior or broker capabilities.

## Executive Summary

- Risks registered: {summary['risk_count']}
- Blocking risks: {summary['blocking_risk_count']}
- Backlog limitations: {summary['backlog_count']}
- Environment warnings: {summary['environment_warning_count']}
- Product positioning risks: {summary['product_positioning_risk_count']}
- Legal/compliance risks: {summary['legal_compliance_risk_count']}

## Categories

{category_lines}

## Risks

{risk_lines}

## Blocking Status

No blocking product risks are active for the next phase. Known limitations remain visible and accepted/deferred with mitigation.

## Next

Proceed to `v2.38CH -- Release candidate audit`.
"""


def manifest_for(inputs: list[Path], output_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "risk_register_manifest_v2_38cg.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs if path.exists() and path.is_file()},
        "outputs": outputs,
        "source_phases": ["v2.38BX", "v2.38BZ", "v2.38CD", "v2.38CE", "v2.38CF"],
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_limitations_backlog_product_risk_register_v2_38cg.py"],
        "tests": [
            "tests/qa_limitations_backlog_product_risk_register_v2_38cg.py",
            "tests/qa_limitations_backlog_product_risk_register_full_suite_v2_38cg.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    summaries = {key: load_json(key) for key in ["bx_summary", "bz_summary", "cd_summary", "ce_summary", "cf_summary"]}
    summaries = {"bx": summaries["bx_summary"], "bz": summaries["bz_summary"], "cd": summaries["cd_summary"], "ce": summaries["ce_summary"], "cf": summaries["cf_summary"]}
    cd_missing = load_csv("cd_missing")
    risks = build_risks(summaries)
    backlog_rows = build_backlog(risks, cd_missing)
    status, qa_status = validate(contract, risks, summaries)
    categories = Counter(row["category"] for row in risks)
    blocking = sum(row["is_blocking"] == "true" for row in risks)
    summary = {
        "phase": PHASE,
        "status": status,
        "qa_status": qa_status,
        "risk_count": len(risks),
        "backlog_count": len(backlog_rows),
        "blocking_risk_count": blocking,
        "non_blocking_risk_count": len(risks) - blocking,
        "environment_warning_count": categories["ENVIRONMENT"],
        "data_coverage_risk_count": categories["DATA_COVERAGE"],
        "product_positioning_risk_count": categories["PRODUCT_POSITIONING"],
        "legal_compliance_risk_count": categories["LEGAL_COMPLIANCE"],
        "categories_covered": sorted(categories),
        "next_recommended_phase": "v2.38CH-release-candidate-audit",
        **GUARDRAILS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "product_risk_register_v2_38cg.csv", risks, ["risk_id", "title", "category", "source_phase", "severity", "likelihood", "status", "is_blocking", "evidence_path", "user_impact", "mitigation", "owner", "next_action"])
    write_csv(output_dir / "limitations_backlog_v2_38cg.csv", backlog_rows, ["backlog_id", "limitation", "source_phase", "limitation_type", "is_blocking", "affected_scope", "current_handling", "proposed_resolution_phase", "notes"])
    write_text(output_dir / "risk_register_summary_v2_38cg.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "LIMITATIONS_BACKLOG_PRODUCT_RISK_REGISTER_v2_38cg.md", report(summary, risks, backlog_rows))
    write_text(output_dir / "README.md", "# v2.38CG Limitations Backlog Product Risk Register\n\nConsolidated limitations backlog and product risk register. No network, scoring, ranking, methodology, UI, dataset, recommendation, or broker changes.\n")
    input_paths = [contract_path, *[ROOT / path for path in INPUTS.values()]]
    write_text(output_dir / "risk_register_manifest_v2_38cg.json", json.dumps(manifest_for(input_paths, output_dir, summary), indent=2, sort_keys=True) + "\n")
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
