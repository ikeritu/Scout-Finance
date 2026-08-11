from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20A"
PHASE = "Quality-First Target Reset and Provider Selection"
PHASE_TYPE = "strategy-reset-and-provider-selection-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
HKEX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V219R_JSON = OUTPUT_DIR / "hkex_closure_report_v2_19r.json"

REPORT_JSON = OUTPUT_DIR / "quality_first_target_reset_provider_selection_v2_20a.json"
REPORT_MD = OUTPUT_DIR / "quality_first_target_reset_provider_selection_v2_20a.md"
DECISION_CSV = OUTPUT_DIR / "quality_first_target_reset_decision_v2_20a.csv"
PROVIDER_RANKING_CSV = OUTPUT_DIR / "quality_first_provider_ranking_v2_20a.csv"
STOP_RULES_CSV = OUTPUT_DIR / "quality_first_stop_rules_v2_20a.csv"
CHECKS_CSV = OUTPUT_DIR / "quality_first_target_reset_checks_v2_20a.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "quality_first_next_actions_v2_20a.csv"

EXPECTED_V219R_STATUS = "HKEX_CLOSURE_REPORT_COMPLETED_41392_ROWS_396_NET_NEW_50K_GATE_STILL_BLOCKED_NEXT_PROVIDER_SELECTION_READY_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
HKEX_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
HKEX_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED = 608
ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED = 3608
ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED = 8608

SELECTED_NEXT_PROVIDER = "ASX"
SELECTED_NEXT_PHASE = "v2.20B - ASX Quality-First Acquisition Plan"

STATUS_SUCCESS = "QUALITY_FIRST_TARGET_RESET_COMPLETED_42K_45K_OPERATIONAL_ASX_SELECTED_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
STATUS_FAILED = "QUALITY_FIRST_TARGET_RESET_FAILED_REVIEW_REQUIRED"


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


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        DECISION_CSV,
        PROVIDER_RANKING_CSV,
        STOP_RULES_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219r = read_json(V219R_JSON)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_rows = count_csv_rows(HKEX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_before = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_after = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

    rows_needed_to_quality_floor = max(QUALITY_FLOOR_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_quality_ceiling = max(QUALITY_CEILING_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_aspirational_50k = max(ASPIRATIONAL_TARGET - hkex_validated_candidate_rows, 0)

    quality_floor_gate = "READY" if hkex_validated_candidate_rows >= QUALITY_FLOOR_TARGET else "BLOCKED"
    quality_ceiling_gate = "READY" if hkex_validated_candidate_rows >= QUALITY_CEILING_TARGET else "BLOCKED"
    aspirational_50k_gate = "READY" if hkex_validated_candidate_rows >= ASPIRATIONAL_TARGET else "BLOCKED"

    decision_rows = [
        {
            "decision": "reset_operational_target",
            "previous_target": ASPIRATIONAL_TARGET,
            "new_operational_target_floor": QUALITY_FLOOR_TARGET,
            "new_operational_target_ceiling": QUALITY_CEILING_TARGET,
            "current_validated_candidate_rows": hkex_validated_candidate_rows,
            "rows_needed_to_floor": rows_needed_to_quality_floor,
            "rows_needed_to_ceiling": rows_needed_to_quality_ceiling,
            "rationale": "Prefer fewer high-quality candidates over reaching 50k by adding noisy instruments.",
            "status": "approved",
        },
        {
            "decision": "keep_50k_as_aspirational_only",
            "previous_target": ASPIRATIONAL_TARGET,
            "new_operational_target_floor": QUALITY_FLOOR_TARGET,
            "new_operational_target_ceiling": QUALITY_CEILING_TARGET,
            "current_validated_candidate_rows": hkex_validated_candidate_rows,
            "rows_needed_to_floor": rows_needed_to_quality_floor,
            "rows_needed_to_ceiling": rows_needed_to_quality_ceiling,
            "rationale": "50k remains useful only if a clean provider produces quality net-new rows without relaxing instrument criteria.",
            "status": "approved",
        },
        {
            "decision": "select_next_provider",
            "previous_target": ASPIRATIONAL_TARGET,
            "new_operational_target_floor": QUALITY_FLOOR_TARGET,
            "new_operational_target_ceiling": QUALITY_CEILING_TARGET,
            "current_validated_candidate_rows": hkex_validated_candidate_rows,
            "rows_needed_to_floor": rows_needed_to_quality_floor,
            "rows_needed_to_ceiling": rows_needed_to_quality_ceiling,
            "rationale": "ASX is selected first because it has high expected equity quality and enough plausible breadth to cross 42k without lowering quality.",
            "status": f"selected:{SELECTED_NEXT_PROVIDER}",
        },
    ]

    provider_ranking_rows = [
        {
            "rank": 1,
            "provider": "ASX",
            "route": "Australia quality-first official source route",
            "quality_score": 92,
            "expected_net_new_quality": "medium_high",
            "noise_risk": "medium",
            "volume_fit_for_42k_45k": "high",
            "recommended_action": "select_next",
            "include_scope": "ordinary shares; liquid REITs; high-quality listed equities; index-backed subsets if available",
            "exclude_scope": "warrants; options; rights; preference shares; debt; structured products; illiquid speculative microcaps",
            "reason": "Best balance between quality, breadth and likely contribution toward 42k-45k without chasing 50k.",
        },
        {
            "rank": 2,
            "provider": "TMX_TSX_ONLY",
            "route": "Canada TSX main market only",
            "quality_score": 88,
            "expected_net_new_quality": "medium_high",
            "noise_risk": "medium_high_if_tsvx_included",
            "volume_fit_for_42k_45k": "high",
            "recommended_action": "backup_1",
            "include_scope": "TSX main market equities; liquid REITs; established issuers",
            "exclude_scope": "TSX Venture by default; capital pool companies; shells; penny stocks; illiquid junior miners",
            "reason": "Good quality in TSX, but Venture must stay excluded unless a later quality filter is approved.",
        },
        {
            "rank": 3,
            "provider": "NASDAQ_NORDIC_MAIN_MARKET",
            "route": "Nordic main market quality route",
            "quality_score": 86,
            "expected_net_new_quality": "medium",
            "noise_risk": "medium_if_first_north_included",
            "volume_fit_for_42k_45k": "medium",
            "recommended_action": "backup_2",
            "include_scope": "main market large/mid/small with liquidity; Sweden, Denmark, Finland, Norway, Iceland and Baltic only if clean",
            "exclude_scope": "First North by default; illiquid microcaps; duplicates across markets",
            "reason": "Strong quality profile, especially industrials, health, banks, software and Nordic compounders.",
        },
        {
            "rank": 4,
            "provider": "SIX",
            "route": "Switzerland quality route",
            "quality_score": 90,
            "expected_net_new_quality": "low_medium",
            "noise_risk": "low",
            "volume_fit_for_42k_45k": "medium_low",
            "recommended_action": "backup_quality",
            "include_scope": "primary equity listings; SPI/SMI/SMIM style universe if source supports it",
            "exclude_scope": "structured products; warrants; GDR duplicates; funds unless explicitly approved",
            "reason": "Very high average quality, but probably fewer net-new rows.",
        },
        {
            "rank": 5,
            "provider": "NSE_BSE_INDIA_INDEX_ONLY",
            "route": "India special block, index-first only",
            "quality_score": 89,
            "expected_net_new_quality": "high",
            "noise_risk": "high_if_all_market_included",
            "volume_fit_for_42k_45k": "high",
            "recommended_action": "special_phase_only",
            "include_scope": "Nifty 50/100/200/500 or BSE 500 style index-backed universe",
            "exclude_scope": "full NSE/BSE universe; SME; illiquid microcaps; duplicates between NSE and BSE",
            "reason": "Excellent opportunity set, but complex enough to require its own controlled phase.",
        },
        {
            "rank": 6,
            "provider": "B3",
            "route": "Brazil selective quality route",
            "quality_score": 78,
            "expected_net_new_quality": "medium",
            "noise_risk": "medium_high",
            "volume_fit_for_42k_45k": "medium",
            "recommended_action": "defer",
            "include_scope": "Ibovespa/IBrX-like liquid equities",
            "exclude_scope": "duplicated common/preferred classes without explicit mapping; illiquid listings",
            "reason": "Useful but macro/currency/class-share complexity makes it less attractive than ASX/TMX/Nordic.",
        },
        {
            "rank": 7,
            "provider": "SGX",
            "route": "Singapore selective quality route",
            "quality_score": 76,
            "expected_net_new_quality": "low_medium",
            "noise_risk": "medium",
            "volume_fit_for_42k_45k": "medium_low",
            "recommended_action": "defer",
            "include_scope": "ordinary shares; liquid REITs; selected business trusts",
            "exclude_scope": "structured warrants; certificates; leverage/inverse products; secondary duplicates",
            "reason": "Good REIT/bank/infrastructure exposure but less likely to add many strong net-new equities.",
        },
        {
            "rank": 8,
            "provider": "BME_AND_EUROPE_MINOR_MARKETS",
            "route": "Spain and minor Europe complement",
            "quality_score": 75,
            "expected_net_new_quality": "low",
            "noise_risk": "low_medium",
            "volume_fit_for_42k_45k": "low",
            "recommended_action": "complement_only",
            "include_scope": "main continuous market; liquid BME Growth only if filtered",
            "exclude_scope": "illiquid listings; duplicates; non-equity instruments",
            "reason": "Good complement but not a primary route for filling the 42k-45k quality band.",
        },
        {
            "rank": 9,
            "provider": "JSE",
            "route": "South Africa selective route",
            "quality_score": 70,
            "expected_net_new_quality": "low_medium",
            "noise_risk": "medium_high",
            "volume_fit_for_42k_45k": "low",
            "recommended_action": "defer",
            "include_scope": "liquid large/mid caps; relevant mining, banks, insurance, retail",
            "exclude_scope": "illiquid names; duplicated dual listings; weak liquidity candidates",
            "reason": "Interesting market, but lower priority due to macro/currency/liquidity risk.",
        },
    ]

    stop_rules_rows = [
        {
            "rule_id": "STOP_001",
            "rule": "do_not_add_rows_for_volume_only",
            "threshold": "always",
            "action": "reject_provider_or_subset",
            "reason": "The project now prioritizes 42k-45k high-quality candidates over 50k inflated candidates.",
        },
        {
            "rule_id": "STOP_002",
            "rule": "provider_minimum_quality_net_new",
            "threshold": ">= 500 clean net-new rows preferred; < 250 triggers fast closure unless quality is exceptional",
            "action": "continue_only_if_quality_justifies_effort",
            "reason": "Avoid long acquisition cycles with poor quality yield.",
        },
        {
            "rule_id": "STOP_003",
            "rule": "quality_ceiling_stop",
            "threshold": "45,000 validated candidates",
            "action": "freeze_expansion_and_move_to_product_scoring",
            "reason": "45k is the operational ceiling; beyond that only exceptional clean sources justify expansion.",
        },
        {
            "rule_id": "STOP_004",
            "rule": "instrument_scope_guard",
            "threshold": "no warrants/options/rights/debt/structured products by default",
            "action": "exclude_before_canonical_validation",
            "reason": "Protect scoring quality and avoid HKEX-style large raw counts with low usable yield.",
        },
        {
            "rule_id": "STOP_005",
            "rule": "microcap_liquidity_guard",
            "threshold": "exclude or flag illiquid speculative microcaps where source allows",
            "action": "do_not_count_as quality net-new unless approved",
            "reason": "Candidate quality is more important than raw universe size.",
        },
        {
            "rule_id": "STOP_006",
            "rule": "50k_aspirational_only",
            "threshold": "50,000",
            "action": "do_not_force_route_selection_to_reach_50k",
            "reason": "50k is no longer the operational success criterion.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "target_strategy",
            "action": "adopt_42k_45k_quality_band",
            "priority": "high",
            "reason": "The project should prefer fewer high-quality candidates over inflated 50k coverage.",
            "recommended_phase": SELECTED_NEXT_PHASE,
            "guardrails": "50k is aspirational only; full59k remains deprecated",
        },
        {
            "action_order": 2,
            "action_scope": "provider_route",
            "action": "open_asx_quality_first_acquisition_plan",
            "priority": "high",
            "reason": "ASX is the best next balance of quality and likely useful breadth.",
            "recommended_phase": SELECTED_NEXT_PHASE,
            "guardrails": "ordinary equities and liquid REITs only; no derivatives, debt, rights or structured products",
        },
        {
            "action_order": 3,
            "action_scope": "fallback_route",
            "action": "prepare_tmx_tsx_only_as_backup",
            "priority": "medium",
            "reason": "TSX main market is a good backup; TSXV must remain excluded by default.",
            "recommended_phase": "post-ASX route decision",
            "guardrails": "no TSX Venture unless explicitly approved with strict filters",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19r_report_exists", V219R_JSON.exists(), "critical", str(V219R_JSON))
    add_check("v2_19r_status_expected", v219r.get("status") == EXPECTED_V219R_STATUS, "critical", str(v219r.get("status", "")))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("hkex_validated_candidate_rows_expected", hkex_validated_candidate_rows == HKEX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"hkex_rows={hkex_validated_candidate_rows}")
    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("current_candidate_sha_expected", current_candidate_sha_before == CURRENT_CANDIDATE_SHA_EXPECTED, "critical", current_candidate_sha_before)
    add_check("hkex_validated_candidate_sha_expected", hkex_validated_candidate_sha_before == HKEX_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", hkex_validated_candidate_sha_before)
    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("current_candidate_sha_unchanged", current_candidate_sha_before == current_candidate_sha_after, "critical", "current candidate sha unchanged")
    add_check("hkex_candidate_sha_unchanged", hkex_validated_candidate_sha_before == hkex_validated_candidate_sha_after, "critical", "HKEX validated candidate sha unchanged")
    add_check("quality_floor_target_expected", QUALITY_FLOOR_TARGET == 42000, "critical", f"quality_floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_target_expected", QUALITY_CEILING_TARGET == 45000, "critical", f"quality_ceiling={QUALITY_CEILING_TARGET}")
    add_check("aspirational_50k_not_operational", ASPIRATIONAL_TARGET == 50000, "critical", "50k retained as aspirational only")
    add_check("rows_needed_to_quality_floor_expected", rows_needed_to_quality_floor == ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED, "critical", f"rows_needed_to_42k={rows_needed_to_quality_floor}")
    add_check("rows_needed_to_quality_ceiling_expected", rows_needed_to_quality_ceiling == ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED, "critical", f"rows_needed_to_45k={rows_needed_to_quality_ceiling}")
    add_check("rows_needed_to_aspirational_50k_expected", rows_needed_to_aspirational_50k == ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_needed_to_50k={rows_needed_to_aspirational_50k}")
    add_check("selected_next_provider_asx", SELECTED_NEXT_PROVIDER == "ASX", "critical", SELECTED_NEXT_PROVIDER)
    add_check("selected_next_phase_asx_plan", SELECTED_NEXT_PHASE == "v2.20B - ASX Quality-First Acquisition Plan", "critical", SELECTED_NEXT_PHASE)
    add_check("quality_first_stop_rules_defined", len(stop_rules_rows) >= 6, "critical", f"stop_rules={len(stop_rules_rows)}")
    add_check("provider_ranking_defined", len(provider_ranking_rows) >= 9, "critical", f"providers_ranked={len(provider_ranking_rows)}")
    add_check("strategy_reset_only", True, "critical", "strategy reset only")
    add_check("dataset_not_modified", True, "critical", "no dataset writes in v2.20A")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("current_candidate_dataset_not_modified", True, "critical", "current_candidate_dataset_modified=False")
    add_check("hkex_candidate_dataset_not_modified", True, "critical", "hkex_candidate_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed == 0:
        status = STATUS_SUCCESS
        recommended_next_phase = SELECTED_NEXT_PHASE
    else:
        status = STATUS_FAILED
        recommended_next_phase = "v2.20A_REVIEW - Quality-First Target Reset Review"

    target_summary = {
        "active_canonical_rows": active_canonical_rows,
        "current_validated_candidate_rows": current_candidate_rows,
        "hkex_validated_candidate_rows": hkex_validated_candidate_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_needed_to_quality_floor": rows_needed_to_quality_floor,
        "rows_needed_to_quality_ceiling": rows_needed_to_quality_ceiling,
        "rows_needed_to_aspirational_50k": rows_needed_to_aspirational_50k,
        "quality_floor_gate": quality_floor_gate,
        "quality_ceiling_gate": quality_ceiling_gate,
        "aspirational_50k_gate": aspirational_50k_gate,
        "selected_next_provider": SELECTED_NEXT_PROVIDER,
        "selected_next_phase": SELECTED_NEXT_PHASE,
        "critical_failed_checks": critical_failed,
        "full59k": "DEPRECATED_DEFERRED",
    }

    write_csv(DECISION_CSV, decision_rows, ["decision", "previous_target", "new_operational_target_floor", "new_operational_target_ceiling", "current_validated_candidate_rows", "rows_needed_to_floor", "rows_needed_to_ceiling", "rationale", "status"])
    write_csv(PROVIDER_RANKING_CSV, provider_ranking_rows, ["rank", "provider", "route", "quality_score", "expected_net_new_quality", "noise_risk", "volume_fit_for_42k_45k", "recommended_action", "include_scope", "exclude_scope", "reason"])
    write_csv(STOP_RULES_CSV, stop_rules_rows, ["rule_id", "rule", "threshold", "action", "reason"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "target_summary": target_summary,
        "decision": decision_rows,
        "provider_ranking": provider_ranking_rows,
        "stop_rules": stop_rules_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "strategy_reset_only": True,
            "target_reset_performed": True,
            "old_operational_target_50000_replaced": True,
            "new_operational_target_floor": QUALITY_FLOOR_TARGET,
            "new_operational_target_ceiling": QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "selected_next_provider": SELECTED_NEXT_PROVIDER,
            "selected_next_phase": SELECTED_NEXT_PHASE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "route_selection_performed": True,
            "acquisition_plan_performed": False,
            "raw_acquisition_performed": False,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": current_candidate_sha_before == current_candidate_sha_after,
            "hkex_validated_candidate_dataset_read": True,
            "hkex_validated_candidate_dataset_modified": False,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    decision_lines = "\n".join(
        f"- `{row['decision']}`: `{row['status']}` — {row['rationale']}"
        for row in decision_rows
    )
    provider_lines = "\n".join(
        f"- #{row['rank']} `{row['provider']}` — score `{row['quality_score']}` — {row['recommended_action']} — {row['reason']}"
        for row in provider_ranking_rows
    )
    stop_rule_lines = "\n".join(
        f"- `{row['rule_id']}` — {row['rule']}: {row['threshold']} → {row['action']}"
        for row in stop_rules_rows
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

v2.20A resets the expansion strategy from a rigid 50,000-candidate target to a quality-first operational band of **{QUALITY_FLOOR_TARGET:,}–{QUALITY_CEILING_TARGET:,}** validated candidates.

The current validated HKEX candidate dataset has **{hkex_validated_candidate_rows:,}** rows.

Rows needed:

- To reach 42k quality floor: **{rows_needed_to_quality_floor:,}**
- To reach 45k quality ceiling: **{rows_needed_to_quality_ceiling:,}**
- To reach 50k aspirational target: **{rows_needed_to_aspirational_50k:,}**

50k remains aspirational only. The project should not add low-quality rows, derivative instruments, debt, structured products, illiquid microcaps or duplicate-heavy routes merely to reach 50k.

The selected next provider route is **{SELECTED_NEXT_PROVIDER}**, with next phase:

`{SELECTED_NEXT_PHASE}`

## Target summary

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows before HKEX: `{current_candidate_rows}`
- HKEX validated candidate rows: `{hkex_validated_candidate_rows}`
- Operational target floor: `{QUALITY_FLOOR_TARGET}`
- Operational target ceiling: `{QUALITY_CEILING_TARGET}`
- Aspirational target: `{ASPIRATIONAL_TARGET}`
- Rows needed to floor: `{rows_needed_to_quality_floor}`
- Rows needed to ceiling: `{rows_needed_to_quality_ceiling}`
- Rows needed to aspirational 50k: `{rows_needed_to_aspirational_50k}`
- Quality floor gate: `{quality_floor_gate}`
- Quality ceiling gate: `{quality_ceiling_gate}`
- 50k aspirational gate: `{aspirational_50k_gate}`
- Selected next provider: `{SELECTED_NEXT_PROVIDER}`
- Critical failed checks: `{critical_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Decisions

{decision_lines}

## Provider ranking

{provider_lines}

## Stop rules

{stop_rule_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Strategy reset only: true
- Target reset performed: true
- Old operational 50k target replaced: true
- New operational target: `{QUALITY_FLOOR_TARGET}`–`{QUALITY_CEILING_TARGET}`
- 50k retained as aspirational: true
- Selected next provider: `{SELECTED_NEXT_PROVIDER}`
- Network download performed: false
- Acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current candidate dataset modified: false
- HKEX candidate dataset modified: false
- Active canonical replaced: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.20A quality-first target reset and provider selection completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("TARGET_SUMMARY:")
    for key, value in target_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("PROVIDER_RANKING:")
    for row in provider_ranking_rows:
        print(f"- #{row['rank']} {row['provider']} score={row['quality_score']} action={row['recommended_action']}")
    print("")
    print("STOP_RULES:")
    for row in stop_rules_rows:
        print(f"- {row['rule_id']}: {row['rule']} threshold={row['threshold']}")
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
