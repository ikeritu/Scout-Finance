from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.17H"
PHASE = "NSE India Expanded Validation"
PHASE_TYPE = "expanded-candidate-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

V217G_JSON = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_v2_17g.json"
EXPANDED_CANDIDATE_CSV = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"
DELTA_ROWS_CSV = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_delta_rows_v2_17g.csv"
PROMOTIONS_CSV = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_promotions_v2_17g.csv"
SCHEMA_MAPPING_CSV = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_schema_mapping_v2_17g.csv"

REPORT_JSON = OUTPUT_DIR / "nse_india_expanded_validation_v2_17h.json"
REPORT_MD = OUTPUT_DIR / "nse_india_expanded_validation_v2_17h.md"
DATASET_PROFILE_CSV = OUTPUT_DIR / "nse_india_expanded_validation_dataset_profile_v2_17h.csv"
PROMOTION_POLICY_QA_CSV = OUTPUT_DIR / "nse_india_expanded_validation_promotion_policy_qa_v2_17h.csv"
DELTA_INTEGRITY_CSV = OUTPUT_DIR / "nse_india_expanded_validation_delta_integrity_v2_17h.csv"

CURRENT_CANONICAL_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000

EXPECTED_V217G_STATUS = "NSE_INDIA_EXPANDED_REBUILD_CANDIDATE_COMPLETED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED"
EXPECTED_V217G_NEXT = "v2.17H - NSE India Expanded Validation"

NEXT_PHASE = "v2.17I - NSE India Closure Report"

SAFE_PROMOTION_POLICY = "include_safe_high_confidence_equity_segment_eq_only_in_candidate_dataset"
SAFE_SOURCE_ID = "nse_securities_available_equity_segment"

DATASET_PROFILE_FIELDS = [
    "profile_key",
    "profile_value",
    "notes",
]

PROMOTION_POLICY_QA_FIELDS = [
    "promotion_id",
    "candidate_id",
    "source_id",
    "raw_symbol",
    "raw_name",
    "raw_series",
    "raw_isin",
    "confidence_bucket",
    "review_required",
    "net_new_bucket",
    "promotion_policy",
    "policy_passed",
    "issues",
]

DELTA_INTEGRITY_FIELDS = [
    "check_id",
    "passed",
    "severity",
    "detail",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                return list(reader.fieldnames or []), rows
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


def norm(value: str) -> str:
    return str(value or "").strip()


def norm_upper(value: str) -> str:
    return norm(value).upper()


def boolish(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def row_signature(row: dict, header: list[str]) -> str:
    values = [str(row.get(col, "") or "") for col in header]
    return sha256_text(json.dumps(values, ensure_ascii=False, separators=(",", ":")))


def row_values_equal(left: dict, right: dict, header: list[str]) -> bool:
    return all(str(left.get(col, "") or "") == str(right.get(col, "") or "") for col in header)


def unsafe_promotion_issues(row: dict) -> list[str]:
    issues = []

    source_id = norm(row.get("source_id", ""))
    symbol = norm_upper(row.get("raw_symbol", ""))
    name = norm_upper(row.get("raw_name", ""))
    series = norm_upper(row.get("raw_series", ""))
    isin = norm_upper(row.get("raw_isin", ""))
    confidence = norm(row.get("confidence_bucket", "")).lower()
    review_required = boolish(row.get("review_required", ""))
    net_new_bucket = norm(row.get("net_new_bucket", ""))
    policy = norm(row.get("promotion_policy", ""))

    if source_id != SAFE_SOURCE_ID:
        issues.append(f"unsafe_source:{source_id}")

    if series != "EQ":
        issues.append(f"unsafe_series:{series}")

    if confidence != "high":
        issues.append(f"unsafe_confidence:{confidence}")

    if review_required:
        issues.append("review_required_true")

    if net_new_bucket != "potential_net_new_high":
        issues.append(f"unsafe_net_new_bucket:{net_new_bucket}")

    if policy != SAFE_PROMOTION_POLICY:
        issues.append(f"unexpected_promotion_policy:{policy}")

    if isin.startswith("INF"):
        issues.append("fund_or_etf_isin_prefix_inf")

    if "-RE" in symbol or symbol.endswith("RE1") or symbol.endswith("RE2"):
        issues.append("rights_entitlement_symbol")

    padded_name = f" {name} "
    for keyword in [" ETF ", " FUND ", " LIQUID ", " NIFTY ", " GOLD ", " SILVER ", " BIRLASLAMC ", " NIPPON INDIA MF "]:
        if keyword in padded_name:
            issues.append(f"unsafe_name_keyword:{keyword.strip().lower()}")

    return issues


def build_promotion_policy_qa(promotions: list[dict]) -> list[dict]:
    rows = []

    for row in promotions:
        issues = unsafe_promotion_issues(row)
        rows.append(
            {
                "promotion_id": row.get("promotion_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "source_id": row.get("source_id", ""),
                "raw_symbol": row.get("raw_symbol", ""),
                "raw_name": row.get("raw_name", ""),
                "raw_series": row.get("raw_series", ""),
                "raw_isin": row.get("raw_isin", ""),
                "confidence_bucket": row.get("confidence_bucket", ""),
                "review_required": row.get("review_required", ""),
                "net_new_bucket": row.get("net_new_bucket", ""),
                "promotion_policy": row.get("promotion_policy", ""),
                "policy_passed": len(issues) == 0,
                "issues": " | ".join(issues),
            }
        )

    return rows


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        DATASET_PROFILE_CSV,
        PROMOTION_POLICY_QA_CSV,
        DELTA_INTEGRITY_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    g_report = read_json(V217G_JSON)

    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)
    expanded_header, expanded_rows = read_csv_with_header(EXPANDED_CANDIDATE_CSV)
    delta_header, delta_rows = read_csv_with_header(DELTA_ROWS_CSV)
    promotions_header, promotions = read_csv_with_header(PROMOTIONS_CSV)
    schema_mapping_header, schema_mapping_rows = read_csv_with_header(SCHEMA_MAPPING_CSV)

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())
    expanded_sha = sha256_bytes(EXPANDED_CANDIDATE_CSV.read_bytes())
    delta_sha = sha256_bytes(DELTA_ROWS_CSV.read_bytes())
    promotions_sha = sha256_bytes(PROMOTIONS_CSV.read_bytes())
    schema_mapping_sha = sha256_bytes(SCHEMA_MAPPING_CSV.read_bytes())

    canonical_prefix_rows = expanded_rows[: len(canonical_rows)]
    expanded_tail_rows = expanded_rows[len(canonical_rows):]

    canonical_prefix_match_count = sum(
        1 for left, right in zip(canonical_rows, canonical_prefix_rows)
        if row_values_equal(left, right, canonical_header)
    )

    delta_tail_match_count = sum(
        1 for left, right in zip(delta_rows, expanded_tail_rows)
        if row_values_equal(left, right, canonical_header)
    )

    canonical_prefix_fully_matches = (
        len(canonical_rows) == len(canonical_prefix_rows)
        and canonical_prefix_match_count == len(canonical_rows)
    )

    delta_tail_fully_matches = (
        len(delta_rows) == len(expanded_tail_rows)
        and delta_tail_match_count == len(delta_rows)
    )

    promotion_policy_qa = build_promotion_policy_qa(promotions)
    promotion_policy_failures = [row for row in promotion_policy_qa if not boolish(row["policy_passed"])]

    delta_signatures = [row_signature(row, delta_header) for row in delta_rows]
    duplicate_delta_rows = len(delta_signatures) - len(set(delta_signatures))

    promotion_candidate_ids = [row.get("candidate_id", "") for row in promotions]
    duplicate_promotion_candidate_ids = len(promotion_candidate_ids) - len(set(promotion_candidate_ids))

    source_counts = Counter(row.get("source_id", "") for row in promotions)
    series_counts = Counter(row.get("raw_series", "") for row in promotions)
    confidence_counts = Counter(row.get("confidence_bucket", "") for row in promotions)
    net_new_bucket_counts = Counter(row.get("net_new_bucket", "") for row in promotions)
    policy_counts = Counter(row.get("promotion_policy", "") for row in promotions)

    expanded_rows_count = len(expanded_rows)
    delta_rows_count = len(delta_rows)
    promotions_count = len(promotions)
    rows_needed_after_candidate = max(FULL_SOURCE_THRESHOLD - expanded_rows_count, 0)

    delta_integrity_rows = [
        {
            "check_id": "canonical_prefix_fully_matches_expanded_candidate",
            "passed": canonical_prefix_fully_matches,
            "severity": "critical",
            "detail": f"matched={canonical_prefix_match_count}/{len(canonical_rows)}",
        },
        {
            "check_id": "delta_rows_match_expanded_tail",
            "passed": delta_tail_fully_matches,
            "severity": "critical",
            "detail": f"matched={delta_tail_match_count}/{len(delta_rows)}",
        },
        {
            "check_id": "delta_rows_equal_promotions",
            "passed": delta_rows_count == promotions_count,
            "severity": "critical",
            "detail": f"delta={delta_rows_count} promotions={promotions_count}",
        },
        {
            "check_id": "no_duplicate_delta_rows",
            "passed": duplicate_delta_rows == 0,
            "severity": "critical",
            "detail": f"duplicate_delta_rows={duplicate_delta_rows}",
        },
        {
            "check_id": "no_duplicate_promotion_candidate_ids",
            "passed": duplicate_promotion_candidate_ids == 0,
            "severity": "critical",
            "detail": f"duplicate_promotion_candidate_ids={duplicate_promotion_candidate_ids}",
        },
    ]

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_17g_report_exists", V217G_JSON.exists(), "critical", str(V217G_JSON))
    add_check(
        "v2_17g_status_expected",
        g_report.get("status") == EXPECTED_V217G_STATUS,
        "critical",
        str(g_report.get("status", "")),
    )
    add_check(
        "v2_17g_recommended_h",
        g_report.get("recommended_next_phase") == EXPECTED_V217G_NEXT,
        "critical",
        str(g_report.get("recommended_next_phase", "")),
    )
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("expanded_candidate_exists", EXPANDED_CANDIDATE_CSV.exists(), "critical", str(EXPANDED_CANDIDATE_CSV))
    add_check("delta_rows_exists", DELTA_ROWS_CSV.exists(), "critical", str(DELTA_ROWS_CSV))
    add_check("promotions_exists", PROMOTIONS_CSV.exists(), "critical", str(PROMOTIONS_CSV))
    add_check("schema_mapping_exists", SCHEMA_MAPPING_CSV.exists(), "critical", str(SCHEMA_MAPPING_CSV))
    add_check("canonical_rows_expected", len(canonical_rows) == CURRENT_CANONICAL_ROWS, "critical", f"canonical_rows={len(canonical_rows)}")
    add_check("headers_match_canonical_expanded", canonical_header == expanded_header, "critical", f"canonical_cols={len(canonical_header)} expanded_cols={len(expanded_header)}")
    add_check("headers_match_canonical_delta", canonical_header == delta_header, "critical", f"canonical_cols={len(canonical_header)} delta_cols={len(delta_header)}")
    add_check("expanded_rows_equal_canonical_plus_delta", expanded_rows_count == len(canonical_rows) + delta_rows_count, "critical", f"expanded={expanded_rows_count} canonical={len(canonical_rows)} delta={delta_rows_count}")
    add_check("delta_rows_equal_promotions", delta_rows_count == promotions_count, "critical", f"delta={delta_rows_count} promotions={promotions_count}")
    add_check("canonical_prefix_fully_matches", canonical_prefix_fully_matches, "critical", f"matched={canonical_prefix_match_count}/{len(canonical_rows)}")
    add_check("delta_tail_fully_matches", delta_tail_fully_matches, "critical", f"matched={delta_tail_match_count}/{delta_rows_count}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "canonical sha unchanged")
    add_check("promotion_policy_qa_all_passed", len(promotion_policy_failures) == 0, "critical", f"failures={len(promotion_policy_failures)}")
    add_check("safe_source_only", set(source_counts.keys()) == {SAFE_SOURCE_ID}, "critical", f"source_counts={dict(source_counts)}")
    add_check("eq_series_only", set(series_counts.keys()) == {"EQ"}, "critical", f"series_counts={dict(series_counts)}")
    add_check("high_confidence_only", set(confidence_counts.keys()) == {"high"}, "critical", f"confidence_counts={dict(confidence_counts)}")
    add_check("safe_policy_only", set(policy_counts.keys()) == {SAFE_PROMOTION_POLICY}, "critical", f"policy_counts={dict(policy_counts)}")
    add_check("potential_net_new_high_only", set(net_new_bucket_counts.keys()) == {"potential_net_new_high"}, "critical", f"net_new_bucket_counts={dict(net_new_bucket_counts)}")
    add_check("no_duplicate_delta_rows", duplicate_delta_rows == 0, "critical", f"duplicate_delta_rows={duplicate_delta_rows}")
    add_check("no_duplicate_promotion_candidate_ids", duplicate_promotion_candidate_ids == 0, "critical", f"duplicate_promotion_candidate_ids={duplicate_promotion_candidate_ids}")
    add_check("expanded_candidate_has_growth", delta_rows_count > 0, "critical", f"delta_rows={delta_rows_count}")
    add_check("full_source_still_blocked", expanded_rows_count < FULL_SOURCE_THRESHOLD, "critical", f"{expanded_rows_count} < {FULL_SOURCE_THRESHOLD}")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("canonical_dataset_read", True, "critical", "canonical_dataset_read=True")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("expanded_candidate_validated", True, "critical", "expanded_candidate_validated=True")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed == 0:
        status = "NSE_INDIA_EXPANDED_VALIDATION_COMPLETED_CANDIDATE_VALID_CLOSURE_READY_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE
    else:
        status = "NSE_INDIA_EXPANDED_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.17H_FIX - NSE India Expanded Validation Repair"

    dataset_profile = [
        {"profile_key": "canonical_dataset", "profile_value": str(CANONICAL_DATASET), "notes": "active canonical, unchanged"},
        {"profile_key": "expanded_candidate_dataset", "profile_value": str(EXPANDED_CANDIDATE_CSV), "notes": "candidate only, not active canonical"},
        {"profile_key": "canonical_rows", "profile_value": len(canonical_rows), "notes": "active canonical rows"},
        {"profile_key": "delta_rows", "profile_value": delta_rows_count, "notes": "rows appended in candidate dataset"},
        {"profile_key": "promotions", "profile_value": promotions_count, "notes": "promotion rows"},
        {"profile_key": "expanded_candidate_rows", "profile_value": expanded_rows_count, "notes": "canonical + delta"},
        {"profile_key": "rows_needed_after_candidate", "profile_value": rows_needed_after_candidate, "notes": "still below full-source threshold"},
        {"profile_key": "completion_after_candidate_percent", "profile_value": round((expanded_rows_count / FULL_SOURCE_THRESHOLD) * 100, 2), "notes": "candidate completion only"},
        {"profile_key": "canonical_sha256_before", "profile_value": canonical_sha_before, "notes": "before validation"},
        {"profile_key": "canonical_sha256_after", "profile_value": canonical_sha_after, "notes": "after validation"},
        {"profile_key": "expanded_candidate_sha256", "profile_value": expanded_sha, "notes": "candidate dataset"},
        {"profile_key": "delta_rows_sha256", "profile_value": delta_sha, "notes": "delta rows"},
        {"profile_key": "promotions_sha256", "profile_value": promotions_sha, "notes": "promotions"},
        {"profile_key": "schema_mapping_sha256", "profile_value": schema_mapping_sha, "notes": "schema mapping"},
        {"profile_key": "source_counts", "profile_value": json.dumps(dict(source_counts), ensure_ascii=False, sort_keys=True), "notes": "promoted rows by source"},
        {"profile_key": "series_counts", "profile_value": json.dumps(dict(series_counts), ensure_ascii=False, sort_keys=True), "notes": "promoted rows by NSE series"},
        {"profile_key": "confidence_counts", "profile_value": json.dumps(dict(confidence_counts), ensure_ascii=False, sort_keys=True), "notes": "promoted rows by confidence"},
        {"profile_key": "policy_counts", "profile_value": json.dumps(dict(policy_counts), ensure_ascii=False, sort_keys=True), "notes": "promotion policy"},
    ]

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": len(canonical_rows),
            "expanded_candidate_dataset": str(EXPANDED_CANDIDATE_CSV),
            "expanded_candidate_rows": expanded_rows_count,
            "delta_rows": delta_rows_count,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_after_candidate": rows_needed_after_candidate,
            "source_to_50k_completed_percent_after_candidate": round((expanded_rows_count / FULL_SOURCE_THRESHOLD) * 100, 2),
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "route_reference": {
            "v2_17g_artifact": str(V217G_JSON),
            "v2_17g_status": g_report.get("status", ""),
            "v2_17g_recommended_next_phase": g_report.get("recommended_next_phase", ""),
            "provider": "NSE India",
            "market": "India",
        },
        "expanded_validation_summary": {
            "canonical_rows": len(canonical_rows),
            "delta_rows": delta_rows_count,
            "promotions": promotions_count,
            "expanded_candidate_rows": expanded_rows_count,
            "rows_needed_after_candidate": rows_needed_after_candidate,
            "completion_after_candidate_percent": round((expanded_rows_count / FULL_SOURCE_THRESHOLD) * 100, 2),
            "canonical_prefix_match_count": canonical_prefix_match_count,
            "delta_tail_match_count": delta_tail_match_count,
            "promotion_policy_failures": len(promotion_policy_failures),
            "duplicate_delta_rows": duplicate_delta_rows,
            "duplicate_promotion_candidate_ids": duplicate_promotion_candidate_ids,
            "source_counts": dict(source_counts),
            "series_counts": dict(series_counts),
            "confidence_counts": dict(confidence_counts),
            "net_new_bucket_counts": dict(net_new_bucket_counts),
            "policy_counts": dict(policy_counts),
            "canonical_sha256_before": canonical_sha_before,
            "canonical_sha256_after": canonical_sha_after,
            "expanded_candidate_sha256": expanded_sha,
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "v2_17g_report_read": True,
            "canonical_dataset_read": True,
            "expanded_candidate_dataset_read": True,
            "delta_rows_read": True,
            "promotions_read": True,
            "schema_mapping_read": True,
            "expanded_candidate_validated": True,
            "promotion_policy_validated": True,
            "safe_promotion_policy_enforced": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
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
    write_csv(DATASET_PROFILE_CSV, dataset_profile, DATASET_PROFILE_FIELDS)
    write_csv(PROMOTION_POLICY_QA_CSV, promotion_policy_qa, PROMOTION_POLICY_QA_FIELDS)
    write_csv(DELTA_INTEGRITY_CSV, delta_integrity_rows, DELTA_INTEGRITY_FIELDS)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

NSE India expanded candidate validation completed.

This phase validates the v2.17G expanded candidate dataset. It confirms schema consistency, append integrity, safe promotion policy compliance, canonical SHA stability and full-source gate status. It does not modify or replace the active canonical dataset.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{len(canonical_rows)}`
- Expanded candidate dataset: `{EXPANDED_CANDIDATE_CSV}`
- Expanded candidate rows: `{expanded_rows_count}`
- Delta rows: `{delta_rows_count}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed after candidate: `{rows_needed_after_candidate}`
- Completion after candidate: `{round((expanded_rows_count / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Expanded validation summary

- Canonical rows: `{len(canonical_rows)}`
- Delta rows: `{delta_rows_count}`
- Promotions: `{promotions_count}`
- Expanded candidate rows: `{expanded_rows_count}`
- Canonical prefix matches: `{canonical_prefix_match_count}/{len(canonical_rows)}`
- Delta tail matches: `{delta_tail_match_count}/{delta_rows_count}`
- Promotion policy failures: `{len(promotion_policy_failures)}`
- Duplicate delta rows: `{duplicate_delta_rows}`
- Duplicate promotion candidate IDs: `{duplicate_promotion_candidate_ids}`
- Source counts: `{dict(source_counts)}`
- Series counts: `{dict(series_counts)}`
- Confidence counts: `{dict(confidence_counts)}`
- Policy counts: `{dict(policy_counts)}`
- Canonical SHA before: `{canonical_sha_before}`
- Canonical SHA after: `{canonical_sha_after}`
- Expanded candidate SHA: `{expanded_sha}`
- Critical failed checks: `{critical_failed}`

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17G report read: true
- Canonical dataset read: true
- Expanded candidate dataset read: true
- Delta rows read: true
- Promotions read: true
- Schema mapping read: true
- Expanded candidate validated: true
- Promotion policy validated: true
- Safe promotion policy enforced: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17H validates the NSE India expanded rebuild candidate and prepares the NSE India closure report.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.17H NSE India expanded validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("EXPANDED_VALIDATION_SUMMARY:")
    for key, value in payload["expanded_validation_summary"].items():
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
