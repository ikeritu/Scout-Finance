#!/usr/bin/env python3
"""v2.38CD required outputs checklist and missing-data diagnostics.

This phase is read-only against prior outputs. It inventories required files
for local use and documents missing/degraded data without network, scoring,
ranking, methodology, UI, or dataset changes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CD-required-outputs-diagnostics"
CONTRACT = ROOT / "config/required_outputs_diagnostics_contract_v2_38cd.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cd_required_outputs_diagnostics"

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

REQUIRED_OUTPUTS = [
    ("app_v2_37", "v2.37", "app_v2_37.py", "app", "local_app_startup", "python", True),
    ("windows_launcher", "v2.37", "run_local_ui_v2_37.bat", "launcher", "local_app_startup", "batch", True),
    ("requirements", "base", "requirements.txt", "dependency", "local_app_startup", "text", True),
    ("ui_requirements", "base", "requirements-ui-v2_28.txt", "dependency", "local_app_startup", "text", False),
    ("ranking_ui_module", "v2.38BW", "src/ui_v2_37/global_ranking.py", "ui", "experimental_ranking", "python", True),
    ("watchlists_module", "v2.37", "src/ui_v2_37/watchlists.py", "ui", "watchlists_exports", "python", True),
    ("ranking_results_json", "v2.38BV", "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json", "ranking", "experimental_ranking", "json", True),
    ("ranking_main_json", "v2.38BV", "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_main_v2_38bv.json", "ranking", "experimental_ranking", "json", True),
    ("ranking_csv", "v2.38BV", "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_v2_38bv.csv", "ranking", "experimental_ranking", "csv", True),
    ("ranking_manifest", "v2.38BV", "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_manifest_v2_38bv.json", "manifest", "experimental_ranking", "json", True),
    ("phase9c_audit_summary", "v2.38BX", "outputs/full_universe_source_acquisition/v2_38bx_phase9c_closure_audit/phase9c_closure_audit_summary_v2_38bx.json", "audit", "release_candidate_docs", "json", True),
    ("ranking_ux_summary", "v2.38BY", "outputs/full_universe_source_acquisition/v2_38by_ranking_ux_hardening/ranking_ux_hardening_summary_v2_38by.json", "audit", "release_candidate_docs", "json", True),
    ("product_readiness_summary", "v2.38BZ", "outputs/full_universe_source_acquisition/v2_38bz_product_readiness_gate/product_readiness_gate_summary_v2_38bz.json", "readiness", "release_candidate_docs", "json", True),
    ("release_candidate_summary", "v2.38CA", "outputs/full_universe_source_acquisition/v2_38ca_release_candidate_local/release_candidate_local_summary_v2_38ca.json", "release", "release_candidate_docs", "json", True),
    ("operator_guide", "v2.38CA", "outputs/full_universe_source_acquisition/v2_38ca_release_candidate_local/OPERATOR_GUIDE_LOCAL_v2_38ca.md", "docs", "release_candidate_docs", "markdown", True),
    ("startup_validation_summary", "v2.38CB", "outputs/full_universe_source_acquisition/v2_38cb_local_startup_validation/local_startup_validation_summary_v2_38cb.json", "startup", "local_app_startup", "json", True),
    ("startup_troubleshooting", "v2.38CB", "outputs/full_universe_source_acquisition/v2_38cb_local_startup_validation/LOCAL_STARTUP_TROUBLESHOOTING_v2_38cb.md", "docs", "local_app_startup", "markdown", True),
    ("user_guide_summary", "v2.38CC", "outputs/full_universe_source_acquisition/v2_38cc_user_guide_dummy_friendly/user_guide_dummy_friendly_summary_v2_38cc.json", "docs", "release_candidate_docs", "json", True),
    ("user_guide", "v2.38CC", "outputs/full_universe_source_acquisition/v2_38cc_user_guide_dummy_friendly/USER_GUIDE_DUMMY_FRIENDLY_v2_38cc.md", "docs", "release_candidate_docs", "markdown", True),
    ("user_quick_start", "v2.38CC", "outputs/full_universe_source_acquisition/v2_38cc_user_guide_dummy_friendly/USER_GUIDE_QUICK_START_v2_38cc.md", "docs", "release_candidate_docs", "markdown", True),
    ("user_faq", "v2.38CC", "outputs/full_universe_source_acquisition/v2_38cc_user_guide_dummy_friendly/USER_GUIDE_FAQ_v2_38cc.md", "docs", "release_candidate_docs", "markdown", True),
    ("country_breakdown", "diagnostic", "outputs/full_universe_source_acquisition/country_breakdown_by_country.csv", "diagnostic", "historical_auxiliary", "csv", False),
    ("currency_breakdown", "diagnostic", "outputs/full_universe_source_acquisition/country_breakdown_by_currency.csv", "diagnostic", "historical_auxiliary", "csv", False),
    ("source_provider_breakdown", "diagnostic", "outputs/full_universe_source_acquisition/country_breakdown_by_source_provider.csv", "diagnostic", "historical_auxiliary", "csv", False),
]

MISSING_DATA_TOPICS = [
    ("europe_ambiguous_identity_review", "coverage_gap", "outputs/full_universe_source_acquisition/v2_38bq_europe_cboe_ambiguous_disambiguation", "NON_BLOCKING_MISSING", False, "Ambiguous European Cboe identities still require manual review before promotion."),
    ("cboe_mass_identity_scaleup", "scope_decision", "outputs/full_universe_source_acquisition/v2_38bb_europe_cboe_secondary_identity_pilot", "NON_BLOCKING_MISSING", False, "Mass Cboe Europe identity expansion remains deferred pending explicit scope decision."),
    ("uk_official_source_blocked", "provider_access", "outputs/full_universe_source_acquisition/v2_38bl_europe_uk_fundamentals_source_research", "NON_BLOCKING_MISSING", False, "UK official source path is documented as blocked for safe automation."),
    ("jurisdictions_without_adapter", "adapter_gap", "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json", "DEGRADED", False, "Some assets remain NOT_YET_SCORED_NO_ADAPTER and are excluded from scored ranking populations."),
    ("low_coverage_blocked_assets", "coverage_gap", "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json", "DEGRADED", False, "Assets with insufficient real factor coverage remain BLOCKED and visible as limitations."),
]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
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


def row_count(path: Path, expected_type: str) -> str:
    if not path.exists() or path.is_dir():
        return ""
    if expected_type == "csv":
        with path.open(encoding="utf-8", newline="") as f:
            return str(max(0, sum(1 for _ in f) - 1))
    if expected_type == "json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return str(len(data))
        if isinstance(data, dict):
            for key in ("results", "rows", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    return str(len(value))
        return str(path.stat().st_size)
    return str(path.stat().st_size)


def output_status(path: Path, required: bool) -> str:
    if path.exists() and path.stat().st_size > 0:
        return "PRESENT"
    if required:
        return "BLOCKING_MISSING"
    return "OPTIONAL"


def build_output_rows() -> list[dict[str, Any]]:
    rows = []
    for output_id, phase, relative_path, category, required_for, expected_type, required in REQUIRED_OUTPUTS:
        path = ROOT / relative_path
        status = output_status(path, required)
        rows.append({
            "output_id": output_id,
            "phase": phase,
            "relative_path": relative_path,
            "category": category,
            "required_for": required_for,
            "expected_type": expected_type,
            "status": status,
            "is_blocking": str(status == "BLOCKING_MISSING").lower(),
            "file_exists": str(path.exists()).lower(),
            "row_count_or_size": row_count(path, expected_type),
            "diagnostic_note": "Required output is available." if status == "PRESENT" and required else ("Optional auxiliary output is available." if status == "PRESENT" else "Output is optional for local product use." if status == "OPTIONAL" else "Required output is missing and blocks local product use."),
            "remediation_hint": "No action required." if status in {"PRESENT", "OPTIONAL"} else f"Regenerate or restore {phase} before packaging the local release.",
        })
    return rows


def build_missing_rows(ranking_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("eligibility_status")) for row in ranking_results)
    rows = []
    for item_id, missing_type, evidence_path, status, is_blocking, note in MISSING_DATA_TOPICS:
        affected = ""
        if item_id == "jurisdictions_without_adapter":
            affected = str(counts["NOT_YET_SCORED_NO_ADAPTER"])
        elif item_id == "low_coverage_blocked_assets":
            affected = str(counts["BLOCKED"])
        rows.append({
            "diagnostic_id": item_id,
            "missing_type": missing_type,
            "evidence_path": evidence_path,
            "status": status,
            "is_blocking": str(is_blocking).lower(),
            "affected_count": affected,
            "diagnostic_note": note,
            "remediation_hint": "Keep documented as limitation unless a later phase explicitly authorizes source expansion, adapter work, or manual review closure.",
        })
    return rows


def previous_status_checks(contract: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "v2.38BZ": ROOT / "outputs/full_universe_source_acquisition/v2_38bz_product_readiness_gate/product_readiness_gate_summary_v2_38bz.json",
        "v2.38CA": ROOT / "outputs/full_universe_source_acquisition/v2_38ca_release_candidate_local/release_candidate_local_summary_v2_38ca.json",
        "v2.38CB": ROOT / "outputs/full_universe_source_acquisition/v2_38cb_local_startup_validation/local_startup_validation_summary_v2_38cb.json",
        "v2.38CC": ROOT / "outputs/full_universe_source_acquisition/v2_38cc_user_guide_dummy_friendly/user_guide_dummy_friendly_summary_v2_38cc.json",
    }
    checks = {}
    for phase, path in paths.items():
        actual = json.loads(path.read_text(encoding="utf-8")).get("status") if path.exists() else "MISSING"
        expected = contract["expected_previous_statuses"][phase]
        ok = actual in expected if isinstance(expected, list) else actual == expected
        checks[phase] = {"expected": expected, "actual": actual, "status": "PASS" if ok else "FAIL"}
    return checks


def report(summary: dict[str, Any], output_rows: list[dict[str, Any]], missing_rows: list[dict[str, Any]]) -> str:
    by_status = Counter(row["status"] for row in output_rows)
    missing_lines = "\n".join(
        f"- `{row['diagnostic_id']}`: {row['diagnostic_note']} Blocking: `{row['is_blocking']}`."
        for row in missing_rows
    )
    blocking = [row for row in output_rows if row["status"] == "BLOCKING_MISSING"]
    blocking_text = "No blocking required outputs are missing." if not blocking else "\n".join(f"- `{row['relative_path']}`" for row in blocking)
    return f"""# Required Outputs Diagnostics v2.38CD

Decision: `{summary['status']}`.

This phase inventories the files required to run Scout Finance locally and to display the real experimental global ranking. It does not call the network, recompute scoring, change methodology, update weights, mutate datasets, change the UI, create recommendations, or enable broker actions.

## Output Checklist

- Outputs checked: {summary['output_count']}
- Present: {by_status['PRESENT']}
- Optional: {by_status['OPTIONAL']}
- Blocking missing: {by_status['BLOCKING_MISSING']}

## Blocking Status

{blocking_text}

## Missing Or Degraded Data

{missing_lines}

## Local Decision

The local app and experimental ranking remain usable with warnings because required runtime, ranking, release-candidate, startup-validation and user-guide outputs are present. Known European coverage, provider and adapter gaps stay documented as non-blocking limitations.

Next recommended phase: `v2.38CE -- Windows reproducible local packaging`.
"""


def manifest_for(inputs: list[Path], output_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "manifest_v2_38cd.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs if path.exists() and path.is_file()},
        "outputs": outputs,
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_required_outputs_diagnostics_v2_38cd.py"],
        "tests": [
            "tests/qa_required_outputs_diagnostics_v2_38cd.py",
            "tests/qa_required_outputs_diagnostics_full_suite_v2_38cd.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    ranking_path = ROOT / "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json"
    ranking_results = json.loads(ranking_path.read_text(encoding="utf-8"))
    output_rows = build_output_rows()
    missing_rows = build_missing_rows(ranking_results)
    statuses = Counter(row["status"] for row in output_rows)
    blocking_missing = statuses["BLOCKING_MISSING"]
    previous = previous_status_checks(contract)
    previous_failures = sum(1 for check in previous.values() if check["status"] != "PASS")
    status = "LOCAL_APP_BLOCKED" if blocking_missing or previous_failures else contract["expected_status"]
    summary = {
        "phase": PHASE,
        "status": status,
        "qa_status": "PASS" if status == contract["expected_status"] else "FAIL",
        "output_count": len(output_rows),
        "missing_diagnostic_count": len(missing_rows),
        "present_count": statuses["PRESENT"],
        "optional_count": statuses["OPTIONAL"],
        "blocking_missing_count": blocking_missing,
        "degraded_data_count": sum(1 for row in missing_rows if row["status"] == "DEGRADED"),
        "non_blocking_missing_data_count": sum(1 for row in missing_rows if row["status"] == "NON_BLOCKING_MISSING"),
        "previous_phase_checks": previous,
        "decision": status,
        "next_recommended_phase": "v2.38CE-windows-reproducible-local-packaging",
        **GUARDRAILS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "required_outputs_checklist_v2_38cd.csv", output_rows, ["output_id", "phase", "relative_path", "category", "required_for", "expected_type", "status", "is_blocking", "file_exists", "row_count_or_size", "diagnostic_note", "remediation_hint"])
    write_csv(output_dir / "missing_data_diagnostics_v2_38cd.csv", missing_rows, ["diagnostic_id", "missing_type", "evidence_path", "status", "is_blocking", "affected_count", "diagnostic_note", "remediation_hint"])
    write_text(output_dir / "required_outputs_summary_v2_38cd.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "REQUIRED_OUTPUTS_DIAGNOSTICS_v2_38cd.md", report(summary, output_rows, missing_rows))
    write_text(output_dir / "README.md", "# v2.38CD Required Outputs Diagnostics\n\nRead-only checklist of required local outputs and missing-data diagnostics. No network, scoring, ranking, UI, recommendation, broker, or dataset changes.\n")
    inputs = [contract_path, ranking_path, *[ROOT / row[2] for row in REQUIRED_OUTPUTS]]
    write_text(output_dir / "manifest_v2_38cd.json", json.dumps(manifest_for(inputs, output_dir, summary), indent=2, sort_keys=True) + "\n")
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
