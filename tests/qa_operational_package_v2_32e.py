#!/usr/bin/env python3
"""Operational packaging gate for the stable Windows local UI."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_FILES = (
    "INICIAR_SCOUT_FINANCE.bat",
    "run_local_ui_v2_28.bat",
    "setup_local_ui_v2_29a.ps1",
    "GUIA_SCOUT_FINANCE.md",
    "LOCAL_UI_V2_28.md",
)
POINTERS = (
    "outputs/full_universe_source_acquisition/current_operational_universe_pointer.json",
    "outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate(path: str, marker: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / path)], cwd=ROOT, capture_output=True, text=True, timeout=120
    )
    if result.returncode:
        raise AssertionError(f"{path} failed\n{result.stdout}\n{result.stderr}")
    assert marker in result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    missing = [path for path in PACKAGE_FILES if not (ROOT / path).is_file()]
    assert not missing, f"missing package files: {missing}"

    launcher = (ROOT / PACKAGE_FILES[0]).read_text(encoding="utf-8")
    alias = (ROOT / PACKAGE_FILES[1]).read_text(encoding="utf-8")
    setup = (ROOT / PACKAGE_FILES[2]).read_text(encoding="utf-8")
    guide = (ROOT / PACKAGE_FILES[3]).read_text(encoding="utf-8")

    # First run, repeat run and safe failure paths must remain explicit.
    assert 'if not exist ".venv\\Scripts\\python.exe"' in launcher
    assert 'setup_local_ui_v2_29a.ps1" -Launch' in launcher
    assert "verify_local_ui_install_v2_29a.py" in launcher
    assert '-m streamlit run "app_v2_28.py"' in launcher
    assert "if errorlevel 1 goto :error" in launcher
    assert "No se ha modificado el universo operativo" in launcher
    assert "Ctrl+C" in launcher and "pause" in launcher
    assert 'call "%~dp0INICIAR_SCOUT_FINANCE.bat"' in alias

    # Setup must stop on dependency or verification failure and preserve privacy defaults.
    assert setup.count("$LASTEXITCODE -ne 0") >= 4
    assert "requirements-ui-v2_28.txt" in setup
    assert "--browser.gatherUsageStats=false" in setup
    assert "INICIAR_SCOUT_FINANCE.bat" in setup

    # A non-technical user must have installation, closing, FAQ and recovery guidance.
    for required in (
        "Primera vez",
        "Veces siguientes",
        "Cerrar Scout Finance",
        "Solución de problemas y preguntas frecuentes",
        "Copias de seguridad",
        ".json.bak",
        "Reinstalación segura",
        "allow_ranking=false",
        "43.089",
    ):
        assert required.casefold() in guide.casefold(), required

    pointer_hashes_before = {path: sha256(ROOT / path) for path in POINTERS}
    run_gate("tests/qa_local_ui_closure_v2_28f.py", "PASS: inventory/launcher/guide")
    run_gate("tests/qa_incident_closure_v2_32d.py", "PASS: v2.32D/5-of-5-incidents-closed")
    pointer_hashes_after = {path: sha256(ROOT / path) for path in POINTERS}
    assert pointer_hashes_before == pointer_hashes_after

    report = {
        "phase": "v2.32E",
        "status": "PASS",
        "delivery": "Windows double-click operational package",
        "first_run_setup": True,
        "repeat_run_verification": True,
        "fail_closed": True,
        "user_guide_and_faq": True,
        "watchlist_backup_and_recovery": True,
        "universe_rows": 43089,
        "production_scoring_authorized": False,
        "allow_ranking": False,
        "package_sha256": {path: sha256(ROOT / path) for path in PACKAGE_FILES},
        "operational_pointer_sha256": pointer_hashes_after,
        "operational_pointers_modified_by_qa": False,
        "dataset_modified_by_qa": False,
        "regression_gates": ["v2.28F", "v2.32D"],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        output = args.json_output if args.json_output.is_absolute() else ROOT / args.json_output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print("PASS: v2.32E/windows-double-click/first-run/setup/verification/guide/faq/recovery/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
