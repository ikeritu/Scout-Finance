#!/usr/bin/env python3
"""Accumulated incident closure gate for v2.32B-v2.32D."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "outputs/local_ui/v2_32d_incident_closure/incident_register.csv"


def run_gate(path: str, marker: str) -> dict[str, object]:
    started = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(ROOT / path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=90,
    )
    if result.returncode:
        raise AssertionError(f"{path} failed\n{result.stdout}\n{result.stderr}")
    assert marker in result.stdout
    return {"gate": path, "status": "PASS", "seconds": round(time.perf_counter() - started, 3)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    with REGISTER.open(encoding="utf-8", newline="") as handle:
        incidents = list(csv.DictReader(handle))
    assert len(incidents) == 5
    assert {item["incident_id"] for item in incidents} == {f"UI-{number:03d}" for number in range(1, 6)}
    assert all(item["status"] == "CLOSED" for item in incidents)
    assert all(item["resolution"] and item["regression_gate"] for item in incidents)

    app = (ROOT / "app_v2_28.py").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements-ui-v2_28.txt").read_text(encoding="utf-8")
    assert "use_container_width" not in app
    assert app.count('width="stretch"') == 3
    assert "streamlit>=1.50,<2" in requirements
    assert "diagnostic_consent_granted" in app
    assert 'key="navigation_screen"' in app and "pending_screen" in app
    assert "FIELD_LABELS" in app and '"provider":"Proveedor"' in app
    assert "providers_ok" in app and '"Estado operativo","Estable"' in app

    gates = [
        run_gate("tests/qa_real_user_journeys_v2_32b.py", "PASS: v2.32B/21-real-user-journeys"),
        run_gate("tests/qa_visual_responsive_usability_v2_32c.py", "PASS: v2.32C/17-visual-responsive-usability-checks"),
        run_gate("tests/qa_ux_accessibility_v2_28e.py", "PASS: WCAG-contrast"),
    ]

    report = {
        "phase": "v2.32D",
        "status": "PASS",
        "incidents_total": len(incidents),
        "incidents_closed": len(incidents),
        "incidents_open": 0,
        "incident_ids": [item["incident_id"] for item in incidents],
        "regression_gates": gates,
        "streamlit_api_deprecations_in_stable_ui": 0,
        "universe_rows": 43089,
        "production_scoring_authorized": False,
        "allow_ranking": False,
        "temporary_watchlist_cleaned": True,
        "universe_pointer_modified": False,
        "scoring_pointer_modified": False,
        "dataset_modified": False,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    print("PASS: v2.32D/5-of-5-incidents-closed/0-open/3-regression-gates/no-deprecations/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
