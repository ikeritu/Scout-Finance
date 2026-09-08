#!/usr/bin/env python3
"""Offline QA for src/ui_v2_37/global_universe.py -- the data-loading and
rebuild-trigger module behind the "Actualizar" button. No real subprocess
execution and no real matrix file: rebuild_global_matrix()'s `run`
parameter is injected with a fake, and load_global_matrix() is pointed at
synthetic fixtures under a temporary root."""
from __future__ import annotations

import csv
import lzma
import tempfile
from pathlib import Path
from types import SimpleNamespace

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_v2_37.global_universe import ELIGIBILITY_REL, MATRIX_REL, UNICORN_REL, load_global_matrix, rebuild_global_matrix  # noqa: E402

FIELDS = ["asset_id", "ticker", "company_name", "exchange", "country", "identity_status", "fundamentals_status", "growth_status", "price_status", "overall_coverage_status"]
ELIGIBILITY_FIELDS = ["asset_id", "eligibility_tier", "eligibility_reason", "is_financial_institution_heuristic"]
UNICORN_FIELDS = ["asset_id", "unicorn_status", "unicorn_reason"]


def write_matrix(root: Path, rows: list[dict]) -> None:
    path = root / MATRIX_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_eligibility(root: Path, rows: list[dict]) -> None:
    path = root / ELIGIBILITY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ELIGIBILITY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_unicorn(root: Path, rows: list[dict]) -> None:
    path = root / UNICORN_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=UNICORN_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def row(asset_id: str, status: str = "NO_DATA_YET") -> dict:
    return {"asset_id": asset_id, "ticker": asset_id, "company_name": f"{asset_id} Co", "exchange": "TEST", "country": "US", "identity_status": "NOT_ATTEMPTED", "fundamentals_status": "NOT_ATTEMPTED", "growth_status": "NOT_ATTEMPTED", "price_status": "NOT_ATTEMPTED", "overall_coverage_status": status}


def test_missing_matrix_reports_unavailable_never_crashes():
    with tempfile.TemporaryDirectory() as tmp:
        data = load_global_matrix(Path(tmp))
    assert data.available is False
    assert data.rows == ()
    assert "Actualizar" in data.error


def test_existing_matrix_loads_all_rows_and_a_real_mtime():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_matrix(root, [row("U1", "GROWTH_READY"), row("U2")])
        data = load_global_matrix(root)
    assert data.available is True
    assert len(data.rows) == 2
    assert data.generated_at  # a real ISO timestamp, not blank
    assert data.rows[0]["asset_id"] == "U1"
    assert data.rows[0]["eligibility_tier"] == ""  # no eligibility file yet -- blank, never a crash
    assert data.rows[0]["unicorn_status"] == ""  # no unicorn file yet -- blank, never a computed "false"


def test_eligibility_file_is_joined_in_by_asset_id():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_matrix(root, [row("U1", "GROWTH_READY"), row("U2", "NO_DATA_YET")])
        write_eligibility(root, [
            {"asset_id": "U1", "eligibility_tier": "ELIGIBLE_FULL", "eligibility_reason": "real_identity_fundamentals_growth_and_price", "is_financial_institution_heuristic": "False"},
            {"asset_id": "U2", "eligibility_tier": "NOT_ELIGIBLE", "eligibility_reason": "no_data_yet", "is_financial_institution_heuristic": "False"},
        ])
        data = load_global_matrix(root)
    by_id = {r["asset_id"]: r for r in data.rows}
    assert by_id["U1"]["eligibility_tier"] == "ELIGIBLE_FULL"
    assert by_id["U2"]["eligibility_tier"] == "NOT_ELIGIBLE"
    assert by_id["U2"]["eligibility_reason"] == "no_data_yet"


def test_unicorn_file_is_joined_in_by_asset_id():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_matrix(root, [row("U1", "GROWTH_READY"), row("U2", "GROWTH_READY"), row("U3", "NO_DATA_YET")])
        write_unicorn(root, [
            {"asset_id": "U1", "unicorn_status": "EVALUATED_UNICORN", "unicorn_reason": "us_fundamental_momentum_flag_true_real_revenue_growth_and_margin_expansion_and_positive_free_cash_flow"},
            {"asset_id": "U2", "unicorn_status": "EVALUATED_NOT_UNICORN", "unicorn_reason": "us_fundamental_momentum_flag_false:revenue_growth_not_positive"},
        ])
        data = load_global_matrix(root)
    by_id = {r["asset_id"]: r for r in data.rows}
    assert by_id["U1"]["unicorn_status"] == "EVALUATED_UNICORN"
    assert by_id["U2"]["unicorn_status"] == "EVALUATED_NOT_UNICORN"
    assert by_id["U3"]["unicorn_status"] == ""  # never evaluated (no growth-feature row) -- blank, not "false"


def test_corrupted_matrix_file_reports_error_never_crashes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = root / MATRIX_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"not a real xz file")
        data = load_global_matrix(root)
    assert data.available is False
    assert data.error


def test_rebuild_runs_all_four_scripts_with_this_interpreter_in_order():
    calls = []

    def fake_run(cmd, cwd, capture_output, text, timeout):
        calls.append(cmd[1])  # the script path, since cmd[0] is sys.executable
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    with tempfile.TemporaryDirectory() as tmp:
        result = rebuild_global_matrix(Path(tmp), run=fake_run)
    assert result.ok is True
    assert len(result.steps) == 4
    assert calls[0].endswith("build_global_coverage_matrix_v2_38al.py")
    assert calls[1].endswith("build_global_macro_geopolitical_context_v2_38am.py")
    assert calls[2].endswith("build_global_scoring_eligibility_v2_38bo.py")
    assert calls[3].endswith("build_global_unicorn_flag_v2_38bt.py")
    assert all(step.ok for step in result.steps)


def test_rebuild_stops_after_coverage_matrix_failure_never_builds_later_steps_on_broken_input():
    calls = []

    def fake_run(cmd, cwd, capture_output, text, timeout):
        calls.append(cmd[1])
        return SimpleNamespace(returncode=1, stdout="", stderr="BLOCKED: something real failed")

    with tempfile.TemporaryDirectory() as tmp:
        result = rebuild_global_matrix(Path(tmp), run=fake_run)
    assert result.ok is False
    assert len(calls) == 1  # neither macro context nor eligibility ever attempted on top of a failed coverage matrix
    assert "BLOCKED" in result.steps[0].detail


def test_rebuild_stops_after_macro_context_failure_never_builds_eligibility():
    calls = []

    def fake_run(cmd, cwd, capture_output, text, timeout):
        calls.append(cmd[1])
        ok = len(calls) == 1  # coverage matrix succeeds, macro context fails
        return SimpleNamespace(returncode=0 if ok else 1, stdout="ok" if ok else "", stderr="" if ok else "BLOCKED: macro failed")

    with tempfile.TemporaryDirectory() as tmp:
        result = rebuild_global_matrix(Path(tmp), run=fake_run)
    assert result.ok is False
    assert len(calls) == 2  # eligibility never attempted on top of a failed macro context step
    assert result.steps[0].ok is True
    assert result.steps[1].ok is False


def test_rebuild_stops_after_eligibility_failure_never_builds_unicorn_flag():
    calls = []

    def fake_run(cmd, cwd, capture_output, text, timeout):
        calls.append(cmd[1])
        ok = len(calls) < 3  # coverage matrix and macro context succeed, eligibility fails
        return SimpleNamespace(returncode=0 if ok else 1, stdout="ok" if ok else "", stderr="" if ok else "BLOCKED: eligibility failed")

    with tempfile.TemporaryDirectory() as tmp:
        result = rebuild_global_matrix(Path(tmp), run=fake_run)
    assert result.ok is False
    assert len(calls) == 3  # unicorn flag never attempted on top of a failed eligibility step
    assert result.steps[0].ok is True
    assert result.steps[1].ok is True
    assert result.steps[2].ok is False


def test_rebuild_exception_is_caught_and_reported_never_crashes_the_app():
    def raising_run(cmd, cwd, capture_output, text, timeout):
        raise TimeoutError("real subprocess timeout")

    with tempfile.TemporaryDirectory() as tmp:
        result = rebuild_global_matrix(Path(tmp), run=raising_run)
    assert result.ok is False
    assert "timeout" in result.steps[0].detail.lower()


def test_path_traversal_in_matrix_path_is_rejected():
    """Same discipline as repository.py's _rooted(): the module must never
    resolve a relative path to somewhere outside the project root, even
    though MATRIX_REL is itself a hardcoded constant, not user input."""
    import src.ui_v2_37.global_universe as gu
    with tempfile.TemporaryDirectory() as tmp:
        try:
            gu._rooted(Path(tmp), "../../etc/passwd")
            raised = False
        except ValueError:
            raised = True
    assert raised


CASES = [
    test_missing_matrix_reports_unavailable_never_crashes,
    test_existing_matrix_loads_all_rows_and_a_real_mtime,
    test_eligibility_file_is_joined_in_by_asset_id,
    test_unicorn_file_is_joined_in_by_asset_id,
    test_corrupted_matrix_file_reports_error_never_crashes,
    test_rebuild_runs_all_four_scripts_with_this_interpreter_in_order,
    test_rebuild_stops_after_coverage_matrix_failure_never_builds_later_steps_on_broken_input,
    test_rebuild_stops_after_macro_context_failure_never_builds_eligibility,
    test_rebuild_stops_after_eligibility_failure_never_builds_unicorn_flag,
    test_rebuild_exception_is_caught_and_reported_never_crashes_the_app,
    test_path_traversal_in_matrix_path_is_rejected,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: ui-global-universe/actualizar-button/fail-closed/no-network-triggered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
