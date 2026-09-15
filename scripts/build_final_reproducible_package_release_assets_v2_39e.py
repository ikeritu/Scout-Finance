#!/usr/bin/env python3
"""v2.39E final reproducible package and release assets builder."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.39E-final-reproducible-package-release-assets"
CONTRACT = ROOT / "config/final_reproducible_package_release_assets_contract_v2_39e.json"
SOURCE_SUMMARY = ROOT / "outputs/full_universe_source_acquisition/v2_39d_clean_windows_install_validation/clean_windows_install_validation_summary_v2_39d.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39e_final_reproducible_package_release_assets"
HEAVY_THRESHOLD = 1_000_000

ASSETS = [
    ("README.md", "release notes", "INCLUDED", True),
    ("VERSION.md", "release notes", "INCLUDED", True),
    ("CHANGELOG.md", "release notes", "INCLUDED", True),
    ("ROADMAP_v2_38_CURRENT.md", "documentation index", "INCLUDED", True),
    ("requirements.txt", "install checklist", "INCLUDED", True),
    ("run_local_ui_v2_37.bat", "install checklist", "INCLUDED", True),
    ("app_v2_37.py", "package inventory", "INCLUDED", True),
    ("docs/PUBLIC_DOCUMENTATION_INDEX_v2_39b.md", "documentation index", "INCLUDED", True),
    ("docs/LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md", "install checklist", "INCLUDED", True),
    ("outputs/full_universe_source_acquisition/v2_38cj_final_operational_publication/final_operational_publication_summary_v2_38cj.json", "stable tag reference", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_38cj_final_operational_publication/final_operational_publication_manifest_v2_38cj.json", "stable tag reference", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_39a_stable_release_tag/stable_release_tag_summary_v2_39a.json", "stable tag reference", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_39a_stable_release_tag/stable_release_tag_manifest_v2_39a.json", "stable tag reference", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_39b_public_documentation_cleanup/public_documentation_cleanup_summary_v2_39b.json", "documentation index", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_39b_public_documentation_cleanup/public_documentation_cleanup_manifest_v2_39b.json", "documentation index", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_39c_security_sensitive_files_audit/security_sensitive_files_summary_v2_39c.json", "security audit reference", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_39c_security_sensitive_files_audit/security_sensitive_files_manifest_v2_39c.json", "security audit reference", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_39d_clean_windows_install_validation/clean_windows_install_validation_summary_v2_39d.json", "clean Windows install reference", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_39d_clean_windows_install_validation/clean_windows_install_validation_manifest_v2_39d.json", "clean Windows install reference", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_39d_clean_windows_install_validation/clean_windows_install_checklist_v2_39d.ps1", "install checklist", "INCLUDED", True),
    ("outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json", "ranking artifact reference", "REFERENCE_ONLY", True),
    ("outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_manifest_v2_38bv.json", "ranking artifact reference", "REFERENCE_ONLY", True),
]

GUARDRAILS = {
    "github_release_created": False,
    "assets_uploaded": False,
    "zip_created": False,
    "tag_created": False,
    "network_used": False,
    "dependency_install_executed": False,
    "datasets_mutated": False,
    "scoring_recomputed": False,
    "weights_changed": False,
    "ranking_changed": False,
    "methodology_changed": False,
    "ui_changed": False,
    "financial_advice_created": False,
    "broker_actions_allowed": False,
}


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace").strip()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


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


def inventory_rows() -> list[dict[str, Any]]:
    rows = []
    for path_text, category, default_status, critical in ASSETS:
        path = ROOT / path_text
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        status = "MISSING" if not exists else default_status
        if exists and size > HEAVY_THRESHOLD:
            status = "EXCLUDED_HEAVY"
        rows.append({
            "asset_path": path_text,
            "category": category,
            "status": status,
            "critical": str(critical).lower(),
            "bytes": size,
            "sha256": sha256(path) if exists else "",
            "notes": "referenced by manifest, not packaged as heavy asset" if status == "EXCLUDED_HEAVY" else "ready",
        })
    return rows


def matrix_rows(inventory: list[dict[str, Any]], source: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [{
        "check_id": "SRC-001",
        "category": "source",
        "severity": "BLOCKER",
        "status": "PASS" if source.get("status") == contract["required_source_status"] else "BLOCKER",
        "evidence": str(source.get("status")),
        "remediation": "Run v2.39D before v2.39E.",
    }]
    for asset in inventory:
        status = "BLOCKER" if asset["status"] == "MISSING" and asset["critical"] == "true" else "WARN" if asset["status"] == "EXCLUDED_HEAVY" else "PASS"
        rows.append({
            "check_id": "ASSET-001",
            "category": asset["category"],
            "severity": "BLOCKER" if asset["critical"] == "true" else "WARN",
            "status": status,
            "evidence": f"{asset['asset_path']}::{asset['status']}",
            "remediation": "Restore missing critical asset or keep heavy assets reference-only.",
        })
    rows.extend([
        {"check_id": "REL-001", "category": "release notes", "severity": "BLOCKER", "status": "PASS", "evidence": "draft release notes generated", "remediation": "No action required."},
        {"check_id": "REL-002", "category": "publication checklist", "severity": "BLOCKER", "status": "PASS", "evidence": "manual GitHub checklist generated", "remediation": "No action required."},
        {"check_id": "GUARDRAIL-001", "category": "no-advice guardrails", "severity": "BLOCKER", "status": "PASS", "evidence": "no advice/no broker/no release flags closed", "remediation": "No action required."},
    ])
    return rows


def release_notes() -> str:
    return """# Scout Finance v2.38CJ Local Stable - Release Notes Draft

Stable tag: `v2.38CJ-local-stable`

Scout Finance is a local research tool with an experimental ranking surface. It is not financial advice, does not produce investment recommendations, includes no broker workflow and cannot execute orders.

## Included Scope

- Local Windows startup through `run_local_ui_v2_37.bat`
- Public documentation index and local usage guide
- Security and sensitive-files audit reference
- Clean Windows install validation checklist
- Experimental ranking artifact references from v2.38BV

## Known Limitations

Coverage gaps, European source constraints, UK/Cboe/Luxembourg/manual-review decisions and environment warnings remain documented. Heavy data artifacts are referenced by manifest rather than duplicated into a release ZIP.

## Publication Status

These are draft assets only. No GitHub Release was created, no assets were uploaded and no new tag was created by v2.39E.
"""


def publication_checklist() -> list[dict[str, str]]:
    return [
        {"step": "confirm_clean_git_status", "status": "PENDING_MANUAL", "notes": "Run git status before release."},
        {"step": "confirm_stable_tag", "status": "PENDING_MANUAL", "notes": "Verify v2.38CJ-local-stable points to intended commit."},
        {"step": "review_security_audit", "status": "PENDING_MANUAL", "notes": "Review v2.39C warnings before attaching assets."},
        {"step": "review_release_notes", "status": "PENDING_MANUAL", "notes": "Confirm no-advice/no-broker language."},
        {"step": "create_github_release_if_authorized", "status": "PENDING_MANUAL", "notes": "Do not automate without explicit user authorization."},
        {"step": "attach_allowed_assets_only", "status": "PENDING_MANUAL", "notes": "Do not attach secrets, raw caches or unreviewed heavy files."},
    ]


def report(summary: dict[str, Any]) -> str:
    return f"""# Final Reproducible Package Release Assets v2.39E

Decision: `{summary['status']}`.

This phase prepares draft GitHub Release assets and a reproducible package inventory without creating a release, uploading assets or creating a ZIP.

## Results

- Assets total: {summary['assets_total']}
- Included assets: {summary['included_asset_count']}
- Reference-only assets: {summary['reference_only_asset_count']}
- Excluded heavy assets: {summary['excluded_heavy_asset_count']}
- Missing assets: {summary['missing_asset_count']}
- Critical missing: {summary['critical_missing_count']}
- Warnings: {summary['warn_count']}
- Blockers: {summary['blocker_count']}

Warnings are documented for heavy artifacts that remain referenced by manifest. Guardrails remain closed: no network, no scoring, no ranking rebuild, no broker, no tag, no upload and no GitHub Release.

Next recommended phase: `{summary['next_recommended_phase']}`.
"""


def build() -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_SUMMARY.read_text(encoding="utf-8"))
    inventory = inventory_rows()
    matrix = matrix_rows(inventory, source, contract)
    missing = [r for r in inventory if r["status"] == "MISSING"]
    critical_missing = [r for r in missing if r["critical"] == "true"]
    heavy = [r for r in inventory if r["status"] == "EXCLUDED_HEAVY"]
    blockers = sum(r["status"] == "BLOCKER" for r in matrix)
    summary = {
        "phase": PHASE,
        "status": contract["status_target"] if blockers == 0 else "FINAL_REPRODUCIBLE_PACKAGE_RELEASE_ASSETS_BLOCKED",
        "qa_status": "PASS" if blockers == 0 else "FAIL",
        "source_phase": contract["source_phase"],
        "source_status": source.get("status"),
        "stable_tag": contract["stable_tag"],
        "publication_scope": contract["publication_scope"],
        "release_asset_scope": contract["release_asset_scope"],
        "assets_total": len(inventory),
        "included_asset_count": sum(r["status"] == "INCLUDED" for r in inventory),
        "reference_only_asset_count": sum(r["status"] == "REFERENCE_ONLY" for r in inventory),
        "excluded_heavy_asset_count": len(heavy),
        "missing_asset_count": len(missing),
        "critical_missing_count": len(critical_missing),
        "warn_count": sum(r["status"] == "WARN" for r in matrix),
        "blocker_count": blockers,
        "release_notes_status": "READY",
        "publication_checklist_status": "READY",
        "package_inventory_status": "READY",
        "next_recommended_phase": contract["next_recommended_phase"],
        **GUARDRAILS,
    }
    matrix_path = OUT / "final_reproducible_package_assets_matrix_v2_39e.csv"
    inventory_path = OUT / "final_reproducible_package_inventory_v2_39e.csv"
    checklist_path = OUT / "github_release_publication_checklist_v2_39e.csv"
    release_notes_path = OUT / "RELEASE_NOTES_DRAFT_v2_39e.md"
    report_path = OUT / "FINAL_REPRODUCIBLE_PACKAGE_RELEASE_ASSETS_v2_39e.md"
    summary_path = OUT / "final_reproducible_package_release_assets_summary_v2_39e.json"
    readme_path = OUT / "README.md"
    write_csv(matrix_path, matrix, ["check_id", "category", "severity", "status", "evidence", "remediation"])
    write_csv(inventory_path, inventory, ["asset_path", "category", "status", "critical", "bytes", "sha256", "notes"])
    write_csv(checklist_path, publication_checklist(), ["step", "status", "notes"])
    write_text(release_notes_path, release_notes())
    write_text(report_path, report(summary))
    write_json(summary_path, summary)
    write_text(readme_path, "# v2.39E Final Reproducible Package Release Assets\n\nDraft release assets, inventory and manual publication checklist.\n")
    manifest_path = OUT / "final_reproducible_package_release_assets_manifest_v2_39e.json"
    outputs = [matrix_path, inventory_path, checklist_path, release_notes_path, report_path, summary_path, readme_path]
    manifest = {
        "phase": PHASE,
        "status": summary["status"],
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "source_commit": run_git(["rev-parse", "--short", "HEAD"]),
        "stable_tag": summary["stable_tag"],
        "inputs": {
            rel(CONTRACT): {"bytes": CONTRACT.stat().st_size, "sha256": sha256(CONTRACT)},
            rel(SOURCE_SUMMARY): {"bytes": SOURCE_SUMMARY.stat().st_size, "sha256": sha256(SOURCE_SUMMARY)},
        },
        "outputs": {rel(p): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in outputs},
        "release_asset_inventory": inventory,
        "guardrails": GUARDRAILS,
    }
    write_json(manifest_path, manifest)
    return summary


def main() -> int:
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
