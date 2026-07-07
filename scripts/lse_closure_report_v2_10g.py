from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.10G"
METHOD = "lse_closure_report_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

VALIDATION_JSON = OUT_DIR / "lse_validation_v2_10d.json"
ACQUISITION_JSON = OUT_DIR / "lse_acquisition_real_v2_10c.json"
PLAN_JSON = OUT_DIR / "lse_acquisition_plan_v2_10b.json"
ROUTE_JSON = OUT_DIR / "next_provider_route_v2_10a.json"

OUT_JSON = OUT_DIR / "lse_closure_report_v2_10g.json"
OUT_MD = OUT_DIR / "lse_closure_report_v2_10g.md"
CLOSURE_SUMMARY_CSV = OUT_DIR / "lse_closure_summary_v2_10g.csv"
SKIPPED_PHASES_CSV = OUT_DIR / "lse_skipped_phases_v2_10g.csv"

CURRENT_EXPANDED_ROWS = 9200
CURRENT_EXCLUSIONS_ROWS = 10056
TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000
ROWS_NEEDED_FIRST_EXPANSION = 5800
ROWS_NEEDED_FULL_SOURCE = 40800

PROVIDER_ID = "lse_issuers_and_instruments_reports"
NEXT_PROVIDER_ROUTE = "v2.11A ? Cboe Europe Route"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    route = read_json(ROUTE_JSON)
    plan = read_json(PLAN_JSON)
    acquisition = read_json(ACQUISITION_JSON)
    validation = read_json(VALIDATION_JSON)

    required_artifacts = [
        ("v2.10A route", ROUTE_JSON, route),
        ("v2.10B plan", PLAN_JSON, plan),
        ("v2.10C acquisition", ACQUISITION_JSON, acquisition),
        ("v2.10D validation", VALIDATION_JSON, validation),
    ]

    for label, path, data in required_artifacts:
        if data.get("_exists"):
            positives.append(f"{label} artifact found: {rel(path)}")
        else:
            blockers.append(f"Missing {label} artifact: {rel(path)}")

    checks = [
        ("v2.10A route_status", route.get("route_status"), "NEXT_PROVIDER_ROUTE_READY"),
        ("v2.10A route_decision", route.get("route_decision"), "LSE_SELECTED_AS_NEXT_PROVIDER_ROUTE"),
        ("v2.10B plan_status", plan.get("plan_status"), "LSE_ACQUISITION_PLAN_READY"),
        ("v2.10B plan_decision", plan.get("plan_decision"), "LSE_CONTROLLED_ACQUISITION_APPROVED"),
        ("v2.10C acquisition_status", acquisition.get("acquisition_status"), "LSE_ACQUISITION_COMPLETED"),
        ("v2.10C acquisition_decision", acquisition.get("acquisition_decision"), "LSE_RAW_SOURCE_READY_FOR_VALIDATION"),
        ("v2.10D validation_status", validation.get("validation_status"), "LSE_VALIDATED_NO_USABLE_TABULAR_SOURCE"),
        ("v2.10D validation_decision", validation.get("validation_decision"), "LSE_ACCESSIBLE_BUT_NO_REBUILDABLE_SOURCE"),
    ]

    for label, actual, expected in checks:
        if actual == expected:
            positives.append(f"{label} accepted: {actual}")
        else:
            blockers.append(f"{label} unexpected: actual={actual} expected={expected}")

    row_summary = validation.get("row_summary", {}) if isinstance(validation, dict) else {}
    threshold_status = validation.get("threshold_status", {}) if isinstance(validation, dict) else {}

    successful_page_downloads = int(row_summary.get("successful_page_downloads") or 0)
    discovered_links = int(row_summary.get("discovered_links") or 0)
    selected_download_candidates = int(row_summary.get("selected_download_candidates") or 0)
    successful_candidate_downloads = int(row_summary.get("successful_candidate_downloads") or 0)
    probable_csv_candidates = int(row_summary.get("probable_csv_candidates") or 0)
    total_probable_csv_rows = int(row_summary.get("total_probable_csv_rows") or 0)
    normalized_candidate_rows = int(row_summary.get("normalized_candidate_rows") or 0)
    net_new_candidate_rows = int(row_summary.get("net_new_candidate_rows") or 0)

    projected_rows_if_rebuilt = int(threshold_status.get("projected_rows_if_rebuilt") or CURRENT_EXPANDED_ROWS)
    first_expansion_unlocked = bool(threshold_status.get("first_expansion_unlocked_if_rebuilt"))
    full_source_unlocked = bool(threshold_status.get("full_source_unlocked_if_rebuilt"))
    rows_still_needed_first = int(threshold_status.get("rows_still_needed_first_expansion_after_lse") or ROWS_NEEDED_FIRST_EXPANSION)
    rows_still_needed_full = int(threshold_status.get("rows_still_needed_full_source_after_lse") or ROWS_NEEDED_FULL_SOURCE)

    if successful_page_downloads == 4:
        positives.append("LSE accessibility confirmed: 4/4 planned pages downloaded.")
    else:
        warnings.append(f"LSE accessibility partial: {successful_page_downloads}/4 planned pages downloaded.")

    if discovered_links > 0:
        positives.append(f"LSE link discovery confirmed: {discovered_links} links discovered.")
    else:
        warnings.append("No LSE links discovered.")

    if selected_download_candidates == 0:
        warnings.append("No official downloadable report candidates selected.")
    if successful_candidate_downloads == 0:
        warnings.append("No LSE report candidates downloaded.")
    if probable_csv_candidates == 0:
        warnings.append("No probable CSV/XLS-derived tabular candidate available.")
    if total_probable_csv_rows == 0:
        warnings.append("LSE produced zero tabular rows.")
    if net_new_candidate_rows == 0:
        warnings.append("LSE produced zero net-new source rows.")

    rebuild_allowed = False
    skip_v2_10e = True
    skip_v2_10f = True

    skipped_phases = [
        {
            "phase": "v2.10E",
            "name": "Rebuild Expanded Source With LSE",
            "status": "SKIPPED",
            "reason": "No usable tabular source and 0 net-new candidate rows.",
        },
        {
            "phase": "v2.10F",
            "name": "Validate Expanded Source With LSE",
            "status": "SKIPPED",
            "reason": "No LSE rebuild was performed.",
        },
    ]

    if blockers:
        closure_status = "LSE_CLOSURE_BLOCKED"
        readiness_score = 0
        closure_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        closure_status = "LSE_CLOSED_ACCESSIBLE_BUT_NOT_USABLE_FOR_REBUILD"
        readiness_score = 95
        closure_decision = "LSE_CLOSED_NO_REBUILD_FALLBACK_REQUIRED"
        recommended_next_phase = NEXT_PROVIDER_ROUTE

    closure_summary = {
        "provider_id": PROVIDER_ID,
        "closure_status": closure_status,
        "readiness_score": readiness_score,
        "closure_decision": closure_decision,
        "successful_page_downloads": successful_page_downloads,
        "discovered_links": discovered_links,
        "selected_download_candidates": selected_download_candidates,
        "successful_candidate_downloads": successful_candidate_downloads,
        "probable_csv_candidates": probable_csv_candidates,
        "total_probable_csv_rows": total_probable_csv_rows,
        "normalized_candidate_rows": normalized_candidate_rows,
        "net_new_candidate_rows": net_new_candidate_rows,
        "current_expanded_rows": CURRENT_EXPANDED_ROWS,
        "projected_rows_if_rebuilt": projected_rows_if_rebuilt,
        "first_expansion_unlocked": first_expansion_unlocked,
        "full_source_unlocked": full_source_unlocked,
        "rows_still_needed_first_expansion": rows_still_needed_first,
        "rows_still_needed_full_source": rows_still_needed_full,
        "rebuild_allowed": rebuild_allowed,
        "skip_v2_10e": skip_v2_10e,
        "skip_v2_10f": skip_v2_10f,
        "recommended_next_phase": recommended_next_phase,
    }

    with CLOSURE_SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        for key, value in closure_summary.items():
            writer.writerow({"metric": key, "value": value})

    with SKIPPED_PHASES_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["phase", "name", "status", "reason"])
        writer.writeheader()
        writer.writerows(skipped_phases)

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "closure_status": closure_status,
        "readiness_score": readiness_score,
        "closure_decision": closure_decision,
        "recommended_next_phase": recommended_next_phase,
        "provider": {
            "provider_id": PROVIDER_ID,
        },
        "closure_summary": closure_summary,
        "skipped_phases": skipped_phases,
        "final_decision": {
            "lse_accessible": successful_page_downloads > 0,
            "lse_usable_for_rebuild": False,
            "rebuild_allowed": False,
            "expanded_universe_rebuilt": False,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
            "fallback_required": True,
            "fallback_route": NEXT_PROVIDER_ROUTE,
        },
        "outputs": {
            "closure_summary_csv": rel(CLOSURE_SUMMARY_CSV),
            "skipped_phases_csv": rel(SKIPPED_PHASES_CSV),
            "closure_json": rel(OUT_JSON),
            "closure_md": rel(OUT_MD),
        },
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "network_download_performed": False,
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
            "closure_only": True,
            "rebuild_allowed": False,
        },
        "recommendation": (
            "Proceed to v2.11A Cboe Europe Route. LSE is closed as accessible but not usable for source rebuild in this route."
            if not blockers
            else "Resolve blockers before closing LSE."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.10G LSE Closure Report")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Closure status: **{closure_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Closure decision: **{closure_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Final decision")
    md.append("")
    md.append("```text")
    md.append("LSE_CLOSED_ACCESSIBLE_BUT_NOT_USABLE_FOR_REBUILD")
    md.append("LSE_ACCESSIBLE_BUT_NO_REBUILDABLE_SOURCE")
    md.append("REBUILD_NOT_ALLOWED")
    md.append("v2.10E_SKIPPED")
    md.append("v2.10F_SKIPPED")
    md.append("FULL_59K_REMAINS_BLOCKED")
    md.append("NEXT_RECOMMENDED_PHASE: v2.11A_CBOE_EUROPE_ROUTE")
    md.append("```")
    md.append("")
    md.append("## Closure summary")
    md.append("")
    md.append(f"- Successful LSE page downloads: {successful_page_downloads}")
    md.append(f"- Discovered links: {discovered_links}")
    md.append(f"- Selected download candidates: {selected_download_candidates}")
    md.append(f"- Successful candidate downloads: {successful_candidate_downloads}")
    md.append(f"- Probable CSV candidates: {probable_csv_candidates}")
    md.append(f"- Total probable CSV rows: {total_probable_csv_rows}")
    md.append(f"- Normalized candidate rows: {normalized_candidate_rows}")
    md.append(f"- Net-new candidate rows: {net_new_candidate_rows}")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Projected rows if rebuilt: {projected_rows_if_rebuilt}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- First expansion unlocked: {first_expansion_unlocked}")
    md.append(f"- Full source unlocked: {full_source_unlocked}")
    md.append(f"- Rows still needed first expansion: {rows_still_needed_first}")
    md.append(f"- Rows still needed full source: {rows_still_needed_full}")
    md.append("")
    md.append("## Skipped phases")
    md.append("")
    for item in skipped_phases:
        md.append(f"- {item['phase']} ? {item['name']}: **{item['status']}** ? {item['reason']}")
    md.append("")
    md.append("## Outputs")
    md.append("")
    md.append(f"- Closure summary CSV: `{rel(CLOSURE_SUMMARY_CSV)}`")
    md.append(f"- Skipped phases CSV: `{rel(SKIPPED_PHASES_CSV)}`")
    md.append(f"- Closure JSON: `{rel(OUT_JSON)}`")
    md.append(f"- Closure report: `{rel(OUT_MD)}`")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- Network download performed: false")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("- Closure only: true")
    md.append("- Rebuild allowed: false")
    md.append("")
    md.append("## Positives")
    md.append("")
    if positives:
        for item in positives:
            md.append(f"- {item}")
    else:
        md.append("- No positives detected.")
    md.append("")
    md.append("## Blockers")
    md.append("")
    if blockers:
        for item in blockers:
            md.append(f"- {item}")
    else:
        md.append("- No blockers detected.")
    md.append("")
    md.append("## Warnings")
    md.append("")
    if warnings:
        for item in warnings:
            md.append(f"- {item}")
    else:
        md.append("- No warnings detected.")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.10G is closure-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.10G LSE Closure Report")
    print("=" * 92)
    print(f"OK   Closure status: {closure_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Closure decision: {closure_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Successful page downloads: {successful_page_downloads}")
    print(f"OK   Discovered links: {discovered_links}")
    print(f"OK   Selected download candidates: {selected_download_candidates}")
    print(f"OK   Successful candidate downloads: {successful_candidate_downloads}")
    print(f"OK   Probable CSV candidates: {probable_csv_candidates}")
    print(f"OK   Net-new candidate rows: {net_new_candidate_rows}")
    print(f"OK   Projected rows if rebuilt: {projected_rows_if_rebuilt}")
    print(f"OK   First expansion unlocked: {first_expansion_unlocked}")
    print(f"OK   Full source unlocked: {full_source_unlocked}")
    print(f"OK   Rebuild allowed: False")
    print(f"OK   v2.10E skipped: {skip_v2_10e}")
    print(f"OK   v2.10F skipped: {skip_v2_10f}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Closure summary CSV written: {CLOSURE_SUMMARY_CSV}")
    print(f"OK   Skipped phases CSV written: {SKIPPED_PHASES_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
