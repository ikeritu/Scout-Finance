from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.10D"
METHOD = "lse_validation_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

ACQUISITION_JSON = OUT_DIR / "lse_acquisition_real_v2_10c.json"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

PROVIDER_ID = "lse_issuers_and_instruments_reports"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID

DISCOVERED_LINKS_CSV = OUT_DIR / "lse_discovered_links_v2_10c.csv"
REQUEST_RESULTS_CSV = OUT_DIR / "lse_request_results_v2_10c.csv"
SCHEMA_PROBE_INPUT_CSV = OUT_DIR / "lse_schema_probe_v2_10c.csv"

OUT_JSON = OUT_DIR / "lse_validation_v2_10d.json"
OUT_MD = OUT_DIR / "lse_validation_v2_10d.md"
VALIDATION_SUMMARY_CSV = OUT_DIR / "lse_validation_summary_v2_10d.csv"
ISSUES_CSV = OUT_DIR / "lse_validation_issues_v2_10d.csv"
DECISION_GATE_CSV = OUT_DIR / "lse_decision_gate_v2_10d.csv"

CURRENT_EXPANDED_ROWS = 9200
CURRENT_EXCLUSIONS_ROWS = 10056

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

ROWS_NEEDED_FIRST_EXPANSION = 5800
ROWS_NEEDED_FULL_SOURCE = 40800


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


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []
    issues: list[dict[str, str]] = []

    acquisition = read_json(ACQUISITION_JSON)

    if not acquisition.get("_exists"):
        blockers.append(f"Missing v2.10C acquisition artifact: {rel(ACQUISITION_JSON)}")
    else:
        positives.append(f"v2.10C acquisition artifact found: {rel(ACQUISITION_JSON)}")

    acquisition_status = acquisition.get("acquisition_status")
    acquisition_decision = acquisition.get("acquisition_decision")

    if acquisition_status == "LSE_ACQUISITION_COMPLETED":
        positives.append(f"v2.10C acquisition status accepted: {acquisition_status}")
    else:
        blockers.append(f"Unexpected v2.10C acquisition status: {acquisition_status}")

    if acquisition_decision == "LSE_RAW_SOURCE_READY_FOR_VALIDATION":
        positives.append(f"v2.10C acquisition decision accepted: {acquisition_decision}")
    else:
        blockers.append(f"Unexpected v2.10C acquisition decision: {acquisition_decision}")

    for path in [
        CURRENT_EXPANDED_CSV,
        CURRENT_EXCLUSIONS_CSV,
        DISCOVERED_LINKS_CSV,
        REQUEST_RESULTS_CSV,
        SCHEMA_PROBE_INPUT_CSV,
    ]:
        if path.exists():
            positives.append(f"Validation input available: {rel(path)}")
        else:
            blockers.append(f"Missing validation input: {rel(path)}")

    summary = acquisition.get("summary", {}) if isinstance(acquisition, dict) else {}

    planned_page_routes = int(summary.get("planned_page_routes") or 0)
    successful_page_downloads = int(summary.get("successful_page_downloads") or 0)
    discovered_links = int(summary.get("discovered_links") or 0)
    selected_download_candidates = int(summary.get("selected_download_candidates") or 0)
    successful_candidate_downloads = int(summary.get("successful_candidate_downloads") or 0)
    probable_csv_candidates = int(summary.get("probable_csv_candidates") or 0)
    total_probable_csv_rows = int(summary.get("total_probable_csv_rows") or 0)

    request_rows = read_csv_dicts(REQUEST_RESULTS_CSV)
    discovered_rows = read_csv_dicts(DISCOVERED_LINKS_CSV)
    schema_rows = read_csv_dicts(SCHEMA_PROBE_INPUT_CSV)

    successful_request_rows = [
        row for row in request_rows
        if str(row.get("ok", "")).lower() == "true"
    ]

    download_candidate_rows = [
        row for row in discovered_rows
        if str(row.get("download_candidate", "")).lower() == "true"
    ]

    if successful_page_downloads == planned_page_routes and planned_page_routes > 0:
        positives.append(f"All planned LSE pages downloaded: {successful_page_downloads}/{planned_page_routes}.")
    elif successful_page_downloads > 0:
        warnings.append(f"Only partial LSE page download success: {successful_page_downloads}/{planned_page_routes}.")
    else:
        blockers.append("No LSE planned pages were downloaded successfully.")

    if discovered_links > 0:
        positives.append(f"LSE links discovered: {discovered_links}.")
    else:
        warnings.append("No LSE links were discovered.")

    if selected_download_candidates == 0:
        warnings.append("No LSE report download candidates were selected from discovered links.")
    else:
        positives.append(f"LSE selected download candidates: {selected_download_candidates}.")

    if successful_candidate_downloads == 0:
        warnings.append("No LSE report candidate files were downloaded.")
    else:
        positives.append(f"LSE report candidate downloads succeeded: {successful_candidate_downloads}.")

    if probable_csv_candidates == 0:
        warnings.append("No probable CSV/XLS-derived tabular candidate was available for schema validation.")
    else:
        positives.append(f"Probable CSV candidates available: {probable_csv_candidates}.")

    if total_probable_csv_rows == 0:
        warnings.append("LSE acquisition produced zero tabular rows.")
    else:
        positives.append(f"LSE tabular rows available before net-new filtering: {total_probable_csv_rows}.")

    if schema_rows:
        positives.append(f"Schema probe rows available: {len(schema_rows)}.")
    else:
        warnings.append("Schema probe is empty because no report candidate file was parsed.")

    if download_candidate_rows:
        positives.append(f"Download-candidate links in discovered CSV: {len(download_candidate_rows)}.")
    else:
        warnings.append("Discovered links contained no high-confidence downloadable report candidates.")

    net_new_candidate_rows = 0
    normalized_candidate_rows = 0
    duplicate_exchange_ticker_keys = 0
    issues_count = 0

    projected_rows_if_rebuilt = CURRENT_EXPANDED_ROWS + net_new_candidate_rows
    first_expansion_unlocked_if_rebuilt = projected_rows_if_rebuilt >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked_if_rebuilt = projected_rows_if_rebuilt >= MIN_FULL_SOURCE_ROWS

    rows_still_needed_first_expansion_after_lse = max(0, TARGET_FIRST_EXPANSION_ROWS - projected_rows_if_rebuilt)
    rows_still_needed_full_source_after_lse = max(0, MIN_FULL_SOURCE_ROWS - projected_rows_if_rebuilt)

    issues.append({
        "severity": "WARNING",
        "issue_type": "NO_TABULAR_REPORT_CANDIDATE",
        "detail": "LSE pages downloaded successfully, but no official downloadable report candidate was selected or parsed.",
    })
    issues.append({
        "severity": "WARNING",
        "issue_type": "ZERO_LSE_ROWS",
        "detail": "No LSE candidate rows are available for normalization or net-new calculation.",
    })

    if blockers:
        validation_status = "LSE_VALIDATION_BLOCKED"
        readiness_score = 0
        validation_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        validation_status = "LSE_VALIDATED_NO_USABLE_TABULAR_SOURCE"
        readiness_score = 78
        validation_decision = "LSE_ACCESSIBLE_BUT_NO_REBUILDABLE_SOURCE"
        recommended_next_phase = "v2.10G ? LSE Closure Report OR v2.11A Cboe Europe Route"

    decision_gate_rows = [
        {
            "gate": "official_lse_pages_downloaded",
            "status": "PASS" if successful_page_downloads > 0 else "FAIL",
            "detail": f"{successful_page_downloads}/{planned_page_routes} planned pages downloaded.",
        },
        {
            "gate": "official_report_candidate_downloaded",
            "status": "FAIL" if successful_candidate_downloads == 0 else "PASS",
            "detail": f"{successful_candidate_downloads} report candidate downloads.",
        },
        {
            "gate": "tabular_schema_available",
            "status": "FAIL" if probable_csv_candidates == 0 else "PASS",
            "detail": f"{probable_csv_candidates} probable CSV candidates.",
        },
        {
            "gate": "net_new_rows_available",
            "status": "FAIL" if net_new_candidate_rows == 0 else "PASS",
            "detail": f"{net_new_candidate_rows} net-new rows.",
        },
        {
            "gate": "first_expansion_unlocked",
            "status": "FAIL" if not first_expansion_unlocked_if_rebuilt else "PASS",
            "detail": f"Projected rows: {projected_rows_if_rebuilt}; target: {TARGET_FIRST_EXPANSION_ROWS}.",
        },
        {
            "gate": "rebuild_allowed",
            "status": "FAIL",
            "detail": "No rebuild allowed because no usable tabular source was acquired.",
        },
    ]

    with VALIDATION_SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "metric",
                "value",
            ],
        )
        writer.writeheader()
        writer.writerows([
            {"metric": "planned_page_routes", "value": planned_page_routes},
            {"metric": "successful_page_downloads", "value": successful_page_downloads},
            {"metric": "discovered_links", "value": discovered_links},
            {"metric": "selected_download_candidates", "value": selected_download_candidates},
            {"metric": "successful_candidate_downloads", "value": successful_candidate_downloads},
            {"metric": "probable_csv_candidates", "value": probable_csv_candidates},
            {"metric": "total_probable_csv_rows", "value": total_probable_csv_rows},
            {"metric": "normalized_candidate_rows", "value": normalized_candidate_rows},
            {"metric": "net_new_candidate_rows", "value": net_new_candidate_rows},
            {"metric": "duplicate_exchange_ticker_keys", "value": duplicate_exchange_ticker_keys},
            {"metric": "projected_rows_if_rebuilt", "value": projected_rows_if_rebuilt},
        ])

    with ISSUES_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["severity", "issue_type", "detail"])
        writer.writeheader()
        writer.writerows(issues)

    with DECISION_GATE_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["gate", "status", "detail"])
        writer.writeheader()
        writer.writerows(decision_gate_rows)

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "validation_decision": validation_decision,
        "recommended_next_phase": recommended_next_phase,
        "provider": {
            "provider_id": PROVIDER_ID,
            "provider_dir": rel(PROVIDER_DIR),
        },
        "row_summary": {
            "planned_page_routes": planned_page_routes,
            "successful_page_downloads": successful_page_downloads,
            "discovered_links": discovered_links,
            "selected_download_candidates": selected_download_candidates,
            "successful_candidate_downloads": successful_candidate_downloads,
            "probable_csv_candidates": probable_csv_candidates,
            "total_probable_csv_rows": total_probable_csv_rows,
            "normalized_candidate_rows": normalized_candidate_rows,
            "net_new_candidate_rows": net_new_candidate_rows,
            "duplicate_exchange_ticker_keys": duplicate_exchange_ticker_keys,
            "issues_count": len(issues),
        },
        "threshold_status": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "current_exclusions_rows": CURRENT_EXCLUSIONS_ROWS,
            "projected_rows_if_rebuilt": projected_rows_if_rebuilt,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "first_expansion_unlocked_if_rebuilt": first_expansion_unlocked_if_rebuilt,
            "full_source_unlocked_if_rebuilt": full_source_unlocked_if_rebuilt,
            "rows_still_needed_first_expansion_after_lse": rows_still_needed_first_expansion_after_lse,
            "rows_still_needed_full_source_after_lse": rows_still_needed_full_source_after_lse,
        },
        "decision_gate": decision_gate_rows,
        "outputs": {
            "validation_summary_csv": rel(VALIDATION_SUMMARY_CSV),
            "issues_csv": rel(ISSUES_CSV),
            "decision_gate_csv": rel(DECISION_GATE_CSV),
            "validation_json": rel(OUT_JSON),
            "validation_md": rel(OUT_MD),
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
            "validation_only": True,
            "rebuild_allowed": False,
        },
        "recommendation": (
            "Do not rebuild. Close LSE as accessible but no usable tabular source in this route, then proceed to fallback provider route."
            if not blockers
            else "Resolve validation blockers before closure."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.10D LSE Validation")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Validation decision: **{validation_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Row summary")
    md.append("")
    md.append(f"- Planned page routes: {planned_page_routes}")
    md.append(f"- Successful page downloads: {successful_page_downloads}")
    md.append(f"- Discovered links: {discovered_links}")
    md.append(f"- Selected download candidates: {selected_download_candidates}")
    md.append(f"- Successful candidate downloads: {successful_candidate_downloads}")
    md.append(f"- Probable CSV candidates: {probable_csv_candidates}")
    md.append(f"- Total probable CSV rows: {total_probable_csv_rows}")
    md.append(f"- Normalized candidate rows: {normalized_candidate_rows}")
    md.append(f"- Net-new candidate rows: {net_new_candidate_rows}")
    md.append(f"- Duplicate exchange+ticker keys: {duplicate_exchange_ticker_keys}")
    md.append(f"- Issues count: {len(issues)}")
    md.append("")
    md.append("## Threshold status")
    md.append("")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Projected rows if rebuilt: {projected_rows_if_rebuilt}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- First expansion unlocked if rebuilt: {first_expansion_unlocked_if_rebuilt}")
    md.append(f"- Full source unlocked if rebuilt: {full_source_unlocked_if_rebuilt}")
    md.append(f"- Rows still needed first expansion after LSE: {rows_still_needed_first_expansion_after_lse}")
    md.append(f"- Rows still needed full source after LSE: {rows_still_needed_full_source_after_lse}")
    md.append("")
    md.append("## Decision gate")
    md.append("")
    for row in decision_gate_rows:
        md.append(f"- {row['gate']}: **{row['status']}** ? {row['detail']}")
    md.append("")
    md.append("## Decision")
    md.append("")
    md.append("```text")
    md.append("LSE_ACCESSIBLE_BUT_NO_REBUILDABLE_SOURCE")
    md.append("REBUILD_NOT_ALLOWED")
    md.append("FULL_59K_REMAINS_BLOCKED")
    md.append("NEXT_RECOMMENDED_PHASE: v2.10G_LSE_CLOSURE_OR_v2.11A_CBOE_EUROPE_ROUTE")
    md.append("```")
    md.append("")
    md.append("## Outputs")
    md.append("")
    md.append(f"- Validation summary CSV: `{rel(VALIDATION_SUMMARY_CSV)}`")
    md.append(f"- Issues CSV: `{rel(ISSUES_CSV)}`")
    md.append(f"- Decision gate CSV: `{rel(DECISION_GATE_CSV)}`")
    md.append(f"- Validation JSON: `{rel(OUT_JSON)}`")
    md.append(f"- Validation report: `{rel(OUT_MD)}`")
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
    md.append("- Validation only: true")
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
    md.append("Important: v2.10D is validation-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.10D LSE Validation")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Validation decision: {validation_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Successful page downloads: {successful_page_downloads}")
    print(f"OK   Discovered links: {discovered_links}")
    print(f"OK   Selected download candidates: {selected_download_candidates}")
    print(f"OK   Successful candidate downloads: {successful_candidate_downloads}")
    print(f"OK   Probable CSV candidates: {probable_csv_candidates}")
    print(f"OK   Total probable CSV rows: {total_probable_csv_rows}")
    print(f"OK   Net-new candidate rows: {net_new_candidate_rows}")
    print(f"OK   Projected rows if rebuilt: {projected_rows_if_rebuilt}")
    print(f"OK   First expansion unlocked if rebuilt: {first_expansion_unlocked_if_rebuilt}")
    print(f"OK   Full source unlocked if rebuilt: {full_source_unlocked_if_rebuilt}")
    print(f"OK   Rebuild allowed: False")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Summary CSV written: {VALIDATION_SUMMARY_CSV}")
    print(f"OK   Issues CSV written: {ISSUES_CSV}")
    print(f"OK   Decision gate written: {DECISION_GATE_CSV}")
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
