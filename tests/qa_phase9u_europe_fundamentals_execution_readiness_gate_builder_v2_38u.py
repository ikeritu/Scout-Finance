#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_fundamentals_execution_readiness_gate_v2_38u.py"
FIXTURE_RUNNER = ROOT / "scripts/run_europe_fundamentals_provider_pilot_test_fixture_v2_38u.py"


def run(env_overrides: dict[str, str]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        r_summary = root / "r.json"
        s_summary = root / "s.json"
        t_summary = root / "t.json"
        out = root / "out"
        r_summary.write_text(json.dumps({"provider_pilot_assets_actual": 10}), encoding="utf-8")
        s_summary.write_text(json.dumps({"official_filings_review_assets_actual": 5, "ready_for_future_official_execution_assets": 0}), encoding="utf-8")
        t_summary.write_text(json.dumps({"manual_review_pack_assets_actual": 3, "ready_for_future_manual_review_execution_assets": 0}), encoding="utf-8")
        env = dict(os.environ)
        env.update(env_overrides)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-provider-pilot-summary", str(r_summary), "--input-official-filings-summary", str(s_summary), "--input-manual-review-summary", str(t_summary), "--output-dir", str(out)],
            cwd=ROOT, text=True, capture_output=True, env=env,
        )
        assert result.returncode == 0, result.stderr
        matrix_path = out / "europe_fundamentals_execution_readiness_matrix_v2_38u.csv"
        import csv
        with matrix_path.open(encoding="utf-8", newline="") as f:
            matrix = list(csv.DictReader(f))
        summary = json.loads((out / "europe_fundamentals_execution_readiness_summary_v2_38u.json").read_text(encoding="utf-8"))
        return {"matrix": matrix, "summary": summary}


def main() -> int:
    env_no_key = dict(os.environ)
    env_no_key.pop("EODHD_API_KEY", None)

    # Scenario 1: nothing ready -- no script, no credential, prerequisites incomplete.
    result = run({"EODHD_API_KEY": ""})
    by_route = {row["route"]: row for row in result["matrix"]}
    assert by_route["provider_pilot"]["readiness_status"] == "NOT_READY"
    assert "credential_missing" in by_route["provider_pilot"]["blockers"]
    assert "automation_script_not_implemented" in by_route["provider_pilot"]["blockers"]
    assert by_route["official_filings_review"]["readiness_status"] == "NOT_READY"
    assert "official_filings_review_prerequisite_incomplete" in by_route["official_filings_review"]["blockers"]
    assert by_route["manual_review"]["readiness_status"] == "NOT_READY"
    assert "manual_review_prerequisite_incomplete" in by_route["manual_review"]["blockers"]
    assert by_route["manual_review"]["automation_script_status"] == "NOT_APPLICABLE_HUMAN_PROCESS"
    assert "automation_script_not_implemented" not in by_route["manual_review"]["blockers"]
    assert result["summary"]["status"] == "EUROPE_FUNDAMENTALS_EXECUTION_NOT_READY_PENDING_PREREQUISITES"
    assert result["summary"]["routes_ready"] == 0
    # the actual credential value must never leak into any output
    assert "EODHD_API_KEY" not in json.dumps(result["matrix"]) or all("=" not in v for v in json.dumps(result["matrix"]))

    # Scenario 2: provider_pilot becomes READY once its script exists and its credential is set.
    FIXTURE_RUNNER.write_text("# temporary QA fixture, deleted by the test\n", encoding="utf-8")
    try:
        result2 = run({"EODHD_API_KEY": "fixture-not-a-real-key"})
        by_route2 = {row["route"]: row for row in result2["matrix"]}
        assert by_route2["provider_pilot"]["readiness_status"] == "READY"
        assert by_route2["provider_pilot"]["blockers"] == ""
        assert by_route2["provider_pilot"]["credential_present"] == "true"
        raw = json.dumps(result2, sort_keys=True)
        assert "fixture-not-a-real-key" not in raw
    finally:
        FIXTURE_RUNNER.unlink(missing_ok=True)

    print("PASS: v2.38U/builder/offline/per-route-readiness/no-credential-leak")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
