#!/usr/bin/env python3
"""Block 9AV: resolve identity for the 25 census rows v2.38N could never
even classify -- COUNTRY_EXCHANGE_MISMATCH_REVIEW -- because their country
tag (BG/KY/LI/LU/MT) conflicted with their mapped exchange (XETR/DE) and
were routed to manual review before v2.38Q ever built the 689-asset
in-scope matrix. Unlike the 689 already attacked, these 25 never flowed
into ANY later block: not v2.38AB's identity resolution, not any country
registry investigation. They also still carry the same Xetra market-
segment placeholder as company_name (LUX0, SDX1, NEWX, MDX1, SWI0, NAM0,
ITA0) that v2.38V/Z/AA/AB already fixed for 689 other assets -- this block
applies the identical fix to this leftover population instead of a new
method.

Real motivation: the user asked to attack "the fundamentals gap for the
remaining ~9,900 companies" -- that figure turned out not to correspond to
any real bucket in this project's data (checked: v2.38N's real leftover
buckets are 21,066 CBOE-secondary-listing rows, 88 non-European ADR/GDR
rows, and these 25 mismatch rows). Of the three, this is the only one that
is (a) genuinely never-attacked and (b) resolvable with the exact,
already-trusted method -- no new policy decision, no new provider.

Same fix as resolve_europe_full_identity_xetra_source_v2_38ab.py: resolve
directly against the local Deutsche Boerse Xetra "all tradable
instruments" reference file (already in git since v2.14c) by
Mnemonic -> Instrument/ISIN. No network, no OpenFIGI, no ticker-collision
risk (ISIN is globally unique). Fail-closed: an asset only resolves if its
ticker matches exactly one Mnemonic row with a single, non-conflicting
ISIN. The real country of incorporation is then read off the ISIN's own
2-letter prefix (ISO 6166), NOT from the census's already-confirmed-
unreliable country tag or the XETR exchange field -- this is what actually
answers the "manual validation required" question v2.38N left open.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT_RESOLUTION = ROOT / "outputs/full_universe_source_acquisition/v2_38n_europe_home_exchange_resolution/europe_home_exchange_resolution_v2_38n.csv"
XETRA_RAW = ROOT / "outputs/full_universe_source_acquisition/raw/deutsche_boerse_xetra_v2_14c/datasets/001_downloads_en_t7-xetr-allTradableInstruments.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38av_europe_mismatch_identity_resolution"
PHASE = "v2.38AV-europe-mismatch-identity-resolution-xetra-source"
TARGET_STATUS = "COUNTRY_EXCHANGE_MISMATCH_REVIEW"

MATRIX_FIELDS = [
    "asset_id", "ticker", "company_name_source_value", "census_country_tag",
    "resolved_company_name", "resolved_company_name_raw", "resolution_status",
    "resolution_reason", "isin", "isin_country_prefix", "real_home_country_guess",
    "source_row_hash", "credentials_used", "phase", "created_at_utc",
]
DENOMINATION_SUFFIX_RE = re.compile(r"\s*(LS|DL|EO|USD|EUR|SF)\s*[\-,.\d]+$")
SHARE_TYPE_SUFFIX_RE = re.compile(r"\s*(INHABER|INH|NOM|NAM|NA|O\.N)\.?$")

# ISO 6166 ISIN country prefix -> readable country name, for the handful of
# jurisdictions this specific leftover population turned out to touch
# (confirmed live below, never assumed in advance).
ISIN_PREFIX_COUNTRY = {
    "LU": "Luxembourg", "MT": "Malta", "BG": "Bulgaria", "LI": "Liechtenstein",
    "KY": "Cayman Islands", "DE": "Germany", "FR": "France", "NL": "Netherlands",
    "GB": "United Kingdom", "IE": "Ireland", "CH": "Switzerland", "IT": "Italy",
    "AT": "Austria", "ES": "Spain", "BE": "Belgium", "FI": "Finland", "SE": "Sweden",
    "DK": "Denmark", "US": "United States", "JE": "Jersey", "GG": "Guernsey",
    "VG": "British Virgin Islands", "CW": "Curacao", "BM": "Bermuda",
}


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
    cleaned = raw_instrument.strip()
    changed = True
    while changed:
        changed = False
        for pattern in (DENOMINATION_SUFFIX_RE, SHARE_TYPE_SUFFIX_RE):
            new_cleaned = pattern.sub("", cleaned).strip()
            if new_cleaned != cleaned:
                cleaned = new_cleaned
                changed = True
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


def select_target_rows(all_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [r for r in all_rows if r.get("resolution_status") == TARGET_STATUS]


def build(input_resolution: Path, xetra_raw: Path, output_dir: Path) -> dict[str, Any]:
    all_rows = read_csv(input_resolution)
    rows = select_target_rows(all_rows)
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
        isin = candidate.get("ISIN", "")
        matrix.append(_record(row, clean_company_name(raw_name), raw_name, "resolved", "exact_mnemonic_match_single_isin_in_xetra_reference_file", created_at, isin=isin))

    status_counts = {"resolved": sum(1 for r in matrix if r["resolution_status"] == "resolved"), "unresolved": sum(1 for r in matrix if r["resolution_status"] == "unresolved")}
    by_isin_country = Counter(r["real_home_country_guess"] for r in matrix if r["resolution_status"] == "resolved")
    by_census_tag = Counter(r["census_country_tag"] for r in matrix)
    mismatches_confirmed = sum(1 for r in matrix if r["resolution_status"] == "resolved" and r["isin_country_prefix"] != "DE")

    report = {
        "phase": PHASE, "target_status_from_v2_38n": TARGET_STATUS, "input_assets": len(rows),
        "resolved": status_counts["resolved"], "unresolved": status_counts["unresolved"],
        "unresolved_reasons": {reason: sum(1 for r in matrix if r["resolution_status"] == "unresolved" and r["resolution_reason"] == reason) for reason in sorted({r["resolution_reason"] for r in matrix if r["resolution_status"] == "unresolved"})},
        "resolved_by_real_isin_country": dict(sorted(by_isin_country.items(), key=lambda kv: -kv[1])),
        "input_by_census_country_tag": dict(sorted(by_census_tag.items(), key=lambda kv: -kv[1])),
        "confirmed_real_country_differs_from_de_home_exchange_flag": mismatches_confirmed,
        "network_used": False, "credentials_used": False, "resolution_method": "xetra_reference_file_mnemonic_to_isin_lookup_plus_isin_country_prefix",
        "note": "v2.38N flagged these 25 for manual review because census country tag (BG/KY/LI/LU/MT) conflicted with the XETR/DE exchange mapping. This block resolves the conflict directly: the ISIN prefix (not the census tag, not the exchange field) is the authoritative real country of incorporation.",
        "phase9c_authorized": False,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_mismatch_identity_resolution_matrix_v2_38av.csv", matrix, MATRIX_FIELDS)
    write_text(output_dir / "europe_mismatch_identity_resolution_summary_v2_38av.json", json.dumps(report, indent=2, sort_keys=True) + "\n")

    manifest = {
        "phase": PHASE, "inputs": {
            relative_or_absolute(input_resolution): {"bytes": input_resolution.stat().st_size, "sha256": sha(input_resolution)},
            relative_or_absolute(xetra_raw): {"bytes": xetra_raw.stat().st_size, "sha256": sha(xetra_raw)},
        },
        "outputs": {}, "scripts": ["scripts/resolve_europe_mismatch_identity_xetra_source_v2_38av.py"],
        "counts": {"resolved": report["resolved"], "unresolved": report["unresolved"]},
        "created_at_utc": created_at, "guardrails": {"network_used": False, "credentials_used": False, "phase9c_authorized": False},
    }
    for path in sorted(output_dir.glob("europe_mismatch_identity_resolution_*")):
        if path.name != "europe_mismatch_identity_resolution_manifest_v2_38av.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    write_text(output_dir / "europe_mismatch_identity_resolution_manifest_v2_38av.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def _record(row: dict[str, str], clean_name: str | None, raw_name: str | None, status: str, reason: str, created_at: str, isin: str = "") -> dict[str, str]:
    isin_prefix = isin[:2] if isin else ""
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name_source_value": row.get("company_name", ""),
        "census_country_tag": row.get("country", ""),
        "resolved_company_name": clean_name or "", "resolved_company_name_raw": raw_name or "", "resolution_status": status,
        "resolution_reason": reason, "isin": isin, "isin_country_prefix": isin_prefix,
        "real_home_country_guess": ISIN_PREFIX_COUNTRY.get(isin_prefix, isin_prefix or ""),
        "source_row_hash": row_hash(row), "credentials_used": "false", "phase": PHASE, "created_at_utc": created_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-resolution", type=Path, default=INPUT_RESOLUTION)
    parser.add_argument("--xetra-raw", type=Path, default=XETRA_RAW)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.input_resolution, args.xetra_raw, args.output_dir)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["unresolved"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
