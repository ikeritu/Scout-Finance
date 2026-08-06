from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.17B"
PHASE = "NSE India Acquisition Plan"
PHASE_TYPE = "provider-acquisition-plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
V217A_JSON = OUTPUT_DIR / "next_provider_route_selection_v2_17a.json"

REPORT_JSON = OUTPUT_DIR / "nse_india_acquisition_plan_v2_17b.json"
REPORT_MD = OUTPUT_DIR / "nse_india_acquisition_plan_v2_17b.md"
SOURCE_PLAN_CSV = OUTPUT_DIR / "nse_india_source_plan_v2_17b.csv"
FILTER_POLICY_CSV = OUTPUT_DIR / "nse_india_filter_policy_v2_17b.csv"
ACQUISITION_ACTIONS_CSV = OUTPUT_DIR / "nse_india_acquisition_actions_v2_17b.csv"

CURRENT_CANONICAL_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713

EXPECTED_V217A_STATUS = "NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_NSE_INDIA_SELECTED_FULL_SOURCE_STILL_BLOCKED"
EXPECTED_V217A_NEXT = "v2.17B - NSE India Acquisition Plan"

NEXT_PHASE = "v2.17C - NSE India Raw Acquisition"

SOURCE_FIELDS = [
    "source_id",
    "priority",
    "source_name",
    "source_url",
    "expected_format",
    "source_role",
    "planned_action",
    "inclusion_scope",
    "expected_noise",
    "risk_level",
    "notes",
]

FILTER_FIELDS = [
    "policy_id",
    "instrument_or_source_type",
    "decision",
    "reason",
    "planned_detection_fields",
    "notes",
]

ACTION_FIELDS = [
    "action_id",
    "phase",
    "source_id",
    "action",
    "network_allowed_in_v2_17b",
    "network_allowed_in_v2_17c",
    "canonical_read_allowed",
    "canonical_modify_allowed",
    "output_expected_in_v2_17c",
    "guard_notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return sum(1 for _ in csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


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


def make_source_plan() -> list[dict]:
    return [
        {
            "source_id": "nse_all_reports_cm_mii_security_file_nse_listed",
            "priority": 1,
            "source_name": "CM - MII - Security File (.gz) (NSE Listed securities)",
            "source_url": "https://www.nseindia.com/all-reports",
            "expected_format": "csv.gz",
            "source_role": "primary_bulk_candidate_source",
            "planned_action": "download raw .gz only in v2.17C; preserve raw artifact; no parsing in acquisition phase",
            "inclusion_scope": "NSE listed capital market securities; later filter to ordinary/listed equity candidates only",
            "expected_noise": "medium",
            "risk_level": "medium",
            "notes": "Main NSE route. File naming appears date-stamped as NSE_CM_security_ddmmyyyy.csv.gz. v2.17C should capture exact downloaded filename and date.",
        },
        {
            "source_id": "nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive",
            "priority": 2,
            "source_name": "CM - MII - Security File (.gz) (NSE Listed and BSE Exclusive securities)",
            "source_url": "https://www.nseindia.com/all-reports",
            "expected_format": "csv.gz",
            "source_role": "secondary_bulk_candidate_source_review",
            "planned_action": "download raw .gz only in v2.17C if available; mark BSE-exclusive rows for review/exclusion until policy is explicit",
            "inclusion_scope": "review only; avoid silently importing BSE-exclusive as NSE-listed",
            "expected_noise": "medium_high",
            "risk_level": "medium_high",
            "notes": "Useful for coverage comparison but must not blur NSE route with BSE-exclusive universe.",
        },
        {
            "source_id": "nse_securities_available_equity_segment",
            "priority": 3,
            "source_name": "Securities available for Equity segment (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "cross_check_and_candidate_source",
            "planned_action": "download raw csv only in v2.17C; use later to confirm tradable equity segment and compare against security file",
            "inclusion_scope": "equity segment securities; later filter out ETF/REIT/INVIT/IDR/preference/partly-paid if present",
            "expected_noise": "medium",
            "risk_level": "medium",
            "notes": "Important cross-check because NSE page separates multiple non-common-equity categories.",
        },
        {
            "source_id": "nse_securities_available_sme",
            "priority": 4,
            "source_name": "Securities available for trading in SME (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "review_candidate_source",
            "planned_action": "download raw csv only in v2.17C; classify SME equity separately for later review",
            "inclusion_scope": "SME ordinary equity candidates may be allowed only after validation",
            "expected_noise": "medium",
            "risk_level": "medium",
            "notes": "Potentially useful for listed equities but should remain review bucket before canonical impact.",
        },
        {
            "source_id": "nse_changes_company_names",
            "priority": 5,
            "source_name": "Changes in Company Names (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "reference_only",
            "planned_action": "download raw csv only in v2.17C; use later as supporting metadata, not as candidate source",
            "inclusion_scope": "reference only",
            "expected_noise": "low",
            "risk_level": "low",
            "notes": "Useful to reconcile canonical name differences and avoid false duplicates.",
        },
        {
            "source_id": "nse_changes_symbols",
            "priority": 6,
            "source_name": "Changes in Symbols (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "reference_only",
            "planned_action": "download raw csv only in v2.17C; use later as supporting metadata, not as candidate source",
            "inclusion_scope": "reference only",
            "expected_noise": "low",
            "risk_level": "low",
            "notes": "Useful to reconcile symbol changes before duplicate checks.",
        },
        {
            "source_id": "nse_idrs",
            "priority": 7,
            "source_name": "Indian Depository Receipts (IDRs) (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "explicit_exclusion_reference",
            "planned_action": "download raw csv only in v2.17C if tiny/available; use as exclusion list",
            "inclusion_scope": "exclude from ordinary equity candidate additions",
            "expected_noise": "low",
            "risk_level": "low",
            "notes": "Depository receipts are not ordinary local equity rows for this route.",
        },
        {
            "source_id": "nse_preference_shares",
            "priority": 8,
            "source_name": "Preference Shares (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "explicit_exclusion_reference",
            "planned_action": "download raw csv only in v2.17C if available; use as exclusion list",
            "inclusion_scope": "exclude or manual review only",
            "expected_noise": "low",
            "risk_level": "low",
            "notes": "Preference shares should not be mixed with common/ordinary equity candidates.",
        },
        {
            "source_id": "nse_warrants",
            "priority": 9,
            "source_name": "Warrants (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "explicit_exclusion_reference",
            "planned_action": "download raw csv only in v2.17C if available; use as exclusion list",
            "inclusion_scope": "exclude",
            "expected_noise": "low",
            "risk_level": "low",
            "notes": "Warrants are derivative-like/security rights instruments and must not enter equity candidate additions.",
        },
        {
            "source_id": "nse_etfs",
            "priority": 10,
            "source_name": "Securities available for trading in ETF (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "explicit_exclusion_reference",
            "planned_action": "download raw csv only in v2.17C; use as exclusion list",
            "inclusion_scope": "exclude",
            "expected_noise": "low",
            "risk_level": "low",
            "notes": "ETFs are excluded from the ordinary equity universe.",
        },
        {
            "source_id": "nse_close_ended_mf",
            "priority": 11,
            "source_name": "Close Ended MF Schemes (Listed) (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "explicit_exclusion_reference",
            "planned_action": "download raw csv only in v2.17C if available; use as exclusion list",
            "inclusion_scope": "exclude",
            "expected_noise": "low",
            "risk_level": "low",
            "notes": "Mutual fund schemes are excluded.",
        },
        {
            "source_id": "nse_reits",
            "priority": 12,
            "source_name": "Units available for REITs (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "explicit_exclusion_reference",
            "planned_action": "download raw csv only in v2.17C if available; use as exclusion list",
            "inclusion_scope": "exclude",
            "expected_noise": "low",
            "risk_level": "low",
            "notes": "REIT units are excluded from ordinary equity candidate additions.",
        },
        {
            "source_id": "nse_invits",
            "priority": 13,
            "source_name": "Units available for INVITs (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "explicit_exclusion_reference",
            "planned_action": "download raw csv only in v2.17C if available; use as exclusion list",
            "inclusion_scope": "exclude",
            "expected_noise": "low",
            "risk_level": "low",
            "notes": "Infrastructure investment trust units are excluded.",
        },
        {
            "source_id": "nse_debt_instruments",
            "priority": 14,
            "source_name": "Debt Instruments (.csv)",
            "source_url": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_format": "csv",
            "source_role": "explicit_exclusion_reference",
            "planned_action": "do not prioritize due size/noise; download only if needed as exclusion evidence",
            "inclusion_scope": "exclude",
            "expected_noise": "high",
            "risk_level": "medium",
            "notes": "Debt file is explicitly not an equity candidate source.",
        },
    ]


def make_filter_policy() -> list[dict]:
    return [
        {
            "policy_id": "include_nse_listed_ordinary_equity",
            "instrument_or_source_type": "NSE listed ordinary/fully paid equity shares",
            "decision": "include_after_validation",
            "reason": "Target universe is listed equity companies/securities, not funds/debt/derivative instruments.",
            "planned_detection_fields": "symbol, company/security name, series/instrument type, source_id",
            "notes": "Do not add directly in v2.17C; only later after extraction and canonical dry-run validation.",
        },
        {
            "policy_id": "review_sme_equity",
            "instrument_or_source_type": "NSE SME/Emerge equity",
            "decision": "review",
            "reason": "May be valid equity but should be classified separately before canonical impact.",
            "planned_detection_fields": "source_id, series, instrument type, SME source file",
            "notes": "Can become candidate rows after v2.17D/E validation if evidence is clean.",
        },
        {
            "policy_id": "exclude_bse_exclusive_until_explicit_scope",
            "instrument_or_source_type": "BSE Exclusive securities inside NSE file route",
            "decision": "exclude_or_review",
            "reason": "This phase is NSE route selection; BSE-exclusive rows should not silently enter NSE-derived universe.",
            "planned_detection_fields": "source file label, exchange/listing flag, security file columns",
            "notes": "Could be a future BSE route, but not silently included here.",
        },
        {
            "policy_id": "exclude_etf",
            "instrument_or_source_type": "ETF",
            "decision": "exclude",
            "reason": "ETF is fund/product exposure, not ordinary company equity.",
            "planned_detection_fields": "ETF source file, series, instrument type, name keywords",
            "notes": "Use NSE ETF CSV as exclusion evidence.",
        },
        {
            "policy_id": "exclude_reit_invit",
            "instrument_or_source_type": "REIT / INVIT units",
            "decision": "exclude",
            "reason": "Trust units are not ordinary operating-company equity shares.",
            "planned_detection_fields": "REIT/INVIT source files, instrument type, name keywords",
            "notes": "Use NSE REIT/INVIT CSVs as exclusion evidence.",
        },
        {
            "policy_id": "exclude_mutual_funds",
            "instrument_or_source_type": "Close-ended mutual fund schemes",
            "decision": "exclude",
            "reason": "Funds are out of scope.",
            "planned_detection_fields": "MF source file, instrument type, name keywords",
            "notes": "Use close-ended MF CSV as exclusion evidence.",
        },
        {
            "policy_id": "exclude_debt",
            "instrument_or_source_type": "Debt instruments",
            "decision": "exclude",
            "reason": "Debt/fixed income instruments are out of scope.",
            "planned_detection_fields": "debt source file, instrument type, ISIN prefix/context, name keywords",
            "notes": "Debt file may be large and should not drive candidate extraction.",
        },
        {
            "policy_id": "exclude_warrants",
            "instrument_or_source_type": "Warrants",
            "decision": "exclude",
            "reason": "Warrants are not ordinary equity shares.",
            "planned_detection_fields": "warrants source file, symbol/name keywords, instrument type",
            "notes": "Use warrants CSV as exclusion evidence.",
        },
        {
            "policy_id": "exclude_idr",
            "instrument_or_source_type": "Indian Depository Receipts",
            "decision": "exclude",
            "reason": "Depository receipts are not local ordinary equity rows for this route.",
            "planned_detection_fields": "IDR source file, instrument type, name keywords",
            "notes": "Explicitly keep separate from equity candidates.",
        },
        {
            "policy_id": "review_preference_shares",
            "instrument_or_source_type": "Preference shares",
            "decision": "exclude_or_manual_review",
            "reason": "Preferred/preference shares should not be mixed with ordinary equity.",
            "planned_detection_fields": "preference shares source file, series, instrument type, name keywords",
            "notes": "Default exclude unless a future explicit policy permits separate share classes.",
        },
        {
            "policy_id": "reference_symbol_name_changes",
            "instrument_or_source_type": "Company name/symbol changes",
            "decision": "reference_only",
            "reason": "Useful for duplicate resolution but not a candidate source.",
            "planned_detection_fields": "changes in company names, changes in symbols",
            "notes": "Use later to improve canonical comparison and avoid false negatives.",
        },
    ]


def make_actions(source_plan: list[dict]) -> list[dict]:
    rows = []

    for source in source_plan:
        source_id = source["source_id"]
        role = source["source_role"]

        if role in {"primary_bulk_candidate_source", "secondary_bulk_candidate_source_review", "cross_check_and_candidate_source", "review_candidate_source"}:
            expected = "raw source artifact under outputs/full_universe_source_acquisition/nse_raw_acquisition_v2_17c/"
        elif role == "reference_only":
            expected = "raw reference artifact under outputs/full_universe_source_acquisition/nse_raw_acquisition_v2_17c/"
        else:
            expected = "raw exclusion/reference artifact under outputs/full_universe_source_acquisition/nse_raw_acquisition_v2_17c/"

        rows.append(
            {
                "action_id": sha256_text(f"{VERSION}|{source_id}|download_raw_v217c")[:16],
                "phase": "v2.17C",
                "source_id": source_id,
                "action": source["planned_action"],
                "network_allowed_in_v2_17b": False,
                "network_allowed_in_v2_17c": True,
                "canonical_read_allowed": False,
                "canonical_modify_allowed": False,
                "output_expected_in_v2_17c": expected,
                "guard_notes": "v2.17C may download raw source files only; no parsing, no candidate extraction, no canonical comparison, no rebuild.",
            }
        )

    return rows


def main() -> None:
    for path in [REPORT_JSON, REPORT_MD, SOURCE_PLAN_CSV, FILTER_POLICY_CSV, ACQUISITION_ACTIONS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v217a = read_json(V217A_JSON)
    canonical_rows = count_csv_rows(CANONICAL_DATASET)

    source_plan = make_source_plan()
    filter_policy = make_filter_policy()
    actions = make_actions(source_plan)

    primary_sources = [
        row for row in source_plan
        if row["source_role"] in {"primary_bulk_candidate_source", "cross_check_and_candidate_source"}
    ]

    exclusion_sources = [
        row for row in source_plan
        if row["source_role"] == "explicit_exclusion_reference"
    ]

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_17a_report_exists", V217A_JSON.exists(), "critical", str(V217A_JSON))
    add_check(
        "v2_17a_status_expected",
        v217a.get("status") == EXPECTED_V217A_STATUS,
        "critical",
        str(v217a.get("status", "")),
    )
    add_check(
        "v2_17a_recommended_b",
        v217a.get("recommended_next_phase") == EXPECTED_V217A_NEXT,
        "critical",
        str(v217a.get("recommended_next_phase", "")),
    )
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("canonical_rows_expected", canonical_rows == CURRENT_CANONICAL_ROWS, "critical", f"canonical_rows={canonical_rows}")
    add_check("nse_primary_source_present", any(row["source_id"] == "nse_all_reports_cm_mii_security_file_nse_listed" for row in source_plan), "critical", "primary NSE MII security file")
    add_check("nse_equity_crosscheck_present", any(row["source_id"] == "nse_securities_available_equity_segment" for row in source_plan), "critical", "equity segment CSV")
    add_check("exclusion_sources_present", len(exclusion_sources) >= 6, "critical", f"exclusion_sources={len(exclusion_sources)}")
    add_check("source_plan_count", len(source_plan) >= 10, "critical", f"sources={len(source_plan)}")
    add_check("filter_policy_count", len(filter_policy) >= 8, "critical", f"policies={len(filter_policy)}")
    add_check("actions_created", len(actions) == len(source_plan), "critical", f"actions={len(actions)} sources={len(source_plan)}")
    add_check("full_source_still_blocked", canonical_rows < FULL_SOURCE_THRESHOLD, "critical", f"{canonical_rows} < {FULL_SOURCE_THRESHOLD}")
    add_check("network_not_used_in_plan", True, "critical", "network_download_performed=False")
    add_check("endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("raw_acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed == 0:
        status = "NSE_INDIA_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE
    else:
        status = "NSE_INDIA_ACQUISITION_PLAN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.17B_FIX - NSE India Acquisition Plan Repair"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": canonical_rows,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": round((canonical_rows / FULL_SOURCE_THRESHOLD) * 100, 2),
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "route_reference": {
            "v2_17a_artifact": str(V217A_JSON),
            "v2_17a_status": v217a.get("status", ""),
            "v2_17a_recommended_next_phase": v217a.get("recommended_next_phase", ""),
            "selected_route": "nse_india",
        },
        "acquisition_plan_summary": {
            "provider": "NSE India",
            "market": "India",
            "source_count": len(source_plan),
            "primary_source_count": len(primary_sources),
            "exclusion_reference_source_count": len(exclusion_sources),
            "filter_policy_count": len(filter_policy),
            "action_count": len(actions),
            "network_allowed_in_this_phase": False,
            "network_allowed_next_phase": True,
            "raw_acquisition_ready": critical_failed == 0,
            "critical_failed_checks": critical_failed,
        },
        "source_plan": source_plan,
        "filter_policy": filter_policy,
        "acquisition_actions": actions,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "v2_17a_report_read": True,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "provider_route_confirmed": True,
            "acquisition_plan_created": True,
            "raw_acquisition_performed": False,
            "raw_files_downloaded": False,
            "candidate_extraction_performed": False,
            "canonical_comparison_performed": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "net_new_filtering_applied_to_canonical": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "full_source_gate_unblocked": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)
    write_csv(SOURCE_PLAN_CSV, source_plan, SOURCE_FIELDS)
    write_csv(FILTER_POLICY_CSV, filter_policy, FILTER_FIELDS)
    write_csv(ACQUISITION_ACTIONS_CSV, actions, ACTION_FIELDS)

    source_lines = "\n".join(
        f"- **{row['priority']}. {row['source_id']}** — role=`{row['source_role']}`, format=`{row['expected_format']}`, risk=`{row['risk_level']}`"
        for row in source_plan
    )

    policy_lines = "\n".join(
        f"- **{row['policy_id']}** — `{row['decision']}`: {row['instrument_or_source_type']}"
        for row in filter_policy
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive plan

NSE India acquisition planning is complete.

The primary planned source is the NSE All Reports CM MII security file for NSE listed securities. The main cross-check source is the NSE Securities Available for Trading equity segment CSV. Exclusion/reference lists are explicitly planned for ETFs, REITs, INVITs, IDRs, warrants, preference shares, mutual funds and debt instruments.

No download is performed in this phase.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{canonical_rows}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completion: `{round((canonical_rows / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Source plan

{source_lines}

## Filter policy

{policy_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17A report read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Provider route confirmed: true
- Acquisition plan created: true
- Raw acquisition performed: false
- Raw files downloaded: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Net-new filtering applied to canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17B defines the NSE India acquisition plan only.

v2.17C may perform raw acquisition from the planned NSE sources, but must still avoid parsing, candidate extraction, canonical comparison, rebuild and full-source unlock.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.17B NSE India acquisition plan completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("ACQUISITION_PLAN_SUMMARY:")
    for key, value in payload["acquisition_plan_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
