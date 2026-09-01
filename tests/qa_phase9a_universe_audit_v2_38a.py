#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import lzma
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38a_global_universe_audit"


def main() -> int:
    schema = json.loads((ROOT / "schemas/global_universe_audit_record_v1.schema.json").read_text(encoding="utf-8"))
    with lzma.open(OUTPUT / "global_universe_audited_v2_38a.csv.xz", "rt", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 43089 == len({r["asset_id"] for r in rows})
    assert set(schema["required"]) == set(rows[0])
    for field in ("identity_status", "eligibility_status", "enrichment_readiness"):
        assert {r[field] for r in rows} <= set(schema["properties"][field]["enum"])
    assert all(r["audit_phase"] == "v2.38A" for r in rows)
    summary = json.loads((OUTPUT / "global_universe_summary_v2_38a.json").read_text(encoding="utf-8"))
    assert summary["canonical_rows"] == 43089 and summary["eligible_rows"] == 21165
    assert summary["missingness"]["mic"] == 23167
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        for target in (first, second):
            subprocess.run([sys.executable, str(ROOT / "scripts/audit_global_universe_v2_38a.py"), "--output", target], cwd=ROOT, check=True, capture_output=True, text=True)
        names = [p.name for p in Path(first).iterdir()]
        assert set(names) == {p.name for p in Path(second).iterdir()}
        assert all(
            hashlib.sha256((Path(first) / name).read_bytes()).digest() == hashlib.sha256((Path(second) / name).read_bytes()).digest()
            for name in names
        )
    print("PASS: v2.38A/audit/43089/schema/identity/missingness/deterministic-fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
