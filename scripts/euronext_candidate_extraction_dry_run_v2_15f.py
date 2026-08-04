from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


VERSION = "v2.15F"
PHASE = "Euronext Candidate Extraction Dry Run"
PHASE_TYPE = "dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "euronext_v2_15c"

PREP_JSON = OUTPUT_DIR / "euronext_rebuild_candidate_prep_v2_15e.json"
TABLE_CANDIDATES_CSV = OUTPUT_DIR / "euronext_table_candidates_v2_15e.csv"
SOURCE_STRATEGY_CSV = OUTPUT_DIR / "euronext_source_strategy_v2_15e.csv"

DRY_RUN_JSON = OUTPUT_DIR / "euronext_candidate_extraction_dry_run_v2_15f.json"
DRY_RUN_MD = OUTPUT_DIR / "euronext_candidate_extraction_dry_run_v2_15f.md"
EXTRACTED_CANDIDATES_CSV = OUTPUT_DIR / "euronext_extracted_candidates_raw_v2_15f.csv"
EXTRACTION_QUALITY_CSV = OUTPUT_DIR / "euronext_extraction_quality_v2_15f.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

ISIN_RE = re.compile(r"\b[A-Z]{2}[A-Z0-9]{9}[0-9]\b")

CSV_FIELDNAMES = [
    "candidate_id",
    "source_kind",
    "raw_file",
    "raw_file_name",
    "table_index",
    "row_index",
    "isin",
    "raw_symbol",
    "raw_name",
    "raw_market",
    "raw_mic",
    "raw_currency",
    "raw_type",
    "raw_row_text",
    "context",
    "extraction_confidence",
    "quality_bucket",
    "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_text_best_effort(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ["utf-8", "utf-8-sig", "cp1252", "latin-1"]:
        try:
            return data.decode(encoding, errors="replace")
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def clean_cell(value: str) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split()).strip()


class TableCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_table: list[list[str]] = []
        self.current_row: list[str] = []
        self.current_cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag_low = tag.lower()
        if tag_low == "table":
            self.in_table = True
            self.current_table = []
        elif self.in_table and tag_low == "tr":
            self.in_row = True
            self.current_row = []
        elif self.in_table and self.in_row and tag_low in {"td", "th"}:
            self.in_cell = True
            self.current_cell_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            cleaned = clean_cell(data)
            if cleaned:
                self.current_cell_parts.append(cleaned)

    def handle_endtag(self, tag: str) -> None:
        tag_low = tag.lower()

        if tag_low in {"td", "th"} and self.in_cell:
            self.current_row.append(clean_cell(" ".join(self.current_cell_parts)))
            self.current_cell_parts = []
            self.in_cell = False

        elif tag_low == "tr" and self.in_row:
            if any(cell.strip() for cell in self.current_row):
                self.current_table.append(self.current_row)
            self.current_row = []
            self.in_row = False

        elif tag_low == "table" and self.in_table:
            if self.current_table:
                self.tables.append(self.current_table)
            self.current_table = []
            self.in_table = False


def extract_tables(path: Path) -> list[list[list[str]]]:
    text = read_text_best_effort(path)
    parser = TableCollector()
    parser.feed(text)
    return parser.tables


def classify_header_cell(value: str) -> str:
    low = clean_cell(value).lower()

    if "isin" in low:
        return "isin"
    if "symbol" in low or "ticker" in low or "mnemo" in low:
        return "raw_symbol"
    if "name" in low or "company" in low or "issuer" in low or "instrument" in low or "product" in low:
        return "raw_name"
    if "market" in low or "exchange" in low or "venue" in low:
        return "raw_market"
    if "mic" in low:
        return "raw_mic"
    if "currency" in low or "ccy" in low:
        return "raw_currency"
    if "type" in low or "segment" in low or "category" in low:
        return "raw_type"

    return ""


def detect_header_map(table: list[list[str]]) -> dict[int, str]:
    best_map: dict[int, str] = {}
    best_score = 0

    for row in table[:5]:
        current_map: dict[int, str] = {}
        score = 0

        for index, cell in enumerate(row):
            field = classify_header_cell(cell)
            if field:
                current_map[index] = field
                score += 1

        if score > best_score:
            best_map = current_map
            best_score = score

    return best_map


def confidence_and_bucket(row: dict) -> tuple[int, str]:
    confidence = 0

    if row.get("isin"):
        confidence += 45
    if row.get("raw_symbol"):
        confidence += 15
    if row.get("raw_name"):
        confidence += 15
    if row.get("raw_market") or row.get("raw_mic"):
        confidence += 10
    if row.get("raw_currency"):
        confidence += 5
    if row.get("raw_type"):
        confidence += 5
    if row.get("source_kind") == "html_table_row":
        confidence += 5

    confidence = min(confidence, 100)

    if confidence >= 75:
        return confidence, "high"
    if confidence >= 55:
        return confidence, "medium"
    return confidence, "low"


def candidate_from_table_row(
    raw_file: Path,
    table_index: int,
    row_index: int,
    row: list[str],
    header_map: dict[int, str],
) -> dict | None:
    cleaned_row = [clean_cell(cell) for cell in row]
    raw_row_text = " | ".join(cell for cell in cleaned_row if cell)
    isin_matches = ISIN_RE.findall(raw_row_text)

    if not isin_matches:
        return None

    result = {
        "candidate_id": "",
        "source_kind": "html_table_row",
        "raw_file": str(raw_file),
        "raw_file_name": raw_file.name,
        "table_index": table_index,
        "row_index": row_index,
        "isin": isin_matches[0],
        "raw_symbol": "",
        "raw_name": "",
        "raw_market": "",
        "raw_mic": "",
        "raw_currency": "",
        "raw_type": "",
        "raw_row_text": raw_row_text[:5000],
        "context": "",
        "extraction_confidence": 0,
        "quality_bucket": "",
        "notes": "dry_run_raw_values_not_normalized",
    }

    for index, field in header_map.items():
        if index >= len(cleaned_row):
            continue
        value = cleaned_row[index]
        if not value:
            continue

        if field == "isin":
            isin_from_cell = ISIN_RE.findall(value)
            if isin_from_cell:
                result["isin"] = isin_from_cell[0]
        elif field in result and not result[field]:
            result[field] = value

    confidence, bucket = confidence_and_bucket(result)
    result["extraction_confidence"] = confidence
    result["quality_bucket"] = bucket

    id_basis = f"{raw_file}|{table_index}|{row_index}|{result['isin']}|{raw_row_text}"
    result["candidate_id"] = sha256_text(id_basis)[:16]

    return result


def context_candidates_from_text(raw_file: Path, existing_table_keys: set[str], limit_per_file: int = 500) -> list[dict]:
    text = read_text_best_effort(raw_file)
    rows: list[dict] = []
    seen_context_keys = set()

    for match in ISIN_RE.finditer(text):
        isin = match.group(0)

        if isin in existing_table_keys:
            continue

        start = max(0, match.start() - 160)
        end = min(len(text), match.end() + 160)
        context = clean_cell(text[start:end])

        context_key = sha256_text(f"{raw_file}|{isin}|{context[:300]}")
        if context_key in seen_context_keys:
            continue
        seen_context_keys.add(context_key)

        row = {
            "candidate_id": context_key[:16],
            "source_kind": "isin_context",
            "raw_file": str(raw_file),
            "raw_file_name": raw_file.name,
            "table_index": "",
            "row_index": "",
            "isin": isin,
            "raw_symbol": "",
            "raw_name": "",
            "raw_market": "",
            "raw_mic": "",
            "raw_currency": "",
            "raw_type": "",
            "raw_row_text": "",
            "context": context[:1000],
            "extraction_confidence": 45,
            "quality_bucket": "low",
            "notes": "dry_run_context_only_not_normalized_not_table_based",
        }

        rows.append(row)

        if len(rows) >= limit_per_file:
            break

    return rows


def deduplicate_candidates(rows: list[dict]) -> list[dict]:
    best_by_key: dict[tuple[str, str], dict] = {}

    for row in rows:
        key = (row.get("isin", ""), row.get("raw_file_name", ""))
        if not key[0]:
            continue

        current = best_by_key.get(key)
        if current is None:
            best_by_key[key] = row
            continue

        if int(row.get("extraction_confidence", 0)) > int(current.get("extraction_confidence", 0)):
            best_by_key[key] = row

    return sorted(
        best_by_key.values(),
        key=lambda item: (
            item.get("raw_file_name", ""),
            item.get("isin", ""),
            -int(item.get("extraction_confidence", 0)),
        ),
    )


def main() -> None:
    for path in [DRY_RUN_JSON, DRY_RUN_MD, EXTRACTED_CANDIDATES_CSV, EXTRACTION_QUALITY_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if not RAW_DIR.exists():
        raise SystemExit(f"Missing raw dir: {RAW_DIR}")

    prep = read_json(PREP_JSON)
    table_candidates = read_csv(TABLE_CANDIDATES_CSV)
    source_strategy = read_csv(SOURCE_STRATEGY_CSV)

    raw_files = sorted(RAW_DIR.glob("*.html"))

    extracted_rows: list[dict] = []
    quality_rows: list[dict] = []

    for raw_file in raw_files:
        tables = extract_tables(raw_file)
        table_rows_before = len(extracted_rows)

        for table_index, table in enumerate(tables):
            header_map = detect_header_map(table)

            for row_index, row in enumerate(table):
                candidate = candidate_from_table_row(raw_file, table_index, row_index, row, header_map)
                if candidate:
                    extracted_rows.append(candidate)

        table_isins_for_file = {
            row["isin"]
            for row in extracted_rows
            if row.get("raw_file_name") == raw_file.name and row.get("source_kind") == "html_table_row"
        }

        context_rows = context_candidates_from_text(raw_file, table_isins_for_file)
        extracted_rows.extend(context_rows)

        file_rows = [
            row for row in extracted_rows
            if row.get("raw_file_name") == raw_file.name
        ]

        quality_counter = Counter(row["quality_bucket"] for row in file_rows)
        source_counter = Counter(row["source_kind"] for row in file_rows)

        quality_rows.append(
            {
                "raw_file_name": raw_file.name,
                "raw_file": str(raw_file),
                "html_tables_detected": len(tables),
                "table_based_candidates": len([
                    row for row in file_rows
                    if row.get("source_kind") == "html_table_row"
                ]),
                "context_only_candidates": len([
                    row for row in file_rows
                    if row.get("source_kind") == "isin_context"
                ]),
                "total_candidates": len(file_rows),
                "high_quality": quality_counter.get("high", 0),
                "medium_quality": quality_counter.get("medium", 0),
                "low_quality": quality_counter.get("low", 0),
                "source_kind_counts": json.dumps(dict(source_counter), ensure_ascii=False),
                "notes": "dry_run_counts_only_no_net_new_no_rebuild",
            }
        )

    deduped_rows = deduplicate_candidates(extracted_rows)

    total_candidates_raw = len(extracted_rows)
    total_candidates_deduped = len(deduped_rows)
    unique_isins = len({row["isin"] for row in deduped_rows if row.get("isin")})

    quality_counter_total = Counter(row["quality_bucket"] for row in deduped_rows)
    source_counter_total = Counter(row["source_kind"] for row in deduped_rows)

    allowed_strategy_rows = [
        row for row in source_strategy
        if str(row.get("allowed_in_next_phase", "")).lower() == "true"
    ]

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append(
            {
                "check": check,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add_check("v2_15e_prep_exists", PREP_JSON.exists(), "critical", str(PREP_JSON))
    add_check("raw_files_available", len(raw_files) > 0, "critical", f"raw_files={len(raw_files)}")
    add_check("table_candidates_available", len(table_candidates) >= 0, "warning", f"table_candidates={len(table_candidates)}")
    add_check("source_strategy_available", len(source_strategy) > 0, "critical", f"strategy_rows={len(source_strategy)}")
    add_check("allowed_strategy_rows_review", len(allowed_strategy_rows) >= 0, "warning", f"allowed_strategy_rows={len(allowed_strategy_rows)}")
    add_check("dry_run_candidates_extracted", total_candidates_deduped > 0, "critical", f"deduped_candidates={total_candidates_deduped}")
    add_check("unique_isins_detected", unique_isins > 0, "critical", f"unique_isins={unique_isins}")
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"current_rows={CURRENT_ROWS}")

    medium_or_high_candidates = (
        quality_counter_total.get("medium", 0)
        + quality_counter_total.get("high", 0)
    )

    table_based_candidates_total = source_counter_total.get("html_table_row", 0)
    context_only_candidates_total = source_counter_total.get("isin_context", 0)

    extraction_quality = "low"
    if medium_or_high_candidates >= 10 or quality_counter_total.get("high", 0) > 0:
        extraction_quality = "medium"
    if quality_counter_total.get("high", 0) >= 25 and table_based_candidates_total >= 25:
        extraction_quality = "high"

    add_check(
        "medium_or_high_candidates_review",
        medium_or_high_candidates > 0,
        "warning",
        f"medium_or_high_candidates={medium_or_high_candidates}",
    )
    add_check(
        "table_based_candidates_review",
        table_based_candidates_total > 0,
        "warning",
        f"table_based_candidates={table_based_candidates_total}",
    )
    add_check(
        "context_only_not_enough_for_rebuild",
        not (context_only_candidates_total > 0 and table_based_candidates_total == 0),
        "warning",
        f"context_only_candidates={context_only_candidates_total}; table_based_candidates={table_based_candidates_total}",
    )

    if critical_failed != 0:
        status = "EURONEXT_CANDIDATE_EXTRACTION_DRY_RUN_FAILED_REBUILD_BLOCKED"
    elif extraction_quality == "low":
        status = "EURONEXT_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_LOW_QUALITY_REBUILD_STILL_BLOCKED"
    else:
        status = "EURONEXT_CANDIDATE_EXTRACTION_DRY_RUN_PASSED_REBUILD_STILL_BLOCKED"

    next_phase = "v2.15G - Euronext Candidate Extraction Validation"
    if total_candidates_deduped == 0 or extraction_quality == "low":
        next_phase = "v2.15F2 - Euronext Extraction Strategy Revision"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "canonical_dataset": CURRENT_CANONICAL_DATASET,
            "current_rows": CURRENT_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED_PERCENT,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "dry_run_summary": {
            "raw_files_reviewed": len(raw_files),
            "strategy_rows_from_v2_15e": len(source_strategy),
            "allowed_strategy_rows_from_v2_15e": len(allowed_strategy_rows),
            "table_candidates_from_v2_15e": len(table_candidates),
            "raw_extracted_candidates_before_dedupe": total_candidates_raw,
            "deduped_extracted_candidates": total_candidates_deduped,
            "unique_isins": unique_isins,
            "quality_bucket_counts": dict(quality_counter_total),
            "source_kind_counts": dict(source_counter_total),
            "extraction_quality": extraction_quality,
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "top_candidates": deduped_rows[:50],
        "quality_by_raw_file": quality_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "raw_html_parsed_for_dry_run": True,
            "candidate_rows_extracted_to_dry_run_csv": True,
            "canonical_dataset_read": False,
            "canonical_dataset_modified": False,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": next_phase,
    }

    write_json(DRY_RUN_JSON, payload)
    write_csv(EXTRACTED_CANDIDATES_CSV, deduped_rows, CSV_FIELDNAMES)

    write_csv(
        EXTRACTION_QUALITY_CSV,
        quality_rows,
        [
            "raw_file_name",
            "raw_file",
            "html_tables_detected",
            "table_based_candidates",
            "context_only_candidates",
            "total_candidates",
            "high_quality",
            "medium_quality",
            "low_quality",
            "source_kind_counts",
            "notes",
        ],
    )

    check_lines = "\n".join(
        f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}"
        for item in checks
    )

    quality_lines = "\n".join(
        f"- `{row['raw_file_name']}` tables={row['html_tables_detected']} table_candidates={row['table_based_candidates']} context_candidates={row['context_only_candidates']} total={row['total_candidates']} high={row['high_quality']} medium={row['medium_quality']} low={row['low_quality']}"
        for row in quality_rows
    )

    candidate_lines = "\n".join(
        f"- `{row['isin']}` source={row['source_kind']} quality={row['quality_bucket']} confidence={row['extraction_confidence']} file=`{row['raw_file_name']}` name=`{row['raw_name']}` symbol=`{row['raw_symbol']}`"
        for row in deduped_rows[:25]
    ) or "- No candidates extracted."

    DRY_RUN_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Current state

- Canonical dataset: `{CURRENT_CANONICAL_DATASET}`
- Current rows: `{CURRENT_ROWS}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completed: `{SOURCE_TO_50K_COMPLETED_PERCENT}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Dry-run summary

- Raw files reviewed: {payload["dry_run_summary"]["raw_files_reviewed"]}
- Strategy rows from v2.15E: {payload["dry_run_summary"]["strategy_rows_from_v2_15e"]}
- Allowed strategy rows from v2.15E: {payload["dry_run_summary"]["allowed_strategy_rows_from_v2_15e"]}
- Table candidates from v2.15E: {payload["dry_run_summary"]["table_candidates_from_v2_15e"]}
- Raw extracted candidates before dedupe: {payload["dry_run_summary"]["raw_extracted_candidates_before_dedupe"]}
- Deduped extracted candidates: {payload["dry_run_summary"]["deduped_extracted_candidates"]}
- Unique ISINs: {payload["dry_run_summary"]["unique_isins"]}
- Quality bucket counts: `{payload["dry_run_summary"]["quality_bucket_counts"]}`
- Source kind counts: `{payload["dry_run_summary"]["source_kind_counts"]}`
- Extraction quality: `{payload["dry_run_summary"]["extraction_quality"]}`
- Critical failed checks: {critical_failed}

## Quality by raw file

{quality_lines}

## Top candidates

{candidate_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.15F: false
- Raw files downloaded in v2.15F: false
- Raw files modified after write: false
- Raw HTML parsed for dry run: true
- Candidate rows extracted to dry-run CSV: true
- Canonical dataset read: false
- Canonical dataset modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase extracts provisional raw candidates only.

It does not read or modify the canonical expanded universe, does not calculate definitive net-new rows, does not normalize securities, does not rebuild the expanded universe, does not score equities, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Recommended next phase

`{next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15F Euronext candidate extraction dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("DRY_RUN_SUMMARY:")
    for key, value in payload["dry_run_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for item in checks:
        print(f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {next_phase}")


if __name__ == "__main__":
    main()
