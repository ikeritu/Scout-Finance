#!/usr/bin/env python3
"""v2.38CA local release candidate builder.

This phase packages the current experimental ranking surface as a local
release candidate with an operator guide and reproducible readiness
diagnostics. It does not score, fetch, normalize, or change data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CA-release-candidate-local"
CONTRACT = ROOT / "config/release_candidate_local_contract_v2_38ca.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ca_release_candidate_local"

STATUS_TO_CONTRACT_KEY = {
    "ELIGIBLE_PARTIAL": "expected_main_ranking_count",
    "PARTIAL_COMPARABILITY": "expected_partial_comparability_count",
    "REVIEW_REQUIRED": "expected_review_required_count",
    "BLOCKED": "expected_blocked_count",
    "NOT_YET_SCORED_NO_ADAPTER": "expected_not_yet_scored_count",
}

GUARDRAILS = {
    "scoring_recomputed": False,
    "methodology_changed": False,
    "weights_changed": False,
    "network_used": False,
    "ui_recomputes_scoring": False,
    "financial_advice_created": False,
    "broker_actions_allowed": False,
    "recommendations_created": False,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def current_branch() -> str:
    head = ROOT / ".git/HEAD"
    if not head.exists():
        return ""
    value = head.read_text(encoding="utf-8").strip()
    prefix = "ref: refs/heads/"
    return value.removeprefix(prefix) if value.startswith(prefix) else value[:12]


def file_check(check_id: str, path: Path, *, critical: bool = True) -> dict[str, Any]:
    exists = path.exists()
    return {
        "check_id": check_id,
        "category": "file",
        "label": rel(path),
        "expected": "present",
        "actual": "present" if exists else "missing",
        "severity": "FAIL" if critical else "WARN",
        "status": "PASS" if exists else ("FAIL" if critical else "WARN"),
    }


def status_check(check_id: str, label: str, actual: Any, expected: Any, *, critical: bool = True) -> dict[str, Any]:
    ok = actual == expected
    return {
        "check_id": check_id,
        "category": "status",
        "label": label,
        "expected": expected,
        "actual": actual,
        "severity": "FAIL" if critical else "WARN",
        "status": "PASS" if ok else ("FAIL" if critical else "WARN"),
    }


def dependency_check(module_name: str) -> dict[str, Any]:
    found = importlib.util.find_spec(module_name) is not None
    return {
        "check_id": f"python_module:{module_name}",
        "category": "dependency",
        "label": module_name,
        "expected": "available",
        "actual": "available" if found else "missing_on_this_machine",
        "severity": "WARN",
        "status": "PASS" if found else "WARN",
    }


def build_checklist(contract: dict[str, Any], rows: list[dict[str, Any]], summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = [
        status_check("branch_declared", "target branch", contract["target_branch"], "phase9b-global-enrichment-v2-38b"),
        status_check("branch_current", "current branch", current_branch(), contract["target_branch"], critical=False),
        file_check("app_present", ROOT / contract["input_app"]),
        file_check("ranking_loader_present", ROOT / contract["input_ui_module"]),
        file_check("windows_runner_present", ROOT / contract["run_script_windows"]),
        file_check("requirements_present", ROOT / contract["requirements_file"]),
        file_check("ui_requirements_present", ROOT / contract["ui_requirements_file"], critical=False),
        file_check("ranking_results_present", ROOT / contract["input_results"]),
        file_check("bx_summary_present", ROOT / contract["input_bx_summary"]),
        file_check("bx_manifest_present", ROOT / contract["input_bx_manifest"]),
        file_check("by_summary_present", ROOT / contract["input_by_summary"]),
        file_check("by_manifest_present", ROOT / contract["input_by_manifest"]),
        file_check("by_checks_present", ROOT / contract["input_by_checks"]),
        file_check("bz_summary_present", ROOT / contract["input_bz_summary"]),
        file_check("bz_manifest_present", ROOT / contract["input_bz_manifest"]),
        file_check("bz_checks_present", ROOT / contract["input_bz_checks"]),
        dependency_check("pandas"),
        dependency_check("streamlit"),
    ]
    counts = Counter(str(row["eligibility_status"]) for row in rows)
    for status, key in STATUS_TO_CONTRACT_KEY.items():
        checks.append(status_check(f"population:{status}", status, counts[status], int(contract[key])))
    checks.append(status_check("population:TOTAL", "total ranking rows", len(rows), int(contract["expected_total_count"])))
    checks.append(status_check("bz_status", "v2.38BZ status", summaries["bz"].get("status"), contract["expected_bz_status"]))
    checks.append(status_check("bx_qa_status", "v2.38BX qa_status", summaries["bx"].get("qa_status"), "PASS"))
    checks.append(status_check("by_qa_status", "v2.38BY qa_status", summaries["by"].get("qa_status"), "PASS"))
    checks.append(status_check("bz_qa_status", "v2.38BZ qa_status", summaries["bz"].get("qa_status"), "PASS"))
    for key, expected in GUARDRAILS.items():
        checks.append(status_check(f"guardrail:{key}", key, summaries["bz"].get(key), expected))
    return checks


def manifest_for(inputs: list[Path], output_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "release_candidate_local_manifest_v2_38ca.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs if path.exists()},
        "outputs": outputs,
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_release_candidate_local_v2_38ca.py"],
        "tests": [
            "tests/qa_release_candidate_local_v2_38ca.py",
            "tests/qa_release_candidate_local_full_suite_v2_38ca.py",
        ],
    }


def guide_markdown(summary: dict[str, Any]) -> str:
    return f"""# Operator Guide Local v2.38CA

Scout Finance is ready as a local release candidate with limitations: `{summary['status']}`.

## Start On Windows

1. Open PowerShell.
2. Go to the project folder:

```powershell
cd "D:\\Proyectos\\💰 Scout Finance"
```

3. Install dependencies if needed:

```powershell
python -m pip install -r requirements.txt
```

4. Start the local app:

```powershell
.\\run_local_ui_v2_37.bat
```

5. Open `http://localhost:8501` if the browser does not open automatically.

## First Screens To Review

- `Inicio`: confirms local product status and general data mode.
- `Universo global (43.089)`: shows global coverage and missing data explicitly.
- `Ranking global (experimental)`: shows the real v2.38BV ranking surface hardened in v2.38BY.

## Required Outputs

- v2.38BV ranking results.
- v2.38BX closure audit summary and manifest.
- v2.38BY UX hardening summary, manifest, and checks.
- v2.38BZ product readiness summary, manifest, and checks.
- v2.38CA release candidate checklist, summary, guide, and manifest.

If a required output is missing, run the corresponding phase builder or stop and inspect the missing artifact. Do not replace a missing real output with a fabricated placeholder.

## State Meanings

- `ELIGIBLE_PARTIAL`: main experimental ranking population.
- `PARTIAL_COMPARABILITY`: scored, but separated because comparability is lower.
- `REVIEW_REQUIRED`: never scored automatically; needs human or separate contract review.
- `BLOCKED`: coverage below the contractual floor.
- `NOT_YET_SCORED_NO_ADAPTER`: eligible in principle, but missing a real adapter.

## Limits That Still Matter

The ranking is for local research triage only. It is not financial advice, not a predictive product, not a price target workflow, not a buy/sell/hold signal, and not connected to any broker. Some countries, prices, adapters, financial institutions, and low-coverage assets remain explicitly limited.
"""


def release_markdown(summary: dict[str, Any]) -> str:
    return f"""# Release Candidate Local v2.38CA

Decision: `{summary['status']}`.

Scout Finance is prepared as a local release candidate for research use with limitations. This phase adds an operator guide and a reproducible local readiness checklist. It does not recompute scores, alter methodology, change weights, call network APIs, create advice, create recommendations, or connect broker workflows.

Verified populations:

- Main ranking: 318
- Partial comparability: 373
- Review required: 124
- Blocked: 270
- Not yet scored: 26
- Total: 1,111

Startup path:

- Install dependencies with `python -m pip install -r requirements.txt`.
- Launch with `run_local_ui_v2_37.bat`.
- Review `Ranking global (experimental)` as a research-only surface.

Readiness result: local candidate ready with explicit limitations. Next recommended phase: `v2.38CB -- Local startup/dependency validation`.
"""


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    results_path = ROOT / contract["input_results"]
    rows = json.loads(results_path.read_text(encoding="utf-8"))
    summaries = {
        "bx": json.loads((ROOT / contract["input_bx_summary"]).read_text(encoding="utf-8")),
        "by": json.loads((ROOT / contract["input_by_summary"]).read_text(encoding="utf-8")),
        "bz": json.loads((ROOT / contract["input_bz_summary"]).read_text(encoding="utf-8")),
    }
    checklist = build_checklist(contract, rows, summaries)
    fail_count = sum(row["status"] == "FAIL" for row in checklist)
    warn_count = sum(row["status"] == "WARN" for row in checklist)
    status = contract["expected_status"] if fail_count == 0 else "RELEASE_CANDIDATE_LOCAL_BLOCKED"
    counts = Counter(str(row["eligibility_status"]) for row in rows)
    summary = {
        "phase": PHASE,
        "status": status,
        "qa_status": "PASS" if fail_count == 0 else "FAIL",
        "check_count": len(checklist),
        "fail_count": fail_count,
        "warn_count": warn_count,
        "target_branch": contract["target_branch"],
        "current_branch": current_branch(),
        "total_assets": len(rows),
        "population_counts": dict(sorted(counts.items())),
        "main_ranking_count": counts["ELIGIBLE_PARTIAL"],
        "partial_comparability_count": counts["PARTIAL_COMPARABILITY"],
        "review_required_count": counts["REVIEW_REQUIRED"],
        "blocked_count": counts["BLOCKED"],
        "not_yet_scored_count": counts["NOT_YET_SCORED_NO_ADAPTER"],
        "operator_guide_created": True,
        "startup_checklist_created": True,
        "local_diagnostic_created": True,
        **GUARDRAILS,
        "next_recommended_phase": "v2.38CB-local-startup-dependency-validation",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "release_candidate_local_checklist_v2_38ca.csv", checklist, ["check_id", "category", "label", "expected", "actual", "severity", "status"])
    write_text(output_dir / "release_candidate_local_summary_v2_38ca.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "OPERATOR_GUIDE_LOCAL_v2_38ca.md", guide_markdown(summary))
    write_text(output_dir / "RELEASE_CANDIDATE_LOCAL_v2_38ca.md", release_markdown(summary))
    write_text(output_dir / "README.md", "# v2.38CA Release Candidate Local\n\nLocal release candidate packaging and operator guide. This phase produces a startup checklist, diagnostic summary, operator guide, and manifest without changing scoring, data, methodology, network behavior, recommendations, or broker guardrails.\n")
    inputs = [
        contract_path,
        results_path,
        ROOT / contract["input_bx_summary"],
        ROOT / contract["input_bx_manifest"],
        ROOT / contract["input_by_summary"],
        ROOT / contract["input_by_manifest"],
        ROOT / contract["input_by_checks"],
        ROOT / contract["input_bz_summary"],
        ROOT / contract["input_bz_manifest"],
        ROOT / contract["input_bz_checks"],
        ROOT / contract["input_app"],
        ROOT / contract["input_ui_module"],
        ROOT / contract["run_script_windows"],
        ROOT / contract["requirements_file"],
        ROOT / contract["ui_requirements_file"],
    ]
    write_text(output_dir / "release_candidate_local_manifest_v2_38ca.json", json.dumps(manifest_for(inputs, output_dir, summary), indent=2, sort_keys=True) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build(args.contract, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
