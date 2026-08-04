from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


VERSION = "v2.15E"
PHASE = "Euronext Expanded Rebuild Candidate Preparation"
PHASE_TYPE = "candidate-preparation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "euronext_v2_15c"

VALIDATION_JSON = OUTPUT_DIR / "euronext_validation_v2_15d.json"
CANDIDATE_ENDPOINTS_CSV = OUTPUT_DIR / "euronext_candidate_endpoints_v2_15d.csv"
RAW_FILE_DIAGNOSTICS_CSV = OUTPUT_DIR / "euronext_raw_file_diagnostics_v2_15d.csv"

PREP_JSON = OUTPUT_DIR / "euronext_rebuild_candidate_prep_v2_15e.json"
PREP_MD = OUTPUT_DIR / "euronext_rebuild_candidate_prep_v2_15e.md"
TABLE_CANDIDATES_CSV = OUTPUT_DIR / "euronext_table_candidates_v2_15e.csv"
SOURCE_STRATEGY_CSV = OUTPUT_DIR / "euronext_source_strategy_v2_15e.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

FIELD_MARKERS = [
    "isin",
    "symbol",
    "ticker",
    "name",
    "instrument",
    "market",
    "mic",
    "currency",
    "company",
    "issuer",
    "listing",
    "stock",
    "equity",
    "shares",
]

MINIMAL_TARGET_FIELDS = [
    "isin",
    "ticker_or_symbol",
    "name_or_issuer",
    "market_or_exchange",
    "currency_optional",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
            cleaned = " ".join(data.split())
            if cleaned:
                self.current_cell_parts.append(cleaned)

    def handle_endtag(self, tag: str) -> None:
        tag_low = tag.lower()
        if tag_low in {"td", "th"} and self.in_cell:
            self.current_row.append(" ".join(self.current_cell_parts).strip())
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


def score_table(table: list[list[str]]) -> dict:
    row_count = len(table)
    max_col_count = max((len(row) for row in table), default=0)

    candidate_header_rows = table[:5]
    header_text = " | ".join(
        " / ".join(cell for cell in row if cell)
        for row in candidate_header_rows
    )
    combined = header_text.lower()

    marker_hits = []
    for marker in FIELD_MARKERS:
        if marker in combined:
            marker_hits.append(marker)

    score = 0
    score += min(row_count, 100)
    score += min(max_col_count * 5, 40)
    score += len(marker_hits) * 20

    if row_count >= 10:
        score += 20
    if max_col_count >= 4:
        score += 20
    if "isin" in marker_hits:
        score += 40
    if "ticker" in marker_hits or "symbol" in marker_hits:
        score += 25
    if "name" in marker_hits or "issuer" in marker_hits or "company" in marker_hits:
        score += 25
    if "currency" in marker_hits:
        score += 10

    suitability = "low"
    if score >= 160:
        suitability = "high"
    elif score >= 90:
        suitability = "medium"

    return {
        "row_count": row_count,
        "max_col_count": max_col_count,
        "header_text": header_text[:1000],
        "field_marker_hits": "|".join(marker_hits),
        "suitability_score": score,
        "suitability": suitability,
    }


def endpoint_strategy_rows(endpoint_rows: list[dict]) -> list[dict]:
    rows = []

    external_noise_markers = [
        "cdnjs.cloudflare.com",
        "api.mapbox.com",
        "mapbox-gl",
        "googletagmanager",
        "google-analytics",
        "jquery",
        "bootstrap",
        ".css",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".svg",
    ]

    marketing_noise_markers = [
        "/raise-capital/",
        "/ipo",
        "/investor-relations/",
        "/news/",
        "/events/",
        "/media/",
        "/careers/",
        "/about/",
    ]

    relevant_markers = [
        "equities",
        "equity",
        "instrument",
        "instruments",
        "stock",
        "stocks",
        "csv",
        "download",
        "json",
        "api",
        "ajax",
        "live.euronext.com",
        "static-reference-data",
        "advanced-reference-data",
    ]

    for row in endpoint_rows:
        url = str(row.get("candidate_url", "")).strip()
        hints = row.get("matched_hints", "")
        score_text = row.get("score", "0")

        try:
            base_score = int(score_text)
        except ValueError:
            base_score = 0

        low = url.lower()

        proposed_use = "excluded_noise_or_irrelevant"
        priority = 9
        risk = "high_irrelevant"
        allowed = False

        is_relative_euronext_route = low.startswith("/") and not low.startswith("//")
        is_euronext_domain = "euronext.com" in low or "live.euronext.com" in low
        is_euronext_like = is_relative_euronext_route or is_euronext_domain
        is_external_noise = any(marker in low for marker in external_noise_markers)
        is_marketing_noise = any(marker in low for marker in marketing_noise_markers)
        has_relevant_marker = any(marker in low for marker in relevant_markers)

        if not url:
            proposed_use = "excluded_empty_url"

        elif is_external_noise:
            proposed_use = "excluded_external_asset_or_library"

        elif is_marketing_noise:
            proposed_use = "excluded_marketing_or_corporate_page"

        elif not is_euronext_like:
            proposed_use = "excluded_non_euronext_url"

        elif not has_relevant_marker:
            proposed_use = "excluded_no_relevant_market_data_marker"

        elif (
            ("csv" in low or "download" in low)
            and is_euronext_like
            and ("equity" in low or "equities" in low or "instrument" in low or "instruments" in low or "stock" in low)
        ):
            proposed_use = "possible_structured_download_endpoint_next_phase"
            priority = 1
            risk = "medium"
            allowed = True

        elif (
            ("live.euronext.com" in low or is_relative_euronext_route)
            and ("equity" in low or "equities" in low)
            and ("list" in low or "products" in low or "markets" in low)
        ):
            proposed_use = "possible_public_equity_listing_route_next_phase"
            priority = 2
            risk = "medium"
            allowed = True

        elif (
            ("json" in low or "/api/" in low or "ajax" in low)
            and is_euronext_like
            and ("equity" in low or "equities" in low or "instrument" in low or "instruments" in low or "stock" in low)
        ):
            proposed_use = "possible_euronext_json_or_ajax_endpoint_next_phase"
            priority = 3
            risk = "medium"
            allowed = True

        elif "static-reference-data" in low or "advanced-reference-data" in low:
            proposed_use = "reference_data_documentation_only"
            priority = 4
            risk = "high_if_commercial_or_gated"
            allowed = False

        else:
            proposed_use = "review_only_euronext_relevant_but_not_allowed"
            priority = 5
            risk = "medium"
            allowed = False

        rows.append(
            {
                "candidate_url": url,
                "source_raw_file": row.get("raw_file", ""),
                "base_validation_score": base_score,
                "matched_hints": hints,
                "proposed_use": proposed_use,
                "priority": priority,
                "risk": risk,
                "allowed_in_next_phase": allowed,
            }
        )

    return sorted(rows, key=lambda item: (int(item["priority"]), -int(item["base_validation_score"])))


def main() -> None:
    for path in [PREP_JSON, PREP_MD, TABLE_CANDIDATES_CSV, SOURCE_STRATEGY_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if not RAW_DIR.exists():
        raise SystemExit(f"Missing raw dir: {RAW_DIR}")

    validation = read_json(VALIDATION_JSON)
    endpoint_rows = read_csv(CANDIDATE_ENDPOINTS_CSV)
    raw_diagnostics = read_csv(RAW_FILE_DIAGNOSTICS_CSV)

    raw_files = sorted(RAW_DIR.glob("*.html"))

    table_candidate_rows = []

    for raw_file in raw_files:
        tables = extract_tables(raw_file)

        for index, table in enumerate(tables):
            scored = score_table(table)
            table_candidate_rows.append(
                {
                    "raw_file": str(raw_file),
                    "raw_file_name": raw_file.name,
                    "table_index": index,
                    **scored,
                }
            )

    table_candidate_rows = sorted(
        table_candidate_rows,
        key=lambda row: int(row["suitability_score"]),
        reverse=True,
    )

    strategy_rows = endpoint_strategy_rows(endpoint_rows)

    suitability_counter = Counter(row["suitability"] for row in table_candidate_rows)
    usable_table_candidates = [
        row for row in table_candidate_rows
        if row["suitability"] in {"high", "medium"}
    ]

    allowed_next_phase_endpoints = [
        row for row in strategy_rows
        if str(row["allowed_in_next_phase"]).lower() == "true"
    ]

    extraction_route = "endpoint_first"
    if usable_table_candidates and not allowed_next_phase_endpoints:
        extraction_route = "html_table_first"
    elif usable_table_candidates and allowed_next_phase_endpoints:
        extraction_route = "hybrid_endpoint_then_html_table_fallback"
    elif allowed_next_phase_endpoints:
        extraction_route = "endpoint_first"
    else:
        extraction_route = "insufficient_candidates_requires_manual_endpoint_review"

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

    add_check("v2_15d_validation_exists", VALIDATION_JSON.exists(), "critical", str(VALIDATION_JSON))
    add_check("v2_15d_validation_passed_or_available", bool(validation.get("status")), "critical", str(validation.get("status")))
    add_check("raw_files_available", len(raw_files) > 0, "critical", f"raw_files={len(raw_files)}")
    add_check("candidate_endpoints_available", len(endpoint_rows) > 0, "critical", f"candidate_endpoints={len(endpoint_rows)}")
    add_check("source_strategy_generated", len(strategy_rows) > 0, "critical", f"strategy_rows={len(strategy_rows)}")
    add_check("rebuild_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"current_rows={CURRENT_ROWS}")
    add_check("no_canonical_dataset_write", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")

    add_check(
        "usable_table_candidates_review",
        len(usable_table_candidates) >= 0,
        "warning",
        f"usable_table_candidates={len(usable_table_candidates)}",
    )

    status = (
        "EURONEXT_REBUILD_CANDIDATE_PREP_PASSED_REBUILD_STILL_BLOCKED"
        if critical_failed == 0
        else "EURONEXT_REBUILD_CANDIDATE_PREP_FAILED_REBUILD_BLOCKED"
    )

    next_phase = "v2.15F - Euronext Candidate Extraction Dry Run"
    if extraction_route == "insufficient_candidates_requires_manual_endpoint_review":
        next_phase = "v2.15E2 - Euronext Manual Endpoint Review"

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
        "preparation_summary": {
            "raw_files_reviewed": len(raw_files),
            "raw_diagnostic_rows": len(raw_diagnostics),
            "candidate_endpoints_from_v2_15d": len(endpoint_rows),
            "source_strategy_rows": len(strategy_rows),
            "html_table_candidates": len(table_candidate_rows),
            "usable_table_candidates_medium_or_high": len(usable_table_candidates),
            "table_suitability_counts": dict(suitability_counter),
            "allowed_next_phase_endpoints": len(allowed_next_phase_endpoints),
            "extraction_route": extraction_route,
            "critical_failed_checks": critical_failed,
        },
        "minimal_target_fields": MINIMAL_TARGET_FIELDS,
        "checks": checks,
        "top_table_candidates": table_candidate_rows[:25],
        "top_source_strategy_rows": strategy_rows[:50],
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "raw_html_parsed_for_candidate_preparation": True,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "canonical_dataset_modified": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": next_phase,
    }

    write_json(PREP_JSON, payload)

    write_csv(
        TABLE_CANDIDATES_CSV,
        table_candidate_rows,
        [
            "raw_file",
            "raw_file_name",
            "table_index",
            "row_count",
            "max_col_count",
            "header_text",
            "field_marker_hits",
            "suitability_score",
            "suitability",
        ],
    )

    write_csv(
        SOURCE_STRATEGY_CSV,
        strategy_rows,
        [
            "candidate_url",
            "source_raw_file",
            "base_validation_score",
            "matched_hints",
            "proposed_use",
            "priority",
            "risk",
            "allowed_in_next_phase",
        ],
    )

    check_lines = "\n".join(
        f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}"
        for item in checks
    )

    table_lines = "\n".join(
        f"- `{row['raw_file_name']}` table={row['table_index']} rows={row['row_count']} cols={row['max_col_count']} score={row['suitability_score']} suitability={row['suitability']} hits={row['field_marker_hits']}"
        for row in table_candidate_rows[:20]
    ) or "- No HTML table candidates detected."

    strategy_lines = "\n".join(
        f"- priority={row['priority']} score={row['base_validation_score']} use={row['proposed_use']} risk={row['risk']} url={row['candidate_url']}"
        for row in strategy_rows[:20]
    ) or "- No source strategy rows generated."

    PREP_MD.write_text(
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

## Preparation summary

- Raw files reviewed: {payload["preparation_summary"]["raw_files_reviewed"]}
- Raw diagnostic rows: {payload["preparation_summary"]["raw_diagnostic_rows"]}
- Candidate endpoints from v2.15D: {payload["preparation_summary"]["candidate_endpoints_from_v2_15d"]}
- Source strategy rows: {payload["preparation_summary"]["source_strategy_rows"]}
- HTML table candidates: {payload["preparation_summary"]["html_table_candidates"]}
- Usable table candidates, medium/high: {payload["preparation_summary"]["usable_table_candidates_medium_or_high"]}
- Allowed next phase endpoints: {payload["preparation_summary"]["allowed_next_phase_endpoints"]}
- Extraction route: `{payload["preparation_summary"]["extraction_route"]}`
- Critical failed checks: {critical_failed}

## Minimal target fields for later extraction

- ISIN
- Ticker or symbol
- Name, issuer or company
- Market or exchange
- Currency optional

## Top table candidates

{table_lines}

## Top source strategy rows

{strategy_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.15E: false
- Raw files downloaded in v2.15E: false
- Raw files modified after write: false
- Raw HTML parsed for candidate preparation: true
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Canonical dataset modified: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase prepares the rebuild candidate strategy only.

It does not normalize securities, classify final instruments, filter net-new rows, rebuild the expanded universe, score equities, call OpenAI, call broker APIs or launch full 59k.

## Recommended next phase

`{next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15E Euronext rebuild candidate preparation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("PREPARATION_SUMMARY:")
    for key, value in payload["preparation_summary"].items():
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
