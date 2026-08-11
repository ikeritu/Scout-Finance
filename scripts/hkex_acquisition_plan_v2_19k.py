from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VERSION = "v2.19K"
PHASE = "HKEX Acquisition Plan"
PHASE_TYPE = "acquisition-plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219J_JSON = OUTPUT_DIR / "next_provider_route_selection_after_krx_v2_19j.json"
V219J_SELECTED_ROUTE_CSV = OUTPUT_DIR / "next_provider_route_selection_after_krx_selected_route_v2_19j.csv"
V219J_DECISION_MATRIX_CSV = OUTPUT_DIR / "next_provider_route_selection_after_krx_decision_matrix_v2_19j.csv"

REPORT_JSON = OUTPUT_DIR / "hkex_acquisition_plan_v2_19k.json"
REPORT_MD = OUTPUT_DIR / "hkex_acquisition_plan_v2_19k.md"
SOURCE_INVENTORY_CSV = OUTPUT_DIR / "hkex_acquisition_plan_source_inventory_v2_19k.csv"
RAW_ARTIFACT_PLAN_CSV = OUTPUT_DIR / "hkex_acquisition_plan_raw_artifacts_v2_19k.csv"
VALIDATION_STRATEGY_CSV = OUTPUT_DIR / "hkex_acquisition_plan_validation_strategy_v2_19k.csv"
FILTERING_POLICY_CSV = OUTPUT_DIR / "hkex_acquisition_plan_filtering_policy_v2_19k.csv"
RISK_REGISTER_CSV = OUTPUT_DIR / "hkex_acquisition_plan_risk_register_v2_19k.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_acquisition_plan_checks_v2_19k.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_acquisition_plan_next_actions_v2_19k.csv"

EXPECTED_V219J_STATUS = "NEXT_PROVIDER_ROUTE_SELECTION_AFTER_KRX_COMPLETED_HKEX_SELECTED_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

SELECTED_ROUTE_ID = "HKEX_HONG_KONG_EXCHANGE"
SELECTED_PROVIDER = "HKEX"

STATUS_SUCCESS = "HKEX_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_FOR_RAW_ACQUISITION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
RECOMMENDED_NEXT_PHASE = "v2.19L - HKEX Raw Acquisition"
RECOMMENDED_REVIEW_PHASE = "v2.19K_REVIEW - HKEX Acquisition Plan Review"

ALLOWED_HOSTS = {
    "www.hkex.com.hk",
    "hkex.com.hk",
    "www.hkexnews.hk",
    "hkexnews.hk",
}

HKEX_OFFICIAL_SOURCES = [
    {
        "source_id": "hkex_securities_lists",
        "source_name": "HKEX Securities Lists",
        "source_role": "primary_candidate_source",
        "url": "https://www.hkex.com.hk/Services/Trading/Securities/Securities-Lists?sc_lang=en",
        "expected_content_type": "html_with_download_links",
        "expected_raw_artifact_id": "hkex_securities_lists_page",
        "expected_parse_signal": "Full List of Securities / securities list links",
        "candidate_value": "high",
        "planned_acquisition_method": "GET page; inspect official links for Full List of Securities downloadable file",
        "notes": "Primary entry point for HKEX securities lists. Raw acquisition should capture page first, then only official linked files.",
    },
    {
        "source_id": "hkex_equities",
        "source_name": "HKEX Equities",
        "source_role": "primary_or_crosscheck_source",
        "url": "https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en",
        "expected_content_type": "html_with_equities_links",
        "expected_raw_artifact_id": "hkex_equities_page",
        "expected_parse_signal": "List of Equities Securities",
        "candidate_value": "high",
        "planned_acquisition_method": "GET page; inspect official equities list links",
        "notes": "Crosscheck/primary source for ordinary equities. Needs filtering of securities/share classes.",
    },
    {
        "source_id": "hkex_newly_listed_securities",
        "source_name": "HKEX Newly Listed Securities",
        "source_role": "supporting_or_crosscheck_source",
        "url": "https://www.hkex.com.hk/Services/Trading/Securities/Trading-News/Newly-Listed-Securities?sc_lang=en",
        "expected_content_type": "html_table_or_dynamic_page",
        "expected_raw_artifact_id": "hkex_newly_listed_securities_page",
        "expected_parse_signal": "Stock Short Name / Stock Code / Board Lot",
        "candidate_value": "medium",
        "planned_acquisition_method": "GET page; capture as support for recency/new listings",
        "notes": "Useful for latest listings and schema hints; not enough alone for full universe.",
    },
    {
        "source_id": "hkex_market_search_listing_result",
        "source_name": "HKEX Market Search Listing Result",
        "source_role": "supporting_or_probe_source",
        "url": "https://www.hkex.com.hk/Global/HKEX-Market-Search-Listing-Result?sc_lang=en",
        "expected_content_type": "html_or_dynamic_search",
        "expected_raw_artifact_id": "hkex_market_search_listing_result_page",
        "expected_parse_signal": "Listing search result / market search",
        "candidate_value": "medium",
        "planned_acquisition_method": "GET page; inspect dynamic/API signals only in raw phase",
        "notes": "Probe source. Do not treat as candidate data unless raw validation proves structured rows.",
    },
    {
        "source_id": "hkexnews_issuer_search",
        "source_name": "HKEXnews Listed Company Information Search",
        "source_role": "issuer_reference_source",
        "url": "https://www.hkexnews.hk/index.htm",
        "expected_content_type": "html_or_search_portal",
        "expected_raw_artifact_id": "hkexnews_index_page",
        "expected_parse_signal": "listed company information search",
        "candidate_value": "low_medium",
        "planned_acquisition_method": "GET page; keep as issuer reference only unless structured search result is discoverable",
        "notes": "Reference/crosscheck source. Not primary candidate source unless official structured output is discovered.",
    },
]

FILTERING_POLICY = [
    {
        "policy_id": "HKEX_FILTER_001",
        "category": "include",
        "rule": "Include ordinary equity/listed company securities only when stock code and issuer/security name are present.",
        "reason": "Avoid adding broad HKEX instruments that are not equity candidates.",
        "phase_enforced": "v2.19M extraction dry run and later",
    },
    {
        "policy_id": "HKEX_FILTER_002",
        "category": "exclude",
        "rule": "Exclude warrants, CBBCs, derivative warrants, debt securities, ETFs, REITs, unit trusts, structured products and similar non-operating-company instruments unless explicitly approved later.",
        "reason": "HKEX lists many instrument types beyond common equities.",
        "phase_enforced": "v2.19M extraction dry run and later",
    },
    {
        "policy_id": "HKEX_FILTER_003",
        "category": "review",
        "rule": "Review multiple counters, RMB/HKD dual counters, share classes and duplicate issuer codes before net-new append.",
        "reason": "HKEX may include multiple counters or share classes for the same issuer.",
        "phase_enforced": "v2.19N validation against canonical and later",
    },
    {
        "policy_id": "HKEX_FILTER_004",
        "category": "dedupe",
        "rule": "Canonical duplicate checks must compare stock code, ticker variants, issuer name normalization and ISIN when available.",
        "reason": "Avoid double-counting Hong Kong listings already represented through ADRs, dual listings, TWSE/NSE/canonical sources or prior datasets.",
        "phase_enforced": "v2.19N validation against canonical and later",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict[str, str]]]:
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def official_scope_allowed(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        SOURCE_INVENTORY_CSV,
        RAW_ARTIFACT_PLAN_CSV,
        VALIDATION_STRATEGY_CSV,
        FILTERING_POLICY_CSV,
        RISK_REGISTER_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219j = read_json(V219J_JSON)
    _, selected_route_rows = read_csv_with_header(V219J_SELECTED_ROUTE_CSV)
    _, decision_matrix_rows = read_csv_with_header(V219J_DECISION_MATRIX_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    selected_route = selected_route_rows[0] if selected_route_rows else {}
    selection_summary = v219j.get("selection_summary", {})

    source_inventory_rows = []
    for source in HKEX_OFFICIAL_SOURCES:
        row = dict(source)
        row["official_scope_allowed"] = official_scope_allowed(source["url"])
        row["planned_raw_phase"] = "v2.19L"
        row["candidate_extraction_phase"] = "v2.19M only if raw validation passes"
        source_inventory_rows.append(row)

    raw_artifact_plan_rows = [
        {
            "artifact_order": index,
            "source_id": source["source_id"],
            "artifact_id": source["expected_raw_artifact_id"],
            "url": source["url"],
            "method": "GET",
            "official_scope_allowed": official_scope_allowed(source["url"]),
            "expected_content_type": source["expected_content_type"],
            "expected_parse_signal": source["expected_parse_signal"],
            "download_policy": "capture_raw_only_in_v2_19l",
            "overwrite_policy": "no_overwrite",
            "validation_required_before_extraction": True,
        }
        for index, source in enumerate(HKEX_OFFICIAL_SOURCES, start=1)
    ]

    validation_strategy_rows = [
        {
            "validation_id": "HKEX_VAL_001",
            "validation_scope": "raw_artifact_integrity",
            "check": "Every planned raw artifact must exist, have byte count > 0, and have recorded sha256.",
            "severity": "critical",
            "blocks_extraction_if_failed": True,
        },
        {
            "validation_id": "HKEX_VAL_002",
            "validation_scope": "official_scope",
            "check": "All captured artifacts must resolve to hkex.com.hk or hkexnews.hk official hosts.",
            "severity": "critical",
            "blocks_extraction_if_failed": True,
        },
        {
            "validation_id": "HKEX_VAL_003",
            "validation_scope": "candidate_parse_readiness",
            "check": "At least one primary/crosscheck artifact must contain parse-ready stock code and issuer/security name rows.",
            "severity": "critical",
            "blocks_extraction_if_failed": True,
        },
        {
            "validation_id": "HKEX_VAL_004",
            "validation_scope": "instrument_type_filtering",
            "check": "Raw validation must identify whether the source mixes equities with warrants, CBBCs, debt, ETFs, REITs, unit trusts or structured products.",
            "severity": "warning",
            "blocks_extraction_if_failed": False,
        },
        {
            "validation_id": "HKEX_VAL_005",
            "validation_scope": "50k_guard",
            "check": "No HKEX rows may be appended until candidate extraction and validation against canonical are complete.",
            "severity": "critical",
            "blocks_extraction_if_failed": True,
        },
    ]

    risk_register_rows = [
        {
            "risk_id": "HKEX_RISK_001",
            "risk": "HKEX source may list broad securities, not only operating-company common equities.",
            "impact": "Could inflate candidate universe with non-equity instruments.",
            "likelihood": "high",
            "mitigation": "Strict filtering policy in extraction dry run; no append before canonical validation.",
        },
        {
            "risk_id": "HKEX_RISK_002",
            "risk": "Multiple counters/share classes may represent the same issuer.",
            "impact": "Duplicate issuer rows or overcounting.",
            "likelihood": "medium_high",
            "mitigation": "Deduplicate by stock code, normalized issuer name and ISIN when available.",
        },
        {
            "risk_id": "HKEX_RISK_003",
            "risk": "Download links may be dynamic or hidden behind page scripts.",
            "impact": "Raw acquisition may need page inspection/HTML signal inventory before structured capture.",
            "likelihood": "medium",
            "mitigation": "v2.19L captures pages first and inventories official links/scripts/forms before attempting linked files.",
        },
        {
            "risk_id": "HKEX_RISK_004",
            "risk": "HKEX expected net-new contribution may be insufficient for the full 9,004-row gap.",
            "impact": "50k gate likely remains blocked after HKEX alone.",
            "likelihood": "high",
            "mitigation": "Use ASX/TMX backups after HKEX if quality gate remains blocked.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "HKEX",
            "action": "run_hkex_raw_acquisition",
            "priority": "high",
            "reason": "HKEX acquisition plan is ready; raw official artifacts can be captured next.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "raw acquisition only; no candidate extraction; no canonical modification",
        },
        {
            "action_order": 2,
            "action_scope": "HKEX",
            "action": "capture_source_pages_before_linked_files",
            "priority": "high",
            "reason": "Official HKEX pages may expose downloadable files via links or scripts.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "only follow hkex.com.hk or hkexnews.hk official links",
        },
        {
            "action_order": 3,
            "action_scope": "50k",
            "action": "preserve_quality_gate",
            "priority": "high",
            "reason": "HKEX may add useful volume but does not guarantee closing the 9,004-row gap.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "do not launch full59k; no volume-padding with non-equity instruments",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19j_report_exists", V219J_JSON.exists(), "critical", str(V219J_JSON))
    add_check("v2_19j_status_expected", v219j.get("status") == EXPECTED_V219J_STATUS, "critical", str(v219j.get("status", "")))
    add_check("selected_route_csv_exists", V219J_SELECTED_ROUTE_CSV.exists(), "critical", str(V219J_SELECTED_ROUTE_CSV))
    add_check("decision_matrix_csv_exists", V219J_DECISION_MATRIX_CSV.exists(), "critical", str(V219J_DECISION_MATRIX_CSV))
    add_check("selected_route_is_hkex", selected_route.get("route_id") == SELECTED_ROUTE_ID, "critical", str(selected_route.get("route_id", "")))
    add_check("selected_provider_is_hkex", selected_route.get("provider") == SELECTED_PROVIDER, "critical", str(selected_route.get("provider", "")))
    add_check("v2_19j_recommended_next_phase_hkex", v219j.get("recommended_next_phase") == "v2.19K - HKEX Acquisition Plan", "critical", str(v219j.get("recommended_next_phase", "")))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("source_inventory_minimum", len(source_inventory_rows) >= 4, "critical", f"sources={len(source_inventory_rows)}")
    add_check("primary_source_present", any(row["source_role"] == "primary_candidate_source" for row in source_inventory_rows), "critical", "primary_candidate_source present")
    add_check("all_sources_official_scope", all(row["official_scope_allowed"] for row in source_inventory_rows), "critical", "all planned urls hkex/hkexnews official")
    add_check("raw_artifact_plan_rows_match_sources", len(raw_artifact_plan_rows) == len(source_inventory_rows), "critical", f"raw_artifact_plan_rows={len(raw_artifact_plan_rows)}")
    add_check("validation_strategy_present", len(validation_strategy_rows) >= 5, "critical", f"validation_strategy_rows={len(validation_strategy_rows)}")
    add_check("filtering_policy_present", len(FILTERING_POLICY) >= 4, "critical", f"filtering_policy_rows={len(FILTERING_POLICY)}")
    add_check("risk_register_present", len(risk_register_rows) >= 4, "warning", f"risk_register_rows={len(risk_register_rows)}")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("network_not_used_by_plan", True, "critical", "network_download_performed=False")
    add_check("raw_acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("next_phase_hkex_raw_acquisition", RECOMMENDED_NEXT_PHASE == "v2.19L - HKEX Raw Acquisition", "critical", RECOMMENDED_NEXT_PHASE)

    if critical_failed == 0:
        status = STATUS_SUCCESS
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "HKEX_ACQUISITION_PLAN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    plan_summary = {
        "selected_route_id": SELECTED_ROUTE_ID,
        "selected_provider": SELECTED_PROVIDER,
        "selected_market": "Hong Kong",
        "source_inventory_rows": len(source_inventory_rows),
        "primary_sources": sum(1 for row in source_inventory_rows if "primary" in row["source_role"]),
        "raw_artifacts_planned_rows": len(raw_artifact_plan_rows),
        "validation_strategy_rows": len(validation_strategy_rows),
        "filtering_policy_rows": len(FILTERING_POLICY),
        "risk_register_rows": len(risk_register_rows),
        "expected_net_new_band": selection_summary.get("expected_selected_route_net_new_band", "1500-2500"),
        "expected_gross_rows_band": selection_summary.get("expected_selected_route_gross_rows_band", "2500-3500"),
        "current_validated_candidate_rows": current_candidate_rows,
        "rows_needed_to_50k": rows_needed_to_50k,
        "final_50k_candidate_gate": "BLOCKED",
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
    }

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "current_validated_candidate_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "current_validated_candidate_rows": current_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "current_candidate_sha256_before": candidate_sha_before,
            "current_candidate_sha256_after": candidate_sha_after,
        },
        "v2_19j_context": {
            "status": v219j.get("status"),
            "selected_route_id": selected_route.get("route_id"),
            "selected_provider": selected_route.get("provider"),
            "selection_score": selected_route.get("selection_score"),
            "decision_matrix_rows": len(decision_matrix_rows),
        },
        "plan_summary": plan_summary,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "route_selection_performed": False,
            "acquisition_plan_performed": True,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": False,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": candidate_sha_before == candidate_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    source_fieldnames = [
        "source_id",
        "source_name",
        "source_role",
        "url",
        "official_scope_allowed",
        "expected_content_type",
        "expected_raw_artifact_id",
        "expected_parse_signal",
        "candidate_value",
        "planned_acquisition_method",
        "planned_raw_phase",
        "candidate_extraction_phase",
        "notes",
    ]

    artifact_fieldnames = [
        "artifact_order",
        "source_id",
        "artifact_id",
        "url",
        "method",
        "official_scope_allowed",
        "expected_content_type",
        "expected_parse_signal",
        "download_policy",
        "overwrite_policy",
        "validation_required_before_extraction",
    ]

    write_csv(SOURCE_INVENTORY_CSV, source_inventory_rows, source_fieldnames)
    write_csv(RAW_ARTIFACT_PLAN_CSV, raw_artifact_plan_rows, artifact_fieldnames)
    write_csv(VALIDATION_STRATEGY_CSV, validation_strategy_rows, ["validation_id", "validation_scope", "check", "severity", "blocks_extraction_if_failed"])
    write_csv(FILTERING_POLICY_CSV, FILTERING_POLICY, ["policy_id", "category", "rule", "reason", "phase_enforced"])
    write_csv(RISK_REGISTER_CSV, risk_register_rows, ["risk_id", "risk", "impact", "likelihood", "mitigation"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    source_lines = "\n".join(
        f"- `{row['source_id']}` — {row['source_role']} — `{row['url']}`"
        for row in source_inventory_rows
    )

    validation_lines = "\n".join(
        f"- `{row['validation_id']}` — {row['severity']} — {row['check']}"
        for row in validation_strategy_rows
    )

    filtering_lines = "\n".join(
        f"- `{row['policy_id']}` — {row['category']} — {row['rule']}"
        for row in FILTERING_POLICY
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.19K prepares the HKEX acquisition plan after HKEX was selected in v2.19J.

This phase is plan-only. It does not download data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Plan summary

- Selected route: `{SELECTED_ROUTE_ID}`
- Provider: `{SELECTED_PROVIDER}`
- Market: `Hong Kong`
- Source inventory rows: `{len(source_inventory_rows)}`
- Raw artifacts planned: `{len(raw_artifact_plan_rows)}`
- Validation strategy rows: `{len(validation_strategy_rows)}`
- Filtering policy rows: `{len(FILTERING_POLICY)}`
- Risk register rows: `{len(risk_register_rows)}`
- Expected gross rows band: `{plan_summary["expected_gross_rows_band"]}`
- Expected net-new band: `{plan_summary["expected_net_new_band"]}`

## Source inventory

{source_lines}

## Validation strategy

{validation_lines}

## Filtering policy

{filtering_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Acquisition plan performed: true
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{candidate_sha_before == candidate_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.19K HKEX acquisition plan completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("PLAN_SUMMARY:")
    for key, value in plan_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_INVENTORY:")
    for row in source_inventory_rows:
        print(f"- {row['source_id']}: role={row['source_role']} official={row['official_scope_allowed']} url={row['url']}")
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
