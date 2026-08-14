#!/usr/bin/env python3
"""Offline verifier for the v2.26D rollback inventory."""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return max(sum(1 for _ in csv.reader(f)) - 1, 0)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--report", type=Path, default=Path("outputs/full_universe_source_acquisition/v2_26d_rollback_validation/rollback_validation_report.json"))
    args = ap.parse_args()
    report = json.loads((args.repo_root / args.report).read_text())
    failures = []
    for g in report["generations"]:
        p = args.repo_root / g["path"]
        if not p.is_file():
            failures.append(f'{g["role"]}: missing')
            continue
        rows, sha = data_rows(p), digest(p)
        if rows != g["rows"]: failures.append(f'{g["role"]}: rows {rows} != {g["rows"]}')
        if sha != g["sha256"]: failures.append(f'{g["role"]}: sha256 {sha} != {g["sha256"]}')
    if failures:
        print("\n".join(failures))
        return 1
    print("PASS: 3/3 generations match row counts and SHA-256 inventory")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
