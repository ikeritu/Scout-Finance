from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.17A"
PHASE = "Next Provider Route Selection"
PHASE_TYPE = "provider-route-selection-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
TMX_CLOSURE_JSON = OUTPUT_DIR / "tmx_closure_report_v2_16i.json"

REPORT_JSON = OUTPUT_DIR / "next_provider_route_selection_v2_17a.json"
REPORT_MD = OUTPUT_DIR / "next_provider_route_selection_v2_17a.md"
ROUTE_CANDIDATES_CSV = OUTPUT_DIR / "next_provider_route_candidates_v2_17a.csv"
DECISION_LOG_CSV = OUTPUT_DIR / "next_provider_route_decision_log_v2_17a.csv"

CURRENT_CANONICAL_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713

EXPECTED_TMX_CLOSURE_STATUS = "TMX_CLOSURE_REPORT_COMPLETED_PLUS1_CANDIDATE_VALIDATED_FULL_SOURCE_STILL_BLOCKED"

SELECTED_ROUTE_ID = "nse_india"
SELECTED_NEXT_PHASE = "v2.17B - NSE India Acquisition Plan"

ROUTE_FIELDS = [
    "rank",
    "route_id",
    "provider",
    "market",
    "primary_sources",
    "official_evidence_urls",
    "expected_yield_bucket",
    "technical_complexity",
    "licensing_or_access_risk",
    "instrument_noise_risk",
    "pipeline_fit_score",
    "volume_potential_score",
    "access_score",
    "filtering_score",
    "total_score",
    "decision",
    "recommended_next_phase",
    "rationale",
]

DECISION_FIELDS = [
    "decision_id",
    "topic",
    "decision",
    "reason",
    "impact",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> int:
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


def make_routes() -> list[dict]:
    routes = [
        {
            "rank": 1,
            "route_id": "nse_india",
            "provider": "NSE India",
            "market": "India",
            "primary_sources": "NSE All Reports; CM - MII - Security File; Securities available for Trading",
            "official_evidence_urls": "https://www.nseindia.com/all-reports | https://www.nseindia.com/static/market-data/securities-available-for-trading",
            "expected_yield_bucket": "high",
            "technical_complexity": "medium",
            "licensing_or_access_risk": "medium",
            "instrument_noise_risk": "medium",
            "pipeline_fit_score": 5,
            "volume_potential_score": 5,
            "access_score": 4,
            "filtering_score": 4,
            "decision": "selected",
            "recommended_next_phase": "v2.17B - NSE India Acquisition Plan",
            "rationale": "Best balance of official bulk-like files, security master structure, volume potential and compatibility with the existing raw acquisition -> validation -> extraction -> canonical dry-run pipeline.",
        },
        {
            "rank": 2,
            "route_id": "twse_tpex_taiwan",
            "provider": "TWSE + TPEx",
            "market": "Taiwan",
            "primary_sources": "TWSE/TPEx ISIN public lists for listed equities",
            "official_evidence_urls": "https://isin.twse.com.tw/isin/e_C_public.jsp?strMode=2 | https://isin.twse.com.tw/isin/e_C_public.jsp?strMode=4 | https://isin.twse.com.tw/isin/e_C_public.jsp?strMode=5",
            "expected_yield_bucket": "high",
            "technical_complexity": "medium_low",
            "licensing_or_access_risk": "low_medium",
            "instrument_noise_risk": "high",
            "pipeline_fit_score": 5,
            "volume_potential_score": 4,
            "access_score": 4,
            "filtering_score": 3,
            "decision": "reserve_route",
            "recommended_next_phase": "future - Taiwan Acquisition Plan",
            "rationale": "Strong official structured ISIN route, but requires strict filtering for ETFs, warrants, notes, bonds and other non-common-equity instruments.",
        },
        {
            "rank": 3,
            "route_id": "asx_australia",
            "provider": "ASX",
            "market": "Australia",
            "primary_sources": "ASX listed companies CSV; ASX ISIN directory",
            "official_evidence_urls": "https://www.asx.com.au/markets/trade-our-cash-market/overview/indices/ | https://www.asx.com.au/markets/market-resources/asx-codes-and-descriptors",
            "expected_yield_bucket": "medium",
            "technical_complexity": "low",
            "licensing_or_access_risk": "low",
            "instrument_noise_risk": "medium",
            "pipeline_fit_score": 5,
            "volume_potential_score": 3,
            "access_score": 5,
            "filtering_score": 4,
            "decision": "reserve_quick_win",
            "recommended_next_phase": "future - ASX Acquisition Plan",
            "rationale": "Very clean official route and likely quick win, but expected yield is lower than India/Taiwan/Korea.",
        },
        {
            "rank": 4,
            "route_id": "krx_korea",
            "provider": "KRX",
            "market": "Korea",
            "primary_sources": "KRX listed company search/download",
            "official_evidence_urls": "https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp",
            "expected_yield_bucket": "high",
            "technical_complexity": "medium_high",
            "licensing_or_access_risk": "medium",
            "instrument_noise_risk": "medium",
            "pipeline_fit_score": 4,
            "volume_potential_score": 5,
            "access_score": 3,
            "filtering_score": 4,
            "decision": "reserve_route",
            "recommended_next_phase": "future - KRX Acquisition Plan",
            "rationale": "High market potential, but likely more dynamic and may require a controlled endpoint/download probe.",
        },
        {
            "rank": 5,
            "route_id": "hkex_hong_kong",
            "provider": "HKEX",
            "market": "Hong Kong",
            "primary_sources": "HKEX Securities Lists; Full List of Securities",
            "official_evidence_urls": "https://www.hkex.com.hk/Services/Trading/Securities/Securities-Lists?sc_lang=en",
            "expected_yield_bucket": "medium_high",
            "technical_complexity": "medium_high",
            "licensing_or_access_risk": "medium_high",
            "instrument_noise_risk": "high",
            "pipeline_fit_score": 4,
            "volume_potential_score": 4,
            "access_score": 3,
            "filtering_score": 2,
            "decision": "reserve_route",
            "recommended_next_phase": "future - HKEX Acquisition Plan",
            "rationale": "Important market and official securities list, but high instrument noise due to structured products, warrants, CBBCs, units and other non-common-equity instruments.",
        },
        {
            "rank": 6,
            "route_id": "lseg_london",
            "provider": "LSEG / London Stock Exchange",
            "market": "United Kingdom / London",
            "primary_sources": "Daily Tradeable Instruments Report; Daily Official List",
            "official_evidence_urls": "https://www.londonstockexchange.com/equities-trading/market-data/historical-and-analytics-data-products",
            "expected_yield_bucket": "medium_high",
            "technical_complexity": "high",
            "licensing_or_access_risk": "high",
            "instrument_noise_risk": "high",
            "pipeline_fit_score": 3,
            "volume_potential_score": 4,
            "access_score": 2,
            "filtering_score": 2,
            "decision": "defer",
            "recommended_next_phase": "future - LSEG Access Review",
            "rationale": "Relevant instrument products exist, but licensing/access and mixed instrument scope make it less attractive as the immediate next route.",
        },
        {
            "rank": 7,
            "route_id": "sgx_singapore",
            "provider": "SGX",
            "market": "Singapore",
            "primary_sources": "Potential SGX securities/lists route to be researched later",
            "official_evidence_urls": "",
            "expected_yield_bucket": "medium",
            "technical_complexity": "medium",
            "licensing_or_access_risk": "medium",
            "instrument_noise_risk": "medium",
            "pipeline_fit_score": 3,
            "volume_potential_score": 3,
            "access_score": 3,
            "filtering_score": 3,
            "decision": "defer_pending_research",
            "recommended_next_phase": "future - SGX Route Research",
            "rationale": "Potentially useful, but not enough current evidence to prioritize over NSE/TWSE/ASX/KRX.",
        },
    ]

    for row in routes:
        row["total_score"] = (
            int(row["pipeline_fit_score"])
            + int(row["volume_potential_score"])
            + int(row["access_score"])
            + int(row["filtering_score"])
        )

    return routes


def main() -> None:
    for path in [REPORT_JSON, REPORT_MD, ROUTE_CANDIDATES_CSV, DECISION_LOG_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    tmx_closure = read_json(TMX_CLOSURE_JSON)
    canonical_rows = read_csv_rows(CANONICAL_DATASET)
    routes = make_routes()

    selected = next(row for row in routes if row["route_id"] == SELECTED_ROUTE_ID)

    decisions = [
        {
            "decision_id": sha256_text(f"{VERSION}|select_nse")[:16],
            "topic": "Selected provider route",
            "decision": "Select NSE India as the next provider route.",
            "reason": "NSE has official bulk-like security files and a better expected yield/structure balance than the just-closed TMX route.",
            "impact": SELECTED_NEXT_PHASE,
        },
        {
            "decision_id": sha256_text(f"{VERSION}|keep_taiwan_reserve")[:16],
            "topic": "Reserve route",
            "decision": "Keep TWSE + TPEx Taiwan as first reserve route.",
            "reason": "TWSE/TPEx ISIN lists are official and structured, but filtering non-equity instruments must be strict.",
            "impact": "Use if NSE acquisition is blocked or low-yield.",
        },
        {
            "decision_id": sha256_text(f"{VERSION}|asx_quick_win")[:16],
            "topic": "Quick win route",
            "decision": "Keep ASX Australia as a clean quick-win fallback.",
            "reason": "ASX official CSV/ISIN routes are likely easier but lower-yield than India.",
            "impact": "Use after NSE/Taiwan or if quick low-risk acquisition is preferred.",
        },
        {
            "decision_id": sha256_text(f"{VERSION}|no_canonical_change")[:16],
            "topic": "Canonical dataset",
            "decision": "Do not modify the canonical dataset in v2.17A.",
            "reason": "This is provider route selection only.",
            "impact": "Active canonical remains 38,287 rows and full source gate remains blocked.",
        },
    ]

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("tmx_closure_report_exists", TMX_CLOSURE_JSON.exists(), "critical", str(TMX_CLOSURE_JSON))
    add_check(
        "tmx_closure_status_expected",
        tmx_closure.get("status") == EXPECTED_TMX_CLOSURE_STATUS,
        "critical",
        str(tmx_closure.get("status", "")),
    )
    add_check(
        "tmx_closure_recommends_v217a",
        tmx_closure.get("recommended_next_phase") == "v2.17A - Next Provider Route Selection",
        "critical",
        str(tmx_closure.get("recommended_next_phase", "")),
    )
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("canonical_rows_expected", canonical_rows == CURRENT_CANONICAL_ROWS, "critical", f"canonical_rows={canonical_rows}")
    add_check("route_candidates_count", len(routes) >= 6, "critical", f"routes={len(routes)}")
    add_check("selected_route_is_nse", selected["route_id"] == "nse_india", "critical", selected["route_id"])
    add_check("selected_next_phase_expected", selected["recommended_next_phase"] == SELECTED_NEXT_PHASE, "critical", selected["recommended_next_phase"])
    add_check("full_source_still_blocked", canonical_rows < FULL_SOURCE_THRESHOLD, "critical", f"{canonical_rows} < {FULL_SOURCE_THRESHOLD}")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed == 0:
        status = "NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_NSE_INDIA_SELECTED_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = SELECTED_NEXT_PHASE
    else:
        status = "NEXT_PROVIDER_ROUTE_SELECTION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.17A_FIX - Next Provider Route Selection Repair"

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
        "tmx_closure_reference": {
            "artifact": str(TMX_CLOSURE_JSON),
            "status": tmx_closure.get("status", ""),
            "recommended_next_phase": tmx_closure.get("recommended_next_phase", ""),
        },
        "selected_route": selected,
        "route_candidates": routes,
        "decision_log": decisions,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "tmx_closure_report_read": True,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "provider_route_selected": True,
            "raw_acquisition_performed": False,
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
    write_csv(ROUTE_CANDIDATES_CSV, routes, ROUTE_FIELDS)
    write_csv(DECISION_LOG_CSV, decisions, DECISION_FIELDS)

    route_lines = "\n".join(
        f"- **#{row['rank']} {row['provider']} ({row['market']})** — decision=`{row['decision']}`, score=`{row['total_score']}`, next=`{row['recommended_next_phase']}`"
        for row in routes
    )

    decision_lines = "\n".join(
        f"- **{row['topic']}**: {row['decision']} Impact: `{row['impact']}`"
        for row in decisions
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

## Executive decision

Selected next provider route:

- Route: `{selected["route_id"]}`
- Provider: `{selected["provider"]}`
- Market: `{selected["market"]}`
- Decision: `{selected["decision"]}`
- Recommended next phase: `{recommended_next_phase}`

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{canonical_rows}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completion: `{round((canonical_rows / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Route candidates

{route_lines}

## Decision log

{decision_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- TMX closure report read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Provider route selected: true
- Raw acquisition performed: false
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

v2.17A selects NSE India as the next provider route after TMX closure.

No acquisition, extraction, canonical comparison, rebuild or canonical modification is performed in this phase.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.17A next provider route selection completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SELECTED_ROUTE:")
    for key, value in selected.items():
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
