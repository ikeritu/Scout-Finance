from __future__ import annotations

import csv
import json
import re
import zipfile
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path


VERSION = "v2.14D2"
PHASE = "Deutsche Boerse Xetra Header Diagnostic"
PHASE_TYPE = "validation-diagnostic-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "deutsche_boerse_xetra_v2_14c" / "datasets"

JSON_OUT = OUTPUT_DIR / "deutsche_boerse_xetra_header_diagnostic_v2_14d2.json"
CSV_OUT = OUTPUT_DIR / "deutsche_boerse_xetra_header_diagnostic_v2_14d2.csv"
SAMPLE_OUT = OUTPUT_DIR / "deutsche_boerse_xetra_header_samples_v2_14d2.csv"
MD_OUT = OUTPUT_DIR / "deutsche_boerse_xetra_header_diagnostic_v2_14d2.md"


DELIMITERS = [",", ";", "\t", "|"]

HEADER_KEYWORDS = {
    "isin": 8,
    "mnemonic": 7,
    "instrumentid": 7,
    "instrument id": 7,
    "instrument": 4,
    "security": 4,
    "product": 3,
    "symbol": 4,
    "ticker": 4,
    "name": 3,
    "currency": 3,
    "market": 2,
    "segment": 2,
    "type": 3,
    "subtype": 3,
    "wkn": 4,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [JSON_OUT, CSV_OUT, SAMPLE_OUT, MD_OUT]
    existing = [str(p) for p in guarded if p.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.14D2 outputs:\n"
            + "\n".join(existing)
        )


def decode_bytes(data: bytes) -> str:
    candidates = ["utf-8-sig", "utf-8", "cp1252", "latin-1", "utf-16"]
    best_text = ""
    best_score = -10**9

    for enc in candidates:
        try:
            text = data.decode(enc, errors="replace")
            score = len(text) - text.count("\ufffd") * 100
            if score > best_score:
                best_text = text
                best_score = score
        except Exception:
            pass

    return best_text


def split_csv_line(line: str, delimiter: str) -> list[str]:
    try:
        return next(csv.reader([line], delimiter=delimiter))
    except Exception:
        return []


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\ufeff", "")).strip()


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def score_header(columns: list[str]) -> int:
    cleaned = [normalize_header(c) for c in columns]
    compacted = [compact(c) for c in cleaned]
    joined = " ".join(c.lower() for c in cleaned)
    joined_compact = " ".join(compacted)

    score = 0

    if len(cleaned) >= 3:
        score += 2
    if len(cleaned) >= 5:
        score += 4
    if len(cleaned) >= 8:
        score += 4

    for keyword, weight in HEADER_KEYWORDS.items():
        k = compact(keyword)
        if keyword in joined or k in joined_compact:
            score += weight

    first = cleaned[0].lower() if cleaned else ""
    if first in {"market:", "market", "date:", "date", "file:", "file"} and len(cleaned) <= 3:
        score -= 20

    if len(set(compacted)) < max(1, len(compacted) // 2):
        score -= 5

    return score


def find_best_header(lines: list[str]) -> dict:
    best = {
        "score": -10**9,
        "line_index": -1,
        "delimiter": "",
        "columns": [],
        "line_text": "",
    }

    max_lines = min(len(lines), 120)

    for idx in range(max_lines):
        line = lines[idx]
        if not line.strip():
            continue

        for delimiter in DELIMITERS:
            cols = [normalize_header(c) for c in split_csv_line(line, delimiter)]
            cols = [c for c in cols if c != ""]
            if not cols:
                continue

            score = score_header(cols)

            if score > best["score"]:
                best = {
                    "score": score,
                    "line_index": idx,
                    "delimiter": delimiter,
                    "columns": cols,
                    "line_text": line[:500],
                }

    return best


def parse_from_header(lines: list[str], header_info: dict) -> tuple[list[str], list[dict]]:
    idx = header_info["line_index"]
    delimiter = header_info["delimiter"]

    if idx < 0 or not delimiter:
        return [], []

    text = "\n".join(lines[idx:])
    reader = csv.DictReader(StringIO(text), delimiter=delimiter)

    if not reader.fieldnames:
        return [], []

    headers = [normalize_header(h) for h in reader.fieldnames]
    rows = []

    for raw in reader:
        row = {}
        for original, clean in zip(reader.fieldnames, headers):
            row[clean] = str(raw.get(original, "") or "").strip()
        rows.append(row)

    return headers, rows


def find_col(headers: list[str], options: list[str]) -> str:
    for h in headers:
        low = h.lower()
        cmp = compact(h)
        for opt in options:
            if opt.lower() in low or compact(opt) in cmp:
                return h
    return ""


def inspect_payload(source_file: Path, member: str, data: bytes) -> tuple[dict, list[dict]]:
    text = decode_bytes(data)
    lines = text.splitlines()
    header = find_best_header(lines)
    headers, rows = parse_from_header(lines, header)

    isin_col = find_col(headers, ["isin"])
    mnemonic_col = find_col(headers, ["mnemonic", "symbol", "ticker"])
    instrument_id_col = find_col(headers, ["instrumentid", "instrument id"])
    name_col = find_col(headers, ["instrument name", "security name", "product name", "name", "description"])
    type_col = find_col(headers, ["security type", "securitytype", "instrument type", "product type", "security subtype", "subtype", "asset class", "category"])

    def val(row: dict, col: str) -> str:
        return str(row.get(col, "") or "").strip()

    row_count = len(rows)
    rows_with_isin = sum(1 for r in rows if val(r, isin_col)) if isin_col else 0
    rows_with_mnemonic = sum(1 for r in rows if val(r, mnemonic_col)) if mnemonic_col else 0
    rows_with_instrument_id = sum(1 for r in rows if val(r, instrument_id_col)) if instrument_id_col else 0
    rows_with_name = sum(1 for r in rows if val(r, name_col)) if name_col else 0
    rows_with_type = sum(1 for r in rows if val(r, type_col)) if type_col else 0

    samples = []
    for r in rows[:25]:
        samples.append(
            {
                "source_file": str(source_file),
                "member": member,
                "isin": val(r, isin_col),
                "mnemonic": val(r, mnemonic_col),
                "instrument_id": val(r, instrument_id_col),
                "name": val(r, name_col),
                "type_text": val(r, type_col),
            }
        )

    result = {
        "source_file": str(source_file),
        "member": member,
        "header_score": header["score"],
        "header_line_index_zero_based": header["line_index"],
        "header_line_number_one_based": header["line_index"] + 1 if header["line_index"] >= 0 else "",
        "delimiter": repr(header["delimiter"]),
        "header_preview": " | ".join(header["columns"][:80]),
        "detected_headers_count": len(headers),
        "row_count_from_detected_header": row_count,
        "isin_col": isin_col,
        "mnemonic_col": mnemonic_col,
        "instrument_id_col": instrument_id_col,
        "name_col": name_col,
        "type_col": type_col,
        "rows_with_isin": rows_with_isin,
        "rows_with_mnemonic": rows_with_mnemonic,
        "rows_with_instrument_id": rows_with_instrument_id,
        "rows_with_name": rows_with_name,
        "rows_with_type": rows_with_type,
        "first_detected_header_line": header["line_text"],
    }

    return result, samples


def iter_payloads(path: Path) -> list[tuple[str, bytes]]:
    if path.suffix.lower() == ".zip":
        payloads = []
        with zipfile.ZipFile(path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                suffix = Path(info.filename).suffix.lower()
                if suffix in {".csv", ".txt", ".dat", ".tsv"}:
                    payloads.append((info.filename, zf.read(info)))
        return payloads

    return [(path.name, path.read_bytes())]


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    no_overwrite_guard()

    if not RAW_DIR.exists():
        raise SystemExit(f"Missing raw dataset directory: {RAW_DIR}")

    files = [
        p for p in RAW_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".csv", ".txt", ".dat", ".tsv", ".zip"}
    ]

    diagnostic_rows = []
    sample_rows = []

    for path in files:
        for member, data in iter_payloads(path):
            result, samples = inspect_payload(path, member, data)
            diagnostic_rows.append(result)
            sample_rows.extend(samples)

    main_candidates = [
        r for r in diagnostic_rows
        if "alltradable" in compact(r["member"]) or "alltradable" in compact(r["source_file"])
    ]

    main_ok = any(
        int(r["row_count_from_detected_header"]) > 0
        and (
            int(r["rows_with_isin"]) > 0
            or int(r["rows_with_mnemonic"]) > 0
            or int(r["rows_with_instrument_id"]) > 0
        )
        for r in main_candidates
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "generated_at_utc": utc_now(),
        "status": "DEUTSCHE_BOERSE_XETRA_HEADER_DIAGNOSTIC_COMPLETED",
        "main_all_tradable_header_detected_with_identifiers": main_ok,
        "diagnostic_payloads": len(diagnostic_rows),
        "main_all_tradable_candidates": main_candidates,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed_for_diagnostic": True,
            "normalization_performed": False,
            "net_new_filtering_finalized": False,
            "expanded_universe_rebuilt": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_step": (
            "Create corrected v2.14D validation parser using detected header line"
            if main_ok
            else "Manual inspection required before corrected v2.14D validation"
        ),
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    write_csv(
        CSV_OUT,
        diagnostic_rows,
        [
            "source_file",
            "member",
            "header_score",
            "header_line_index_zero_based",
            "header_line_number_one_based",
            "delimiter",
            "header_preview",
            "detected_headers_count",
            "row_count_from_detected_header",
            "isin_col",
            "mnemonic_col",
            "instrument_id_col",
            "name_col",
            "type_col",
            "rows_with_isin",
            "rows_with_mnemonic",
            "rows_with_instrument_id",
            "rows_with_name",
            "rows_with_type",
            "first_detected_header_line",
        ],
    )

    write_csv(
        SAMPLE_OUT,
        sample_rows,
        [
            "source_file",
            "member",
            "isin",
            "mnemonic",
            "instrument_id",
            "name",
            "type_text",
        ],
    )

    main_lines = "\n".join(
        f"- `{r['member']}` header line {r['header_line_number_one_based']} "
        f"rows={r['row_count_from_detected_header']} "
        f"isin={r['rows_with_isin']} mnemonic={r['rows_with_mnemonic']} "
        f"instrument_id={r['rows_with_instrument_id']} type={r['rows_with_type']}"
        for r in main_candidates
    )

    MD_OUT.write_text(
        f"""# {VERSION} - {PHASE}

Status: **DEUTSCHE_BOERSE_XETRA_HEADER_DIAGNOSTIC_COMPLETED**

Main all-tradable header detected with identifiers: **{str(main_ok).lower()}**

## Main all-tradable candidates

{main_lines if main_lines else "- No main all-tradable candidate detected"}

## Guards

- Network download performed: false
- Raw files downloaded: false
- Raw files modified after write: false
- Workbook/CSV parsed for diagnostic: true
- Normalization performed: false
- Final net-new filtering finalized: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Recommended next step

{payload["recommended_next_step"]}
""",
        encoding="utf-8",
    )

    print("v2.14D2 header diagnostic completed.")
    print(f"- json: {JSON_OUT}")
    print(f"- csv: {CSV_OUT}")
    print(f"- samples: {SAMPLE_OUT}")
    print(f"- report: {MD_OUT}")
    print("")
    print("STATUS:")
    print(f"- main_all_tradable_header_detected_with_identifiers: {main_ok}")
    print(f"- diagnostic_payloads: {len(diagnostic_rows)}")
    print(f"- recommended_next_step: {payload['recommended_next_step']}")


if __name__ == "__main__":
    main()
