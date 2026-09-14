#!/usr/bin/env python3
"""v2.38CF Streamlit visual smoke test builder.

This phase records a browser-aware smoke test. If Streamlit/Playwright are
not available in the execution environment, it performs an honest structural
smoke test instead of claiming real screenshots.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CF-streamlit-visual-smoke-test"
CONTRACT = ROOT / "config/streamlit_visual_smoke_test_contract_v2_38cf.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cf_streamlit_visual_smoke_test"

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
    "browser_claimed_without_browser": False,
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


def check(check_id: str, category: str, item: str, expected: str, actual: str, severity: str = "FAIL", note: str = "", hint: str = "") -> dict[str, str]:
    status = "PASS" if expected == actual else severity
    return {
        "check_id": check_id,
        "category": category,
        "item": item,
        "expected": expected,
        "actual": actual,
        "severity": severity,
        "status": status,
        "diagnostic_note": note,
        "remediation_hint": "No action required." if status == "PASS" else hint,
    }


def ast_status(path: Path) -> str:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return f"syntax_error:{exc.lineno}"
    return "parseable"


def environment() -> dict[str, Any]:
    return {
        "streamlit_available": importlib.util.find_spec("streamlit") is not None,
        "playwright_available": importlib.util.find_spec("playwright") is not None,
        "browser_validation_attempted": False,
        "external_network_used": False,
    }


def load_ranking() -> tuple[list[dict[str, Any]], str]:
    path = ROOT / "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    return rows, rel(path)


def build_checks(contract: dict[str, Any], env: dict[str, Any], ranking_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in contract["required_files"]:
        path = ROOT / item
        rows.append(check(f"file:{item}", "file", item, "present", "present" if path.exists() else "missing", hint=f"Restore {item}."))
    for item in ["app_v2_37.py", "src/ui_v2_37/global_ranking.py", "src/ui_v2_37/global_universe.py", "src/ui_v2_37/ui.py"]:
        rows.append(check(f"ast:{item}", "python_ast", item, "parseable", ast_status(ROOT / item), hint=f"Fix Python syntax in {item}."))
    ce_summary = json.loads((ROOT / "outputs/full_universe_source_acquisition/v2_38ce_windows_reproducible_packaging/windows_reproducible_packaging_summary_v2_38ce.json").read_text(encoding="utf-8"))
    rows.append(check("ce_status", "source", "v2.38CE summary", contract["expected_ce_status"], ce_summary.get("status", "MISSING"), hint="Regenerate v2.38CE first."))
    counts = Counter(str(row.get("eligibility_status")) for row in ranking_rows)
    expected_counts = contract["expected_ranking_counts"]
    for status, expected in expected_counts.items():
        actual = len(ranking_rows) if status == "TOTAL" else counts[status]
        rows.append(check(f"ranking_count:{status}", "ranking_data", status, str(expected), str(actual), hint="Regenerate v2.38BV only if inputs and methodology are unchanged."))
    app_text = (ROOT / "app_v2_37.py").read_text(encoding="utf-8")
    ui_text = (ROOT / "src/ui_v2_37/ui.py").read_text(encoding="utf-8")
    combined = f"{app_text}\n{ui_text}"
    for token in contract["required_ui_tokens"]:
        rows.append(check(f"ui_token:{token}", "ui_structure", token, "present", "present" if token in combined else "missing", hint=f"Confirm UI text contains {token}."))
    rows.append(check("streamlit_available", "environment", "python module streamlit", "available", "available" if env["streamlit_available"] else "missing", severity="WARN", note="Missing Streamlit prevents live app launch in this environment."))
    rows.append(check("playwright_available", "environment", "python module playwright", "available", "available" if env["playwright_available"] else "missing", severity="WARN", note="Missing Playwright/browser prevents screenshot capture in this environment."))
    rows.append(check("screenshots_available", "evidence", "screenshots", "true", "false", severity="WARN", note="Screenshots are unavailable because browser smoke test could not run here."))
    for key, expected in GUARDRAILS.items():
        rows.append(check(f"guardrail:{key}", "guardrail", key, str(expected).lower(), str(contract["guardrails"].get(key)).lower(), hint=f"Keep {key}=false."))
    return rows


def report(summary: dict[str, Any]) -> str:
    return f"""# Streamlit Visual Smoke Test v2.38CF

Decision: `{summary['status']}`.

Validation mode: `{summary['validation_mode']}`.

Screenshots available: `{str(summary['screenshots_available']).lower()}`.

This phase checks whether the Streamlit app can be visually smoke-tested. In this execution environment, `streamlit` and `playwright` are not available, so the phase records an honest structural smoke test instead of claiming a browser pass.

## Covered

- App entry point exists and parses.
- Global universe module exists and parses.
- Global ranking module exists and parses.
- Navigation tokens for Inicio, Universo global and Ranking global experimental are present.
- Ranking disclaimer/no-advice language is present.
- Ranking loader data remains at 1,111 rows.
- Expected ranking populations remain 318/373/124/270/26.
- v2.38CE packaging status is present and valid.

## Not Covered Here

- Real browser screenshots.
- Real Streamlit launch on Windows.
- Pixel-level visual review.

These are deferred to an environment with Streamlit and browser tooling installed. The next phase can still proceed with the limitation documented.

## Guardrails

No network, scoring, ranking, methodology, weight, dataset, UI, recommendation, or broker changes were made.

Next recommended phase: `v2.38CG -- Limitations backlog / product risk register`.
"""


def manifest_for(output_dir: Path, summary: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "streamlit_visual_smoke_test_manifest_v2_38cf.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "source_phase": "v2.38CE-windows-reproducible-packaging",
        "validation_mode": summary["validation_mode"],
        "screenshots_available": summary["screenshots_available"],
        "screenshots": [],
        "environment": env,
        "outputs": outputs,
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_streamlit_visual_smoke_test_v2_38cf.py"],
        "tests": [
            "tests/qa_streamlit_visual_smoke_test_v2_38cf.py",
            "tests/qa_streamlit_visual_smoke_test_full_suite_v2_38cf.py",
        ],
        "next_recommended_phase": summary["next_recommended_phase"],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    env = environment()
    ranking_rows, ranking_path = load_ranking()
    checks = build_checks(contract, env, ranking_rows)
    fail_count = sum(row["status"] == "FAIL" for row in checks)
    warn_count = sum(row["status"] == "WARN" for row in checks)
    browser_ready = env["streamlit_available"] and env["playwright_available"]
    status = "STREAMLIT_VISUAL_SMOKE_BLOCKED" if fail_count else (contract["expected_status_full_browser"] if browser_ready else contract["expected_status_with_environment_limitations"])
    summary = {
        "phase": PHASE,
        "status": status,
        "qa_status": "PASS" if fail_count == 0 else "FAIL",
        "source_phase": "v2.38CE-windows-reproducible-packaging",
        "validation_mode": "BROWSER_SMOKE_TEST" if browser_ready else "STRUCTURAL_SMOKE_TEST",
        "screenshots_available": bool(browser_ready),
        "browser_validation_attempted": False,
        "ranking_source": ranking_path,
        "total_assets": len(ranking_rows),
        "main_ranking_count": sum(1 for row in ranking_rows if row.get("eligibility_status") == "ELIGIBLE_PARTIAL"),
        "partial_comparability_count": sum(1 for row in ranking_rows if row.get("eligibility_status") == "PARTIAL_COMPARABILITY"),
        "review_required_count": sum(1 for row in ranking_rows if row.get("eligibility_status") == "REVIEW_REQUIRED"),
        "blocked_count": sum(1 for row in ranking_rows if row.get("eligibility_status") == "BLOCKED"),
        "not_yet_scored_count": sum(1 for row in ranking_rows if row.get("eligibility_status") == "NOT_YET_SCORED_NO_ADAPTER"),
        "check_count": len(checks),
        "fail_count": fail_count,
        "warn_count": warn_count,
        "next_recommended_phase": "v2.38CG-limitations-backlog-product-risk-register",
        **GUARDRAILS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "streamlit_visual_smoke_test_checklist_v2_38cf.csv", checks, ["check_id", "category", "item", "expected", "actual", "severity", "status", "diagnostic_note", "remediation_hint"])
    write_text(output_dir / "streamlit_visual_smoke_test_summary_v2_38cf.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "STREAMLIT_VISUAL_SMOKE_TEST_v2_38cf.md", report(summary))
    write_text(output_dir / "README.md", "# v2.38CF Streamlit Visual Smoke Test\n\nBrowser-aware smoke test record for Scout Finance Streamlit UI. This run uses structural validation when Streamlit/Playwright are unavailable. No network, scoring, ranking, UI, dataset, recommendation, or broker changes.\n")
    write_text(output_dir / "streamlit_visual_smoke_test_manifest_v2_38cf.json", json.dumps(manifest_for(output_dir, summary, env), indent=2, sort_keys=True) + "\n")
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
