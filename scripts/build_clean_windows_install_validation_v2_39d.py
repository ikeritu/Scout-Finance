#!/usr/bin/env python3
"""v2.39D clean Windows install validation builder."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.39D-clean-windows-install-validation"
CONTRACT = ROOT / "config/clean_windows_install_validation_contract_v2_39d.json"
SOURCE_SUMMARY = ROOT / "outputs/full_universe_source_acquisition/v2_39c_security_sensitive_files_audit/security_sensitive_files_summary_v2_39c.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39d_clean_windows_install_validation"

CRITICAL_FILES = [
    "requirements.txt",
    "run_local_ui_v2_37.bat",
    "app_v2_37.py",
    "README.md",
    "VERSION.md",
    "CHANGELOG.md",
    "ROADMAP_v2_38_CURRENT.md",
    "src/ui_v2_37/global_ranking.py",
]
REQUIRED_OUTPUTS = [
    "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json",
    "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_manifest_v2_38bv.json",
    "outputs/full_universe_source_acquisition/v2_39c_security_sensitive_files_audit/security_sensitive_files_summary_v2_39c.json",
]
GUARDRAILS = {
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
    "tag_created": False,
    "github_release_created": False,
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


def row(check_id: str, category: str, severity: str, status: str, item: str, evidence: str, remediation: str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "category": category,
        "severity": severity,
        "status": status,
        "item": item,
        "evidence": evidence,
        "remediation": remediation,
    }


def quoted_windows_paths_ok(text: str) -> bool:
    return 'cd "D:\\' in text or 'cd "C:\\' in text or "spaces or emoji must be wrapped in quotes" in text


def build_matrix(contract: dict[str, Any], source: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.append(row("SRC-001", "source", "BLOCKER", "PASS" if source.get("status") == contract["required_source_status"] else "BLOCKER", "v2.39C status", str(source.get("status")), "Run v2.39C first."))
    for file in CRITICAL_FILES:
        exists = (ROOT / file).is_file()
        rows.append(row("FILE-CRITICAL", "critical_files", "BLOCKER", "PASS" if exists else "BLOCKER", file, "present" if exists else "missing", "Restore the critical file."))
    for output in REQUIRED_OUTPUTS:
        exists = (ROOT / output).is_file()
        rows.append(row("OUTPUT-REQUIRED", "required_outputs", "BLOCKER", "PASS" if exists else "BLOCKER", output, "present" if exists else "missing", "Restore or regenerate the required output before clean install."))
    launcher = (ROOT / "run_local_ui_v2_37.bat").read_text(encoding="utf-8", errors="replace")
    readme = (ROOT / "README.md").read_text(encoding="utf-8", errors="replace")
    guide = (ROOT / "docs/LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md").read_text(encoding="utf-8", errors="replace")
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8", errors="replace")
    rows.extend([
        row("BAT-001", "Windows launcher", "BLOCKER", "PASS" if "streamlit run app_v2_37.py" in launcher else "BLOCKER", "run_local_ui_v2_37.bat", "streamlit entrypoint checked", "Keep launcher pointing to app_v2_37.py."),
        row("REQ-001", "dependency install command", "BLOCKER", "PASS" if "streamlit" in req.lower() else "BLOCKER", "requirements.txt", "streamlit dependency checked", "Add Streamlit to requirements."),
        row("DOC-001", "local usage docs", "BLOCKER", "PASS" if "local_research_tool_only" in readme else "BLOCKER", "README.md", "local scope checked", "Document local research scope."),
        row("DOC-002", "local path safety", "WARN", "PASS" if quoted_windows_paths_ok(guide) else "WARN", "docs/LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md", "quoted Windows path guidance checked", "Use quotes for Windows paths with spaces or emoji."),
        row("ENV-001", "environment variables", "WARN", "PASS" if ".env" not in launcher.lower() else "WARN", "run_local_ui_v2_37.bat", "basic launcher does not require .env", "Keep secrets optional for basic local launch."),
    ])
    for step in ["git clone", "cd", "py -m venv .venv", ".venv\\Scripts\\Activate.ps1", "python -m pip install --upgrade pip", "pip install -r requirements.txt", "python -m py_compile app_v2_37.py", "run_local_ui_v2_37.bat", "http://localhost:8501"]:
        rows.append(row("MANUAL-WINDOWS", "manual_windows_steps", "WARN", "WARN", step, "requires real Windows execution", "Run this command on a clean Windows checkout."))
    return rows


def checklist_ps1() -> str:
    return r'''# Scout Finance v2.39D - Clean Windows install validation checklist
# Run manually in PowerShell from a clean folder.

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/ikeritu/Scout-Finance.git"
$Branch = "phase9b-global-enrichment-v2-38b"
$Target = "$env:USERPROFILE\ScoutFinanceCleanInstall"

git clone --branch $Branch $RepoUrl $Target
cd "$Target"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m py_compile app_v2_37.py
python -m py_compile src\ui_v2_37\global_ranking.py
.\run_local_ui_v2_37.bat
# Open http://localhost:8501 and verify "Ranking global (experimental)" loads.
'''


def report(summary: dict[str, Any]) -> str:
    return f"""# Clean Windows Install Validation v2.39D

Decision: `{summary['status']}`.

This phase prepares a reproducible clean Windows install validation without installing dependencies or opening a browser from the builder.

## Results

- Target platform: {summary['target_platform']}
- Checks total: {summary['checks_total']}
- PASS: {summary['pass_count']}
- WARN: {summary['warn_count']}
- BLOCKER: {summary['blocker_count']}
- Critical files missing: {summary['critical_files_missing_count']}
- Required outputs missing: {summary['required_outputs_missing_count']}
- Manual Windows steps: {summary['manual_windows_steps_count']}
- Launcher status: `{summary['launcher_status']}`
- Requirements status: `{summary['requirements_status']}`
- Local usage docs status: `{summary['local_usage_docs_status']}`

Warnings are expected for steps that must be executed on a real Windows machine. No network, dependency installation, scoring, ranking rebuild, dataset mutation, UI change, broker action, tag creation or GitHub release was performed by this builder.

Next recommended phase: `{summary['next_recommended_phase']}`.
"""


def manifest(summary: dict[str, Any], outputs: list[Path]) -> dict[str, Any]:
    return {
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
        "outputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in outputs if path.exists()},
        "guardrails": GUARDRAILS,
    }


def build() -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_SUMMARY.read_text(encoding="utf-8"))
    rows = build_matrix(contract, source)
    blocker_count = sum(r["status"] == "BLOCKER" for r in rows)
    summary = {
        "phase": PHASE,
        "status": contract["status_target"] if blocker_count == 0 else "CLEAN_WINDOWS_INSTALL_VALIDATION_BLOCKED",
        "qa_status": "PASS" if blocker_count == 0 else "FAIL",
        "source_phase": contract["source_phase"],
        "source_status": source.get("status"),
        "stable_tag": contract["stable_tag"],
        "publication_scope": contract["publication_scope"],
        "target_platform": contract["target_platform"],
        "checks_total": len(rows),
        "pass_count": sum(r["status"] == "PASS" for r in rows),
        "warn_count": sum(r["status"] == "WARN" for r in rows),
        "blocker_count": blocker_count,
        "critical_files_present_count": sum((ROOT / f).is_file() for f in CRITICAL_FILES),
        "critical_files_missing_count": sum(not (ROOT / f).is_file() for f in CRITICAL_FILES),
        "manual_windows_steps_count": sum(r["category"] == "manual_windows_steps" for r in rows),
        "required_outputs_present_count": sum((ROOT / f).is_file() for f in REQUIRED_OUTPUTS),
        "required_outputs_missing_count": sum(not (ROOT / f).is_file() for f in REQUIRED_OUTPUTS),
        "launcher_status": "PASS" if any(r["check_id"] == "BAT-001" and r["status"] == "PASS" for r in rows) else "BLOCKER",
        "requirements_status": "PASS" if any(r["check_id"] == "REQ-001" and r["status"] == "PASS" for r in rows) else "BLOCKER",
        "local_usage_docs_status": "PASS" if any(r["check_id"] == "DOC-001" and r["status"] == "PASS" for r in rows) else "BLOCKER",
        "next_recommended_phase": contract["next_recommended_phase"],
        **GUARDRAILS,
    }
    matrix_path = OUT / "clean_windows_install_validation_matrix_v2_39d.csv"
    checklist_path = OUT / "clean_windows_install_checklist_v2_39d.ps1"
    summary_path = OUT / "clean_windows_install_validation_summary_v2_39d.json"
    report_path = OUT / "CLEAN_WINDOWS_INSTALL_VALIDATION_v2_39d.md"
    readme_path = OUT / "README.md"
    write_csv(matrix_path, rows, ["check_id", "category", "severity", "status", "item", "evidence", "remediation"])
    write_text(checklist_path, checklist_ps1())
    write_json(summary_path, summary)
    write_text(report_path, report(summary))
    write_text(readme_path, "# v2.39D Clean Windows Install Validation\n\nOffline readiness outputs and manual PowerShell checklist for clean Windows validation.\n")
    manifest_path = OUT / "clean_windows_install_validation_manifest_v2_39d.json"
    outputs = [matrix_path, checklist_path, summary_path, report_path, readme_path]
    write_json(manifest_path, manifest(summary, outputs))
    return summary


def main() -> int:
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
