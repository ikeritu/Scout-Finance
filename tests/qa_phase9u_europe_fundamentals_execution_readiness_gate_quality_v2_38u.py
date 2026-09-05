#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_fundamentals_execution_readiness_gate_v2_38u.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38u_europe_fundamentals_execution_readiness_gate"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]", re.I)
ACTION_RE = re.compile(r"\b(buy|sell|hold|strong buy|recommendation|target price|undervalued|overvalued|expected return|guaranteed|will rise)\b", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def non_identity_text(row: dict[str, str]) -> str:
    identity = {"route", "route_phase", "assets_in_route"}
    return " ".join(value for key, value in row.items() if key not in identity)


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    matrix = rows(OUT / "europe_fundamentals_execution_readiness_matrix_v2_38u.csv")
    summary = json.loads((OUT / "europe_fundamentals_execution_readiness_summary_v2_38u.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "europe_fundamentals_execution_readiness_manifest_v2_38u.json").read_text(encoding="utf-8"))

    assert len(matrix) == 3
    assert {row["route"] for row in matrix} == {"provider_pilot", "official_filings_review", "manual_review"}
    assert summary["routes_assessed"] == 3
    assert summary["status"] in {"EUROPE_FUNDAMENTALS_EXECUTION_READY", "EUROPE_FUNDAMENTALS_EXECUTION_NOT_READY_PENDING_PREREQUISITES"}
    assert summary["routes_ready"] + summary["routes_not_ready"] == 3
    for key in ["network_used", "scraping_used", "api_used", "real_filings_downloaded", "real_fundamentals_present", "normalized_fundamentals_created", "scoring_created", "ranking_created", "recommendations_created", "phase9c_authorized"]:
        assert summary[key] is False

    by_route = {row["route"]: row for row in matrix}
    assert by_route["manual_review"]["execution_method"] == "human_manual_review"
    assert by_route["manual_review"]["automation_script_status"] == "NOT_APPLICABLE_HUMAN_PROCESS"
    assert all(row["real_fundamentals_downloaded"] == "false" and row["network_used_in_this_gate"] == "false" and row["phase9c_authorized"] == "false" for row in matrix)
    assert all(row["readiness_status"] in {"READY", "NOT_READY"} for row in matrix)
    assert all((row["readiness_status"] == "READY") == (row["blockers"] == "") for row in matrix)

    for row in matrix:
        assert not ACTION_RE.search(non_identity_text(row)), row["route"]
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    for path in OUT.glob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert not SECRET_RE.search(text), path
            assert "EODHD_API_KEY=" not in text  # the env var name may appear as a column value, but never as key=value
    print("PASS: v2.38U/quality/readiness-gate/no-credential-leak/no-network-no-advice")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
