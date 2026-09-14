#!/usr/bin/env python3
"""v2.38CE Windows reproducible local packaging builder.

This phase creates a manifest-based Windows packaging plan from v2.38CD.
It does not create a heavy ZIP, call the network, mutate datasets, change UI,
or recompute ranking/scoring.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CE-windows-reproducible-packaging"
CONTRACT = ROOT / "config/windows_reproducible_packaging_contract_v2_38ce.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ce_windows_reproducible_packaging"
CD_OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cd_required_outputs_diagnostics"

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
    "zip_created": False,
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


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def check(check_id: str, category: str, item: str, expected: str, actual: str, severity: str = "FAIL", hint: str = "") -> dict[str, str]:
    status = "PASS" if expected == actual else severity
    return {
        "check_id": check_id,
        "category": category,
        "item": item,
        "expected": expected,
        "actual": actual,
        "severity": severity,
        "status": status,
        "remediation_hint": hint if status != "PASS" else "No action required.",
    }


def included_files(checklist: list[dict[str, str]]) -> list[Path]:
    paths: list[Path] = []
    for row in checklist:
        if row["status"] == "PRESENT" and row["required_for"] in {"local_app_startup", "experimental_ranking", "watchlists_exports", "release_candidate_docs"}:
            path = ROOT / row["relative_path"]
            if path.exists() and path.is_file():
                paths.append(path)
    paths.extend([
        ROOT / "README.md",
        ROOT / "VERSION.md",
        ROOT / "CHANGELOG.md",
        ROOT / "ROADMAP_v2_38_CURRENT.md",
        ROOT / "config/required_outputs_diagnostics_contract_v2_38cd.json",
        ROOT / "scripts/build_required_outputs_diagnostics_v2_38cd.py",
        ROOT / "tests/qa_required_outputs_diagnostics_v2_38cd.py",
    ])
    return sorted(set(paths), key=lambda p: rel(p))


def build_checks(contract: dict[str, Any], cd_summary: dict[str, Any], files: list[Path]) -> list[dict[str, str]]:
    rows = [
        check("cd_status", "source", "v2.38CD summary", contract["expected_cd_status"], cd_summary.get("status", "MISSING"), hint="Regenerate v2.38CD first."),
        check("cd_blockers", "source", "v2.38CD blocking_missing_count", "0", str(cd_summary.get("blocking_missing_count", "")), hint="Resolve blocking missing outputs before packaging."),
        check("packaging_mode", "packaging", "packaging strategy", contract["packaging_mode"], "manifest_based_reproducible_packaging"),
    ]
    for item in contract["required_windows_paths"]:
        path = ROOT / item
        rows.append(check(f"windows_path:{item}", "windows_preflight", item, "present", "present" if path.exists() else "missing", hint=f"Restore {item}."))
    launcher = ROOT / "run_local_ui_v2_37.bat"
    launcher_text = launcher.read_text(encoding="utf-8", errors="replace").lower() if launcher.exists() else ""
    rows.append(check("launcher_targets_app", "windows_preflight", "run_local_ui_v2_37.bat", "present", "present" if "app_v2_37.py" in launcher_text else "missing", hint="Point launcher to app_v2_37.py."))
    rows.append(check("launcher_uses_localhost", "windows_preflight", "run_local_ui_v2_37.bat", "present", "present" if "localhost" in launcher_text else "missing", hint="Keep Streamlit bound to localhost."))
    secret_hits = [path for path in files if path.name in {".env", "secrets.toml"} or ".git/" in rel(path)]
    rows.append(check("no_secrets_in_manifest", "security", "included files", "0", str(len(secret_hits)), hint="Remove secrets from package manifest."))
    for key, expected in GUARDRAILS.items():
        rows.append(check(f"guardrail:{key}", "guardrail", key, str(expected).lower(), str(contract["guardrails"].get(key)).lower(), hint=f"Keep {key}=false."))
    return rows


def guide(summary: dict[str, Any], contract: dict[str, Any]) -> str:
    excluded = "\n".join(f"- `{item}`" for item in contract["excluded_patterns"])
    return f"""# Windows Reproducible Packaging v2.38CE

Decision: `{summary['status']}`.

This phase defines a reproducible Windows local package through a manifest instead of creating a heavy ZIP. The repository already stores the required files, so the package is reproduced by checking out the branch and validating the manifest.

## Included

- Local app entry point and Windows launcher.
- Python requirements.
- Read-only global ranking UI module and watchlist support.
- v2.38BV ranking outputs required by the UI.
- v2.38BX-v2.38CD audit, readiness, startup, user-guide and diagnostics outputs.
- Current README, VERSION, CHANGELOG and roadmap.

## Excluded

{excluded}

## Windows Start

```powershell
cd "D:\\Proyectos\\💰 Scout Finance"
git status
python --version
python -m pip install -r requirements.txt
.\\run_local_ui_v2_37.bat
```

Open `http://localhost:8501` if the browser does not open automatically.

## Reproducibility

- Source phase: `v2.38CD`.
- Included files: {summary['total_files_in_package']}.
- Total bytes: {summary['total_bytes']}.
- ZIP created: `false`.

## Limitations

This is still a local release candidate package. The ranking remains experimental and the documented missing/degraded data from v2.38CD remains visible. This is not financial advice and does not enable broker actions.

Next recommended phase: `v2.38CF -- Streamlit visual smoke test`.
"""


def preflight() -> str:
    return """# Windows Preflight Checklist v2.38CE

- Open PowerShell.
- Run `cd "D:\\Proyectos\\💰 Scout Finance"`.
- Run `git status` and confirm the branch is `phase9b-global-enrichment-v2-38b`.
- Run `python --version`.
- Run `python -m pip install -r requirements.txt` if dependencies are missing.
- Run `.\\run_local_ui_v2_37.bat`.
- Open `http://localhost:8501`.
- Confirm `Inicio` loads.
- Open `Ranking global (experimental)`.
- Confirm the ranking loads with the expected warning/disclaimer context.
- Review known warnings from v2.38CD before using the app for research.
"""


def manifest_for(files: list[Path], contract: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    included = {
        rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in files
        if path.exists() and path.is_file()
    }
    outputs = {}
    for path in sorted(OUT.glob("*")):
        if path.name != "windows_reproducible_packaging_manifest_v2_38ce.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "source_phase": contract["source_phase"],
        "packaging_mode": contract["packaging_mode"],
        "included_files": included,
        "excluded_patterns": contract["excluded_patterns"],
        "required_outputs_source": rel(CD_OUT / "required_outputs_checklist_v2_38cd.csv"),
        "total_files_in_package": len(included),
        "total_bytes": sum(item["bytes"] for item in included.values()),
        "reproducibility_status": summary["reproducibility_status"],
        "outputs": outputs,
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_windows_reproducible_packaging_v2_38ce.py"],
        "tests": [
            "tests/qa_windows_reproducible_packaging_v2_38ce.py",
            "tests/qa_windows_reproducible_packaging_full_suite_v2_38ce.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    cd_summary = json.loads((CD_OUT / "required_outputs_summary_v2_38cd.json").read_text(encoding="utf-8"))
    checklist = load_rows(CD_OUT / "required_outputs_checklist_v2_38cd.csv")
    files = included_files(checklist)
    total_bytes = sum(path.stat().st_size for path in files if path.exists() and path.is_file())
    checks = build_checks(contract, cd_summary, files)
    fail_count = sum(row["status"] == "FAIL" for row in checks)
    status = "WINDOWS_PACKAGE_BLOCKED" if fail_count else contract["expected_status"]
    summary = {
        "phase": PHASE,
        "status": status,
        "qa_status": "PASS" if fail_count == 0 else "FAIL",
        "source_phase": contract["source_phase"],
        "packaging_mode": contract["packaging_mode"],
        "reproducibility_status": "MANIFEST_REPRODUCIBLE_WITH_WARNINGS" if fail_count == 0 else "BLOCKED",
        "check_count": len(checks),
        "fail_count": fail_count,
        "total_files_in_package": len(files),
        "total_bytes": total_bytes,
        "zip_created": False,
        "next_recommended_phase": "v2.38CF-streamlit-visual-smoke-test",
        **GUARDRAILS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "windows_reproducible_packaging_checklist_v2_38ce.csv", checks, ["check_id", "category", "item", "expected", "actual", "severity", "status", "remediation_hint"])
    write_text(output_dir / "windows_reproducible_packaging_summary_v2_38ce.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "WINDOWS_REPRODUCIBLE_PACKAGING_v2_38ce.md", guide(summary, contract))
    write_text(output_dir / "WINDOWS_PREFLIGHT_CHECKLIST_v2_38ce.md", preflight())
    write_text(output_dir / "README.md", "# v2.38CE Windows Reproducible Packaging\n\nManifest-based Windows local packaging for Scout Finance. No ZIP, network, scoring, ranking, UI, dataset, recommendation, or broker changes.\n")
    write_text(output_dir / "windows_reproducible_packaging_manifest_v2_38ce.json", json.dumps(manifest_for(files, contract, summary), indent=2, sort_keys=True) + "\n")
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
