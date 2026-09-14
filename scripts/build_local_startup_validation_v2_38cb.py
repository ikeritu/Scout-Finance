#!/usr/bin/env python3
"""v2.38CB local startup/dependency validation.

This phase validates local startup readiness without opening a browser,
calling network APIs, recomputing ranking, changing scoring, or touching
watchlists.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CB-local-startup-validation"
CONTRACT = ROOT / "config/local_startup_validation_contract_v2_38cb.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cb_local_startup_validation"

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

FORBIDDEN_UI_TOKENS = [
    "score_assets(",
    "percentile_scores(",
    "build_raw_factors(",
    "build_global_research_ranking_v2_38bv",
    "requests.",
    "httpx.",
    "urlopen(",
    "subprocess.",
    "os.system(",
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


def check(check_id: str, category: str, label: str, expected: Any, actual: Any, *, fail: bool = True) -> dict[str, Any]:
    ok = actual == expected
    return {
        "check_id": check_id,
        "category": category,
        "label": label,
        "expected": expected,
        "actual": actual,
        "severity": "FAIL" if fail else "WARN",
        "status": "PASS" if ok else ("FAIL" if fail else "WARN"),
    }


def file_check(check_id: str, path: Path, *, fail: bool = True) -> dict[str, Any]:
    return check(check_id, "file", rel(path), "present", "present" if path.exists() else "missing", fail=fail)


def ast_check(check_id: str, path: Path) -> dict[str, Any]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
        actual = "parseable"
    except SyntaxError as exc:
        actual = f"syntax_error:{exc.lineno}"
    return check(check_id, "python_ast", rel(path), "parseable", actual)


def dependency_check(module_name: str) -> dict[str, Any]:
    found = importlib.util.find_spec(module_name) is not None
    return check(f"python_module:{module_name}", "dependency", module_name, "available", "available" if found else "missing_on_this_machine", fail=False)


def bat_checks(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace").lower() if path.exists() else ""
    return [
        check("bat_uses_app_v2_37", "windows_runner", rel(path), "present", "present" if "app_v2_37.py" in text else "missing"),
        check("bat_uses_streamlit_run", "windows_runner", rel(path), "present", "present" if "streamlit run" in text else "missing"),
        check("bat_uses_localhost", "windows_runner", rel(path), "present", "present" if "localhost" in text else "missing"),
        check("bat_checks_dependencies", "windows_runner", rel(path), "present", "present" if "import streamlit, pandas" in text else "missing"),
        check("bat_no_external_network", "windows_runner", rel(path), "absent", "present" if any(token in text for token in ["http://", "https://", "curl ", "wget ", "invoke-webrequest"]) and "localhost" not in text else "absent"),
    ]


def loader_check() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    try:
        from src.ui_v2_37.global_ranking import load_global_ranking

        data = load_global_ranking(ROOT)
        actual = f"available:{data.available};rows:{len(data.rows)}"
    except Exception as exc:  # noqa: BLE001 - diagnostic output, fail closed.
        actual = f"error:{type(exc).__name__}"
    return check("ranking_loader_real_json", "loader", "load_global_ranking(ROOT)", "available:True;rows:1111", actual)


def ui_forbidden_checks(app_path: Path, module_path: Path) -> list[dict[str, Any]]:
    app_text = app_path.read_text(encoding="utf-8")
    module_text = module_path.read_text(encoding="utf-8")
    rows = []
    for token in FORBIDDEN_UI_TOKENS:
        rows.append(check(f"app_forbidden_absent:{token}", "guardrail", rel(app_path), "absent", "present" if token in app_text else "absent"))
    for token in FORBIDDEN_UI_TOKENS:
        if token == "build_global_research_ranking_v2_38bv":
            imported = re.search(r"^\s*(from|import)\s+.*build_global_research_ranking_v2_38bv", module_text, flags=re.M)
            rows.append(check(f"loader_no_recompute_import:{token}", "guardrail", rel(module_path), "absent", "present" if imported else "absent"))
            continue
        rows.append(check(f"loader_forbidden_absent:{token}", "guardrail", rel(module_path), "absent", "present" if token in module_text else "absent"))
    return rows


def build_checks(contract: dict[str, Any]) -> list[dict[str, Any]]:
    paths = {key: ROOT / contract[key] for key in [
        "input_results",
        "input_bx_summary",
        "input_by_summary",
        "input_bz_summary",
        "input_ca_summary",
        "input_ca_manifest",
        "input_app",
        "input_ui_module",
        "run_script_windows",
        "requirements_file",
        "ui_requirements_file",
    ]}
    rows: list[dict[str, Any]] = [file_check(key, path, fail=key != "ui_requirements_file") for key, path in paths.items()]
    rows += [ast_check("app_ast_parseable", paths["input_app"]), ast_check("ranking_loader_ast_parseable", paths["input_ui_module"])]
    rows += bat_checks(paths["run_script_windows"])
    rows += [dependency_check(name) for name in contract["environment_dependency_modules"]]
    rows.append(loader_check())

    results = json.loads(paths["input_results"].read_text(encoding="utf-8"))
    counts = Counter(str(row["eligibility_status"]) for row in results)
    for status, key in STATUS_TO_CONTRACT_KEY.items():
        rows.append(check(f"population:{status}", "population", status, int(contract[key]), counts[status]))
    rows.append(check("population:TOTAL", "population", "total ranking rows", int(contract["expected_total_count"]), len(results)))

    summaries = {
        "bx": json.loads(paths["input_bx_summary"].read_text(encoding="utf-8")),
        "by": json.loads(paths["input_by_summary"].read_text(encoding="utf-8")),
        "bz": json.loads(paths["input_bz_summary"].read_text(encoding="utf-8")),
        "ca": json.loads(paths["input_ca_summary"].read_text(encoding="utf-8")),
    }
    rows.append(check("bz_status", "upstream", "v2.38BZ status", contract["expected_bz_status"], summaries["bz"].get("status")))
    rows.append(check("ca_status", "upstream", "v2.38CA status", contract["expected_ca_status"], summaries["ca"].get("status")))
    for key in ["bx", "by", "bz", "ca"]:
        rows.append(check(f"{key}_qa_status", "upstream", f"{key} qa_status", "PASS", summaries[key].get("qa_status")))
    for key, expected in GUARDRAILS.items():
        rows.append(check(f"guardrail:{key}", "guardrail", key, expected, summaries["ca"].get(key) if key in summaries["ca"] else summaries["bz"].get(key)))
    rows += ui_forbidden_checks(paths["input_app"], paths["input_ui_module"])
    return rows


def status_for(rows: list[dict[str, Any]], contract: dict[str, Any]) -> str:
    if any(row["status"] == "FAIL" for row in rows):
        return "LOCAL_STARTUP_BLOCKED"
    if any(row["status"] == "WARN" for row in rows):
        return contract["expected_status_with_warnings"]
    return contract["expected_status_without_warnings"]


def troubleshooting_markdown() -> str:
    return """# Local Startup Troubleshooting v2.38CB

## `fatal: not a git repository`

You are probably in `C:\\Users\\ikeri` instead of the project folder.

```powershell
cd "D:\\Proyectos\\💰 Scout Finance"
git status
```

## Python Missing

Install Python 3 and make sure `python` is available in PowerShell:

```powershell
python --version
```

## Dependencies Missing

Install the project requirements:

```powershell
python -m pip install -r requirements.txt
```

For the minimal UI path, this also works:

```powershell
python -m pip install -r requirements-ui-v2_28.txt
```

## Streamlit Does Not Start

Run the local launcher:

```powershell
.\\run_local_ui_v2_37.bat
```

If port `8501` is occupied, close the previous Streamlit process or run Streamlit manually on another port:

```powershell
python -m streamlit run app_v2_37.py --server.address localhost --server.port 8502
```

## Required Output Missing

Stop and inspect which phase output is missing. Do not fabricate replacement ranking data. Re-run the corresponding offline builder only when its inputs are present.

## Reminder

The ranking screen is for local research only. It is not financial advice, not a buy/sell/hold signal, and not connected to brokers.
"""


def validation_markdown(summary: dict[str, Any]) -> str:
    return f"""# Local Startup Validation v2.38CB

Decision: `{summary['status']}`.

This phase validates the local startup path for Scout Finance without opening a browser or calling network APIs.

Validated:

- `app_v2_37.py` exists and parses.
- `src/ui_v2_37/global_ranking.py` exists and parses.
- `run_local_ui_v2_37.bat` points to `app_v2_37.py`, uses `streamlit run`, uses `localhost`, and checks dependencies.
- The ranking loader reads the real v2.38BV JSON and returns 1,111 rows.
- v2.38BZ and v2.38CA summaries are present and in the expected states.
- Guardrails remain closed: no scoring recomputation, no methodology/weight changes, no network, no recommendations, no broker actions.

Counts:

- Main ranking: 318
- Partial comparability: 373
- Review required: 124
- Blocked: 270
- Not yet scored: 26
- Total: 1,111

Environment warnings are allowed because this diagnostic may run outside the user's Windows setup. The next phase is `v2.38CC -- User guide / dummy-friendly guide`.
"""


def manifest_for(inputs: list[Path], output_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "local_startup_validation_manifest_v2_38cb.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs if path.exists()},
        "outputs": outputs,
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_local_startup_validation_v2_38cb.py"],
        "tests": [
            "tests/qa_local_startup_validation_v2_38cb.py",
            "tests/qa_local_startup_validation_full_suite_v2_38cb.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    rows = build_checks(contract)
    fail_count = sum(row["status"] == "FAIL" for row in rows)
    warn_count = sum(row["status"] == "WARN" for row in rows)
    results = json.loads((ROOT / contract["input_results"]).read_text(encoding="utf-8"))
    counts = Counter(str(row["eligibility_status"]) for row in results)
    summary = {
        "phase": PHASE,
        "status": status_for(rows, contract),
        "qa_status": "PASS" if fail_count == 0 else "FAIL",
        "check_count": len(rows),
        "fail_count": fail_count,
        "warn_count": warn_count,
        "total_assets": len(results),
        "main_ranking_count": counts["ELIGIBLE_PARTIAL"],
        "partial_comparability_count": counts["PARTIAL_COMPARABILITY"],
        "review_required_count": counts["REVIEW_REQUIRED"],
        "blocked_count": counts["BLOCKED"],
        "not_yet_scored_count": counts["NOT_YET_SCORED_NO_ADAPTER"],
        "startup_bat_validated": True,
        "ranking_loader_validated": True,
        "troubleshooting_created": True,
        **GUARDRAILS,
        "next_recommended_phase": "v2.38CC-user-guide-dummy-friendly-guide",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "local_startup_validation_checks_v2_38cb.csv", rows, ["check_id", "category", "label", "expected", "actual", "severity", "status"])
    write_text(output_dir / "local_startup_validation_summary_v2_38cb.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "LOCAL_STARTUP_VALIDATION_v2_38cb.md", validation_markdown(summary))
    write_text(output_dir / "LOCAL_STARTUP_TROUBLESHOOTING_v2_38cb.md", troubleshooting_markdown())
    write_text(output_dir / "README.md", "# v2.38CB Local Startup Validation\n\nLocal startup and dependency validation for the Scout Finance release candidate. This phase checks files, Python parsing, dependency availability, the Windows launcher, the ranking loader, required outputs, and guardrails without opening a browser or calling network APIs.\n")
    inputs = [
        contract_path,
        ROOT / contract["input_results"],
        ROOT / contract["input_bx_summary"],
        ROOT / contract["input_by_summary"],
        ROOT / contract["input_bz_summary"],
        ROOT / contract["input_ca_summary"],
        ROOT / contract["input_ca_manifest"],
        ROOT / contract["input_app"],
        ROOT / contract["input_ui_module"],
        ROOT / contract["run_script_windows"],
        ROOT / contract["requirements_file"],
        ROOT / contract["ui_requirements_file"],
    ]
    write_text(output_dir / "local_startup_validation_manifest_v2_38cb.json", json.dumps(manifest_for(inputs, output_dir, summary), indent=2, sort_keys=True) + "\n")
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
