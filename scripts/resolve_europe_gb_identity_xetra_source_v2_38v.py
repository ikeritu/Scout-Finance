#!/usr/bin/env python3
"""Block 9V correction: resolve real company identity for the 40 GB
official-filings-review assets using the authoritative source directly --
the local Deutsche Boerse Xetra "all tradable instruments" reference file
(outputs/full_universe_source_acquisition/raw/deutsche_boerse_xetra_v2_14c/),
already downloaded in an earlier phase and already tracked in git.

This supersedes the OpenFIGI ticker-based resolver
(resolve_europe_gb_identity_v2_38v.py). That approach treated each asset's
"ticker" field as if it were a real LSE ticker and searched for it on the
London market. It is not: the ticker field is actually Xetra's own
internal cross-listing mnemonic for a foreign (UK) security -- unrelated
to that company's real home-market ticker. Confirmed with two real,
serious consequences: the mnemonic "SCT" (assigned by Xetra to SSE PLC's
cross-listing) coincidentally collided with SOFTCAT PLC's real, unrelated
LSE ticker, and "BMT" (Xetra's mnemonic for British American Tobacco)
collided with BRAIME's real LSE ticker. Both were accepted by the old
resolver's fail-closed exact-match logic because the match genuinely was
exact and unambiguous -- just for the wrong company, because the input
string itself was never a real ticker for the intended company.

The fix: the raw Xetra file's own "Instrument" and "ISIN" columns give
the real company identity directly, keyed by the exact same "Mnemonic"
value already stored as this project's "ticker" field for these assets --
no network call, no guessing, no ticker-collision risk (ISIN is globally
unique). Fail-closed: an asset only resolves if its ticker matches
exactly one Mnemonic row with a single, non-conflicting ISIN.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38s_europe_official_filings_review/europe_official_filings_review_matrix_v2_38s.csv"
XETRA_RAW = ROOT / "outputs/full_universe_source_acquisition/raw/deutsche_boerse_xetra_v2_14c/datasets/001_downloads_en_t7-xetr-allTradableInstruments.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38v_europe_gb_identity_resolution"
PHASE = "v2.38V-europe-gb-identity-resolution-xetra-source-correction"
JURISDICTION_FILTER = "GB"

MATRIX_FIELDS = [
    "asset_id", "ticker", "company_name_source_value", "resolved_company_name",
    "resolved_company_name_raw", "resolution_status", "resolution_reason", "isin",
    "home_mic", "home_country", "source_row_hash", "credentials_used", "phase", "created_at_utc",
]
DENOMINATION_SUFFIX_RE = re.compile(r"\s*(LS|DL|EO|USD|EUR)[\-,.\d]+$")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_hash(row: dict[str, str]) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def clean_company_name(raw_instrument: str) -> str:
    """Strip the trailing denomination/par-value notation Xetra appends to
    every instrument name (e.g. 'DIAGEO PLC LS-,28935185' -> 'DIAGEO PLC').
    This is presentation cleanup only -- the raw value is always kept
    alongside it, never discarded."""
    cleaned = DENOMINATION_SUFFIX_RE.sub("", raw_instrument).strip()
    return cleaned or raw_instrument.strip()


def load_xetra_index(path: Path) -> dict[str, list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        lines = f.readlines()
    header = lines[2].strip().split(";")
    reader = csv.DictReader(lines[2:], fieldnames=header, delimiter=";")
    index: dict[str, list[dict[str, str]]] = {}
    for row in reader:
        mnemonic = row.get("Mnemonic", "")
        if not mnemonic:
            continue
        index.setdefault(mnemonic, []).append(row)
    return index


def build(input_matrix: Path, xetra_raw: Path, output_dir: Path) -> dict[str, Any]:
    rows = [r for r in read_csv(input_matrix) if r.get("jurisdiction_code") == JURISDICTION_FILTER]
    xetra_index = load_xetra_index(xetra_raw)
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    matrix = []
    for row in rows:
        ticker = row["ticker"]
        candidates = xetra_index.get(ticker, [])
        distinct_isins = {c.get("ISIN", "") for c in candidates}
        if not candidates:
            matrix.append(_record(row, None, None, "unresolved", "mnemonic_not_found_in_xetra_reference_file", created_at))
            continue
        if len(distinct_isins) > 1:
            matrix.append(_record(row, None, None, "unresolved", "ambiguous_multiple_distinct_isins_for_mnemonic", created_at))
            continue
        candidate = candidates[0]
        raw_name = candidate.get("Instrument", "")
        matrix.append(_record(row, clean_company_name(raw_name), raw_name, "resolved", "exact_mnemonic_match_single_isin_in_xetra_reference_file", created_at, isin=candidate.get("ISIN", "")))

    status_counts = {"resolved": sum(1 for r in matrix if r["resolution_status"] == "resolved"), "unresolved": sum(1 for r in matrix if r["resolution_status"] == "unresolved")}
    report = {
        "phase": PHASE, "input_assets": len(rows), "resolved": status_counts["resolved"], "unresolved": status_counts["unresolved"],
        "unresolved_reasons": {reason: sum(1 for r in matrix if r["resolution_status"] == "unresolved" and r["resolution_reason"] == reason) for reason in sorted({r["resolution_reason"] for r in matrix if r["resolution_status"] == "unresolved"})},
        "network_used": False, "credentials_used": False, "resolution_method": "xetra_reference_file_mnemonic_to_isin_lookup",
        "supersedes": "resolve_europe_gb_identity_v2_38v.py (OpenFIGI ticker-based, superseded due to two confirmed Xetra-mnemonic/LSE-ticker collisions -- see module docstring)",
        "phase9c_authorized": False,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_gb_identity_resolution_xetra_source_matrix_v2_38v.csv", matrix, MATRIX_FIELDS)
    write_text(output_dir / "europe_gb_identity_resolution_xetra_source_summary_v2_38v.json", json.dumps(report, indent=2, sort_keys=True) + "\n")

    manifest = {
        "phase": PHASE, "inputs": {
            relative_or_absolute(input_matrix): {"bytes": input_matrix.stat().st_size, "sha256": sha(input_matrix)},
            relative_or_absolute(xetra_raw): {"bytes": xetra_raw.stat().st_size, "sha256": sha(xetra_raw)},
        },
        "outputs": {}, "scripts": ["scripts/resolve_europe_gb_identity_xetra_source_v2_38v.py"],
        "counts": {"resolved": report["resolved"], "unresolved": report["unresolved"]},
        "created_at_utc": created_at, "guardrails": {"network_used": False, "credentials_used": False, "phase9c_authorized": False},
    }
    for path in sorted(output_dir.glob("europe_gb_identity_resolution_xetra_source_*")):
        if path.name != "europe_gb_identity_resolution_xetra_source_manifest_v2_38v.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    write_text(output_dir / "europe_gb_identity_resolution_xetra_source_manifest_v2_38v.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def _record(row: dict[str, str], clean_name: str | None, raw_name: str | None, status: str, reason: str, created_at: str, isin: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name_source_value": row.get("company_name", ""),
        "resolved_company_name": clean_name or "", "resolved_company_name_raw": raw_name or "", "resolution_status": status,
        "resolution_reason": reason, "isin": isin, "home_mic": row.get("mic", ""), "home_country": row.get("country", ""),
        "source_row_hash": row_hash(row), "credentials_used": "false", "phase": PHASE, "created_at_utc": created_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--xetra-raw", type=Path, default=XETRA_RAW)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.input_matrix, args.xetra_raw, args.output_dir)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["unresolved"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
