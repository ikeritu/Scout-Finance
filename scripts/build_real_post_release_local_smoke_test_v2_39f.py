#!/usr/bin/env python3
"""v2.39F real post-release local smoke test builder."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import py_compile
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.39F-real-post-release-local-smoke-test"
CONTRACT = ROOT / "config/real_post_release_local_smoke_test_contract_v2_39f.json"
SOURCE_SUMMARY = ROOT / "outputs/full_universe_source_acquisition/v2_39e_final_reproducible_package_release_assets/final_reproducible_package_release_assets_summary_v2_39e.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39f_real_post_release_local_smoke_test"
RANKING_PATH = ROOT / "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json"

EXPECTED_COUNTS = {
    "ELIGIBLE_PARTIAL": 318,
    "PARTIAL_COMPARABILITY": 373,
    "REVIEW_REQUIRED": 124,
    "BLOCKED": 270,
    "NOT_YET_SCORED_NO_ADAPTER": 26,
}
REQUIRED_FILES = [
    "outputs/full_universe_source_acquisition/v2_39e_final_reproducible_package_release_assets/RELEASE_NOTES_DRAFT_v2_39e.md",
    "outputs/full_universe_source_acquisition/v2_39e_final_reproducible_package_release_assets/final_reproducible_package_inventory_v2_39e.csv",
    "outputs/full_universe_source_acquisition/v2_39d_clean_windows_install_validation/clean_windows_install_checklist_v2_39d.ps1",
    "run_local_ui_v2_37.bat",
    "app_v2_37.py",
    "src/ui_v2_37/global_ranking.py",
    "README.md",
    "VERSION.md",
    "CHANGELOG.md",
    "ROADMAP_v2_38_CURRENT.md",
]
COMPILE_FILES = ["app_v2_37.py", "src/ui_v2_37/global_ranking.py"]
GUARDRAILS = {
    "github_release_created": False,
    "assets_uploaded": False,
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


def add(rows: list[dict[str, Any]], check_id: str, category: str, severity: str, status: str, evidence: str, remediation: str) -> None:
    rows.append({
        "check_id": check_id,
        "category": category,
        "severity": severity,
        "status": status,
        "evidence": evidence,
        "remediation": remediation,
    })


def compile_checks(rows: list[dict[str, Any]]) -> int:
    fail_count = 0
    for item in COMPILE_FILES:
        try:
            py_compile.compile(str(ROOT / item), doraise=True)
            add(rows, "COMPILE-001", "app compile", "BLOCKER", "PASS", item, "No action required.")
        except py_compile.PyCompileError as exc:
            fail_count += 1
            add(rows, "COMPILE-001", "app compile", "BLOCKER", "BLOCKER", f"{item}: {exc}", "Fix Python syntax before release smoke.")
    return fail_count


def load_ranking_via_module(rows: list[dict[str, Any]]) -> tuple[bool, int, dict[str, int]]:
    spec = importlib.util.spec_from_file_location("global_ranking_v2_39f", ROOT / "src/ui_v2_37/global_ranking.py")
    if spec is None or spec.loader is None:
        add(rows, "RANKING-LOADER", "ranking loader", "BLOCKER", "BLOCKER", "module spec unavailable", "Fix global_ranking module.")
        return False, 0, {}
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    data = module.load_global_ranking(ROOT)
    if not data.available:
        add(rows, "RANKING-LOADER", "ranking loader", "BLOCKER", "BLOCKER", data.error, "Restore ranking artifact.")
        return False, 0, {}
    counts = Counter(row.get("eligibility_status") for row in data.rows)
    ok = len(data.rows) == 1111 and all(counts.get(k) == v for k, v in EXPECTED_COUNTS.items())
    add(rows, "RANKING-LOADER", "ranking loader", "BLOCKER", "PASS" if ok else "BLOCKER", f"rows={len(data.rows)} counts={dict(counts)}", "Investigate ranking artifact drift.")
    return ok, len(data.rows), dict(counts)


def manual_checklist() -> list[dict[str, str]]:
    return [
        {"step": "apply_patch", "status": "PENDING_MANUAL", "expected": "git am --3way succeeds"},
        {"step": "push_branch", "status": "PENDING_MANUAL", "expected": "git push succeeds"},
        {"step": "clean_checkout", "status": "PENDING_MANUAL", "expected": "fresh clone or clean folder available"},
        {"step": "install_dependencies", "status": "PENDING_MANUAL", "expected": "pip install -r requirements.txt succeeds"},
        {"step": "run_launcher", "status": "PENDING_MANUAL", "expected": "run_local_ui_v2_37.bat starts Streamlit"},
        {"step": "open_browser", "status": "PENDING_MANUAL", "expected": "http://localhost:8501 opens"},
        {"step": "verify_ranking_screen", "status": "PENDING_MANUAL", "expected": "Ranking global (experimental) visible"},
        {"step": "verify_counts", "status": "PENDING_MANUAL", "expected": "318/373/124/270/26 over 1111 rows"},
        {"step": "verify_guardrails", "status": "PENDING_MANUAL", "expected": "no-advice and no-broker copy visible"},
    ]


def report(summary: dict[str, Any]) -> str:
    return f"""# Real Post-Release Local Smoke Test v2.39F

Decision: `{summary['status']}`.

This phase runs the reproducible offline portion of the post-release local smoke test and leaves real Windows/Streamlit/browser checks as explicit manual validation.

## Results

- Checks total: {summary['checks_total']}
- PASS: {summary['pass_count']}
- WARN: {summary['warn_count']}
- BLOCKER: {summary['blocker_count']}
- Compile failures: {summary['compile_fail_count']}
- Ranking loader: `{summary['ranking_loader_status']}`
- Ranking total: {summary['ranking_total']}
- Ranking populations: {summary['ranking_main_count']}/{summary['ranking_partial_count']}/{summary['ranking_review_required_count']}/{summary['ranking_blocked_count']}/{summary['ranking_no_adapter_count']}
- Launcher: `{summary['launcher_status']}`
- Streamlit environment: `{summary['streamlit_environment_status']}`
- Browser validation: `{summary['browser_validation_status']}`

Warnings are documented for Streamlit/browser checks that require a real local runtime. No network, dependency installation, scoring, ranking rebuild, dataset mutation, UI change, broker action, tag creation, asset upload or GitHub Release was performed.

Next recommended phase: `{summary['next_recommended_phase']}`.
"""


def build() -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_SUMMARY.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    add(rows, "SRC-001", "source phase", "BLOCKER", "PASS" if source.get("status") == contract["required_source_status"] else "BLOCKER", str(source.get("status")), "Run v2.39E first.")
    for path_text in REQUIRED_FILES:
        exists = (ROOT / path_text).is_file()
        add(rows, "FILE-001", "release assets", "BLOCKER", "PASS" if exists else "BLOCKER", path_text, "Restore missing release/smoke asset.")
    launcher = (ROOT / "run_local_ui_v2_37.bat").read_text(encoding="utf-8", errors="replace")
    add(rows, "LAUNCHER-001", "launcher", "BLOCKER", "PASS" if "streamlit run app_v2_37.py" in launcher else "BLOCKER", "streamlit run app_v2_37.py", "Fix launcher entrypoint.")
    compile_fail_count = compile_checks(rows)
    ranking_ok, ranking_total, counts = load_ranking_via_module(rows)
    doc_text = "\n".join((ROOT / p).read_text(encoding="utf-8", errors="replace") for p in ["README.md", "VERSION.md", "CHANGELOG.md", "ROADMAP_v2_38_CURRENT.md"])
    add(rows, "DOC-001", "public documentation", "BLOCKER", "PASS" if "v2.39F" in doc_text and "v2.40A" in doc_text else "BLOCKER", "docs mention current and next phase", "Update public docs.")
    add(rows, "GUARDRAIL-001", "no-advice guardrails", "BLOCKER", "PASS" if "sin recomendaciones financieras" in doc_text and "sin broker" in doc_text else "BLOCKER", "no-advice/no-broker copy checked", "Restore guardrail language.")
    streamlit_status = "STREAMLIT_AVAILABLE" if shutil.which("streamlit") else "STREAMLIT_NOT_AVAILABLE_IN_BUILDER_ENV"
    add(rows, "STREAMLIT-001", "Streamlit availability", "WARN", "WARN" if streamlit_status != "STREAMLIT_AVAILABLE" else "PASS", streamlit_status, "Run real Streamlit check on Windows.")
    add(rows, "BROWSER-001", "browser/manual validation", "WARN", "WARN", "MANUAL_REQUIRED", "Open browser manually; do not claim real browser pass here.")
    for item in manual_checklist():
        add(rows, "MANUAL-001", "post-release checklist", "WARN", "WARN", item["step"], item["expected"])
    blocker_count = sum(row["status"] == "BLOCKER" for row in rows)
    summary = {
        "phase": PHASE,
        "status": contract["status_target"] if blocker_count == 0 else "REAL_POST_RELEASE_LOCAL_SMOKE_TEST_BLOCKED",
        "qa_status": "PASS" if blocker_count == 0 else "FAIL",
        "source_phase": contract["source_phase"],
        "source_status": source.get("status"),
        "stable_tag": contract["stable_tag"],
        "publication_scope": contract["publication_scope"],
        "test_scope": contract["test_scope"],
        "target_runtime": contract["target_runtime"],
        "checks_total": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "warn_count": sum(row["status"] == "WARN" for row in rows),
        "blocker_count": blocker_count,
        "compile_checks_total": len(COMPILE_FILES),
        "compile_fail_count": compile_fail_count,
        "ranking_loader_status": "PASS" if ranking_ok else "BLOCKER",
        "ranking_available": bool(ranking_ok),
        "ranking_total": ranking_total,
        "ranking_main_count": counts.get("ELIGIBLE_PARTIAL", 0),
        "ranking_partial_count": counts.get("PARTIAL_COMPARABILITY", 0),
        "ranking_review_required_count": counts.get("REVIEW_REQUIRED", 0),
        "ranking_blocked_count": counts.get("BLOCKED", 0),
        "ranking_no_adapter_count": counts.get("NOT_YET_SCORED_NO_ADAPTER", 0),
        "launcher_status": "PASS" if any(r["check_id"] == "LAUNCHER-001" and r["status"] == "PASS" for r in rows) else "BLOCKER",
        "streamlit_environment_status": streamlit_status,
        "browser_validation_status": "MANUAL_REQUIRED",
        "manual_steps_count": len(manual_checklist()),
        "next_recommended_phase": contract["next_recommended_phase"],
        **GUARDRAILS,
    }
    matrix_path = OUT / "real_post_release_local_smoke_matrix_v2_39f.csv"
    checklist_path = OUT / "real_post_release_local_manual_checklist_v2_39f.csv"
    summary_path = OUT / "real_post_release_local_smoke_summary_v2_39f.json"
    report_path = OUT / "REAL_POST_RELEASE_LOCAL_SMOKE_TEST_v2_39f.md"
    readme_path = OUT / "README.md"
    write_csv(matrix_path, rows, ["check_id", "category", "severity", "status", "evidence", "remediation"])
    write_csv(checklist_path, manual_checklist(), ["step", "status", "expected"])
    write_json(summary_path, summary)
    write_text(report_path, report(summary))
    write_text(readme_path, "# v2.39F Real Post-Release Local Smoke Test\n\nOffline smoke evidence and manual local runtime checklist.\n")
    manifest_path = OUT / "real_post_release_local_smoke_manifest_v2_39f.json"
    outputs = [matrix_path, checklist_path, summary_path, report_path, readme_path]
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
            rel(RANKING_PATH): {"bytes": RANKING_PATH.stat().st_size, "sha256": sha256(RANKING_PATH)},
        },
        "outputs": {rel(p): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in outputs},
        "ranking_counts": {k: summary[k] for k in ["ranking_total", "ranking_main_count", "ranking_partial_count", "ranking_review_required_count", "ranking_blocked_count", "ranking_no_adapter_count"]},
        "guardrails": GUARDRAILS,
    }
    write_json(manifest_path, manifest)
    return summary


def main() -> int:
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
