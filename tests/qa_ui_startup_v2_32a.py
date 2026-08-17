#!/usr/bin/env python3
"""Clean-install and real Streamlit startup gate for v2.32A."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def free_port() -> int:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


def wait_for_health(port: int, process: subprocess.Popen[str]) -> tuple[int, str, float]:
    started = time.perf_counter()
    url = f"http://127.0.0.1:{port}/_stcore/health"
    last_error: Exception | None = None
    for _ in range(80):
        if process.poll() is not None:
            raise AssertionError(f"Streamlit exited before health check (code {process.returncode})")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                body = response.read().decode("utf-8")
                return response.status, body, time.perf_counter() - started
        except Exception as exc:  # server startup is intentionally retried
            last_error = exc
            time.sleep(0.25)
    raise AssertionError(f"Streamlit health endpoint unavailable: {last_error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    from scripts.verify_local_ui_install_v2_29a import verify
    from src.ui_v2_28.adapters import build_app_state
    from src.ui_v2_28.catalog import load_catalog, query_catalog

    universe_pointer_path = ROOT / "outputs/full_universe_source_acquisition/current_operational_universe_pointer.json"
    scoring_pointer_path = ROOT / "outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json"
    universe_pointer_before = sha256(universe_pointer_path)
    scoring_pointer_before = sha256(scoring_pointer_path)

    install_report = verify(ROOT, skip_dataset_hash=False, check_dependencies=True)
    assert install_report["status"] == "PASS", install_report
    pointer = json.loads(universe_pointer_path.read_text(encoding="utf-8"))
    dataset = ROOT / str(pointer["current_dataset"]).replace("\\", "/")

    load_started = time.perf_counter()
    rows = load_catalog(dataset)
    load_seconds = time.perf_counter() - load_started
    identities = {row["identity_key"] for row in rows}
    nse_rows = query_catalog(rows, filters={"provider": ["nse_india"]}, page_size=1).total
    state = build_app_state(ROOT)

    assert len(rows) == 43089
    assert len(identities) == 43089
    assert nse_rows == 2013
    assert state.maintenance.providers_complete == 14
    assert state.maintenance.missing_rows == 0
    assert state.scoring.allow_ranking is False

    port = free_port()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app_v2_28.py",
        "--server.headless=true",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--browser.gatherUsageStats=false",
    ]
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        health_status, health_body, startup_seconds = wait_for_health(port, process)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    assert health_status == 200
    assert health_body.strip() == "ok"
    assert sha256(universe_pointer_path) == universe_pointer_before
    assert sha256(scoring_pointer_path) == scoring_pointer_before

    report = {
        "phase": "v2.32A",
        "status": "PASS",
        "python": sys.version.split()[0],
        "streamlit_health": health_body.strip(),
        "streamlit_http_status": health_status,
        "startup_seconds": round(startup_seconds, 3),
        "catalog_load_seconds": round(load_seconds, 3),
        "universe_rows": len(rows),
        "unique_identities": len(identities),
        "providers_complete": state.maintenance.providers_complete,
        "providers_expected": state.maintenance.providers_expected,
        "missing_provider_rows": state.maintenance.missing_rows,
        "nse_rows": nse_rows,
        "production_scoring_authorized": False,
        "allow_ranking": state.scoring.allow_ranking,
        "universe_pointer_modified": False,
        "scoring_pointer_modified": False,
        "dataset_modified": False,
        "checks": {
            "clean_install_contract": "PASS",
            "dependencies": "PASS",
            "dataset_hash": "PASS",
            "catalog_load": "PASS",
            "identity_uniqueness": "PASS",
            "provider_coverage": "PASS",
            "streamlit_process": "PASS",
            "http_health": "PASS",
            "scoring_fail_closed": "PASS",
            "pointer_invariance": "PASS",
        },
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    print("PASS: v2.32A/clean-install/real-startup/http-health/43089/14-of-14/fail-closed/pointers-unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
