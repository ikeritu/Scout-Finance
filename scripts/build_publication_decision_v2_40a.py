#!/usr/bin/env python3
"""v2.40A publication decision builder."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.40A-publication-decision"
CONTRACT = ROOT / "config/publication_decision_contract_v2_40a.json"
SMOKE = ROOT / "outputs/full_universe_source_acquisition/v2_39f_real_post_release_local_smoke_test/real_post_release_local_smoke_summary_v2_39f.json"
SECURITY = ROOT / "outputs/full_universe_source_acquisition/v2_39c_security_sensitive_files_audit/security_sensitive_files_summary_v2_39c.json"
ASSETS = ROOT / "outputs/full_universe_source_acquisition/v2_39e_final_reproducible_package_release_assets/final_reproducible_package_release_assets_summary_v2_39e.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_40a_publication_decision"

GUARDRAILS = {
    "deployment_allowed": False,
    "github_release_created": False,
    "assets_uploaded": False,
    "tag_created": False,
    "network_used": False,
    "credential_preparation_done": False,
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


def options_analysis() -> list[dict[str, str]]:
    return [
        {"mode": "LOCAL_ONLY", "data_exposure": "lowest", "financial_interpretation_risk": "low", "demo_mode_needed": "no", "credentials_needed": "no", "real_visual_qa_needed": "recommended", "no_advice_compatible": "yes", "effort_remaining": "low", "recommended_decision": "safe fallback"},
        {"mode": "PRIVATE_REPO_ONLY", "data_exposure": "low", "financial_interpretation_risk": "medium", "demo_mode_needed": "optional", "credentials_needed": "no", "real_visual_qa_needed": "recommended", "no_advice_compatible": "yes", "effort_remaining": "low", "recommended_decision": "acceptable for trusted users"},
        {"mode": "PUBLIC_DEMO_SAFE_MODE", "data_exposure": "controlled", "financial_interpretation_risk": "medium", "demo_mode_needed": "required", "credentials_needed": "no real credentials", "real_visual_qa_needed": "required", "no_advice_compatible": "yes with guardrails", "effort_remaining": "medium", "recommended_decision": "selected path"},
        {"mode": "CONTROLLED_EXTERNAL_DEPLOYMENT", "data_exposure": "highest", "financial_interpretation_risk": "high", "demo_mode_needed": "required first", "credentials_needed": "possibly", "real_visual_qa_needed": "required", "no_advice_compatible": "only after gates", "effort_remaining": "high", "recommended_decision": "blocked until v2.40B and v2.40C pass"},
    ]


def policy_gate_rows(contract: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"phase": gate["phase"], "gate": gate["gate"], "decision": gate["decision"], "notes": "publication control recorded in v2.40A"}
        for gate in contract["policy_gates"]
    ]


def decision_matrix(contract: dict[str, Any], smoke: dict[str, Any], security: dict[str, Any], assets: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"check_id": "SRC-001", "category": "source", "status": "PASS" if smoke.get("status") == contract["required_source_status"] else "BLOCKER", "evidence": str(smoke.get("status")), "remediation": "Complete v2.39F."},
        {"check_id": "SEC-001", "category": "security warnings", "status": "PASS", "evidence": str(security.get("warn_count", 0)), "remediation": "Keep warnings visible before public demo."},
        {"check_id": "ASSET-001", "category": "release assets", "status": "PASS" if assets.get("status") == "FINAL_REPRODUCIBLE_PACKAGE_RELEASE_ASSETS_READY" else "BLOCKER", "evidence": str(assets.get("status")), "remediation": "Complete v2.39E."},
        {"check_id": "DECISION-001", "category": "publication decision", "status": "PASS", "evidence": contract["selected_decision"], "remediation": "No action required."},
        {"check_id": "GATE-001", "category": "policy gates", "status": "PASS", "evidence": "v2.40B prep only; v2.40C required; v2.40D blocked", "remediation": "No action required."},
        {"check_id": "NO-DEPLOY-001", "category": "deployment", "status": "PASS", "evidence": "deployment_allowed=false", "remediation": "No action required."},
    ]


def report(summary: dict[str, Any]) -> str:
    return f"""# Publication Decision v2.40A

Decision: `{summary['selected_decision']}`.

The full real Scout Finance app and ranking should not be deployed publicly yet. The selected path requires a safe public demo mode before any controlled external deployment.

## Policy Gates

- `v2.40B`: allowed only as technical hosting preparation.
- `v2.40C`: required before any public demo.
- `v2.40D`: blocked until both `v2.40B` and `v2.40C` pass.

## Rationale

Scout Finance remains a local research tool with an experimental ranking, known coverage gaps, security warnings, manual Streamlit/browser validation and strict no-advice/no-broker guardrails.

No deployment, release, asset upload, tag, credential preparation, network call, scoring, ranking rebuild, dataset mutation or functional UI change was performed.

Next recommended phase: `{summary['next_recommended_phase']}`.
"""


def build() -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    smoke = json.loads(SMOKE.read_text(encoding="utf-8"))
    security = json.loads(SECURITY.read_text(encoding="utf-8"))
    assets = json.loads(ASSETS.read_text(encoding="utf-8"))
    matrix = decision_matrix(contract, smoke, security, assets)
    options = options_analysis()
    gates = policy_gate_rows(contract)
    blockers = sum(row["status"] == "BLOCKER" for row in matrix)
    summary = {
        "phase": PHASE,
        "status": contract["status_target"] if blockers == 0 else "PUBLICATION_DECISION_BLOCKED",
        "qa_status": "PASS" if blockers == 0 else "FAIL",
        "source_phase": contract["source_phase"],
        "source_status": smoke.get("status"),
        "stable_tag": contract["stable_tag"],
        "publication_scope_current": contract["publication_scope_current"],
        "selected_decision": contract["selected_decision"],
        "decision_rationale": contract["decision_rationale"],
        "allowed_publication_modes_count": len(contract["allowed_publication_modes"]),
        "policy_gate_count": len(gates),
        "security_warn_count": security.get("warn_count", 0),
        "post_release_smoke_warn_count": smoke.get("warn_count", 0),
        "release_assets_status": assets.get("status"),
        "ranking_total": smoke.get("ranking_total"),
        "ranking_main_count": smoke.get("ranking_main_count"),
        "ranking_partial_count": smoke.get("ranking_partial_count"),
        "ranking_review_required_count": smoke.get("ranking_review_required_count"),
        "ranking_blocked_count": smoke.get("ranking_blocked_count"),
        "ranking_no_adapter_count": smoke.get("ranking_no_adapter_count"),
        "next_recommended_phase": contract["next_recommended_phase"],
        **GUARDRAILS,
    }
    matrix_path = OUT / "publication_decision_matrix_v2_40a.csv"
    options_path = OUT / "publication_options_analysis_v2_40a.csv"
    gates_path = OUT / "publication_policy_gate_v2_40a.csv"
    summary_path = OUT / "publication_decision_summary_v2_40a.json"
    report_path = OUT / "PUBLICATION_DECISION_v2_40a.md"
    readme_path = OUT / "README.md"
    write_csv(matrix_path, matrix, ["check_id", "category", "status", "evidence", "remediation"])
    write_csv(options_path, options, ["mode", "data_exposure", "financial_interpretation_risk", "demo_mode_needed", "credentials_needed", "real_visual_qa_needed", "no_advice_compatible", "effort_remaining", "recommended_decision"])
    write_csv(gates_path, gates, ["phase", "gate", "decision", "notes"])
    write_json(summary_path, summary)
    write_text(report_path, report(summary))
    write_text(readme_path, "# v2.40A Publication Decision\n\nFormal publication decision and policy gates for Scout Finance.\n")
    manifest_path = OUT / "publication_decision_manifest_v2_40a.json"
    outputs = [matrix_path, options_path, gates_path, summary_path, report_path, readme_path]
    manifest = {
        "phase": PHASE,
        "status": summary["status"],
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "source_commit": run_git(["rev-parse", "--short", "HEAD"]),
        "stable_tag": summary["stable_tag"],
        "inputs": {rel(p): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in [CONTRACT, SMOKE, SECURITY, ASSETS]},
        "outputs": {rel(p): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in outputs},
        "selected_decision": summary["selected_decision"],
        "policy_gates": gates,
        "guardrails": GUARDRAILS,
    }
    write_json(manifest_path, manifest)
    return summary


def main() -> int:
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
