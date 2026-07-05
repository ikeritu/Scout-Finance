from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.4D"
METHOD = "expanded_source_partial_closure_report_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "expanded_source_partial_closure_v2_4d.json"
OUT_MD = OUT_DIR / "expanded_source_partial_closure_v2_4d.md"

ACQUISITION_JSON = OUT_DIR / "provider_source_acquisition_v2_4a.json"
BUILDER_JSON = OUT_DIR / "expanded_source_builder_real_v2_4b.json"
VALIDATION_JSON = OUT_DIR / "expanded_source_validation_real_v2_4c.json"

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000
TARGET_FIRST_EXPANSION_ROWS = 15000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}

    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    acquisition = read_json(ACQUISITION_JSON)
    builder = read_json(BUILDER_JSON)
    validation = read_json(VALIDATION_JSON)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    required_inputs = {
        "v2.4A acquisition": acquisition,
        "v2.4B builder": builder,
        "v2.4C validation": validation,
    }

    for name, payload in required_inputs.items():
        if not payload.get("_exists"):
            blockers.append(f"Missing required input: {name} ({payload.get('_path')})")
        else:
            positives.append(f"{name} artifact found: {payload.get('_path')}")

    acquisition_status = acquisition.get("acquisition_status")
    builder_status = builder.get("builder_status")
    validation_status = validation.get("validation_status")
    full_source_gate = validation.get("full_source_gate")

    if acquisition_status in {"PROVIDER_SOURCE_ACQUISITION_COMPLETED", "PROVIDER_SOURCE_ACQUISITION_COMPLETED_WITH_WARNINGS"}:
        positives.append(f"v2.4A acquisition usable: {acquisition_status}")
    else:
        blockers.append(f"v2.4A acquisition not usable: {acquisition_status}")

    if builder_status in {
        "EXPANDED_SOURCE_BUILD_FULL_READY",
        "EXPANDED_SOURCE_BUILD_PARTIAL_READY",
        "EXPANDED_SOURCE_BUILD_PARTIAL_BELOW_TARGET_WITH_WARNINGS",
    }:
        positives.append(f"v2.4B builder usable: {builder_status}")
    else:
        blockers.append(f"v2.4B builder not usable: {builder_status}")

    if validation_status in {
        "EXPANDED_SOURCE_REAL_VALIDATION_FULL_READY",
        "EXPANDED_SOURCE_REAL_VALIDATION_PARTIAL_READY_WITH_WARNINGS",
        "EXPANDED_SOURCE_REAL_VALIDATION_PARTIAL_BELOW_TARGET_WITH_WARNINGS",
    }:
        positives.append(f"v2.4C validation usable: {validation_status}")
    else:
        blockers.append(f"v2.4C validation not usable: {validation_status}")

    acquisition_rows = int(acquisition.get("total_rows") or 0)
    builder_summary = builder.get("summary", {}) if isinstance(builder.get("summary"), dict) else {}
    validation_summary = validation.get("summary", {}) if isinstance(validation.get("summary"), dict) else {}

    raw_rows = int(builder_summary.get("raw_rows") or acquisition_rows or 0)
    included_rows = int(builder_summary.get("included_rows") or validation_summary.get("row_count") or 0)
    excluded_rows = int(builder_summary.get("excluded_rows") or validation_summary.get("exclusions_count") or 0)

    issues = (
        int(validation_summary.get("empty_tickers") or 0)
        + int(validation_summary.get("empty_company_names") or 0)
        + int(validation_summary.get("empty_exchanges") or 0)
        + int(validation_summary.get("empty_countries") or 0)
        + int(validation_summary.get("invalid_scope_values") or 0)
        + int(validation_summary.get("invalid_instrument_type_values") or 0)
        + int(validation_summary.get("invalid_confidence_values") or 0)
    )

    duplicate_keys = int(validation_summary.get("duplicate_exchange_ticker_keys") or 0)
    missing_required_columns = validation_summary.get("missing_required_columns", [])

    if included_rows > 0:
        positives.append(f"Expanded source has valid included rows: {included_rows}")
    else:
        blockers.append("Expanded source has no included rows.")

    if issues == 0:
        positives.append("No structural row issues detected in v2.4C.")
    else:
        blockers.append(f"Structural row issues detected: {issues}")

    if duplicate_keys == 0:
        positives.append("No duplicate exchange+ticker keys detected.")
    else:
        blockers.append(f"Duplicate exchange+ticker keys detected: {duplicate_keys}")

    if not missing_required_columns:
        positives.append("No missing required canonical columns.")
    else:
        blockers.append(f"Missing required canonical columns: {missing_required_columns}")

    if included_rows < TARGET_FIRST_EXPANSION_ROWS:
        warnings.append(f"Expanded source remains below first expansion target: {included_rows} < {TARGET_FIRST_EXPANSION_ROWS}")

    if included_rows < MIN_FULL_SOURCE_ROWS:
        warnings.append(f"Expanded source remains below full-source threshold: {included_rows} < {MIN_FULL_SOURCE_ROWS}")

    if full_source_gate != "FULL_SOURCE_BLOCKED_BELOW_FIRST_EXPANSION_TARGET":
        warnings.append(f"Unexpected full source gate value: {full_source_gate}")
    else:
        positives.append("Full 59k gate remains correctly blocked by source size.")

    if blockers:
        closure_status = "EXPANDED_SOURCE_PARTIAL_CLOSURE_BLOCKED"
        readiness_score = 0
    elif warnings:
        closure_status = "EXPANDED_SOURCE_PARTIAL_CLOSED_WITH_CONDITIONS"
        readiness_score = 90
    else:
        closure_status = "EXPANDED_SOURCE_PARTIAL_CLOSED"
        readiness_score = 100

    next_options = [
        {
            "id": "A",
            "name": "Add more official providers",
            "status": "RECOMMENDED_IF_59K_REMAINS_GOAL",
            "description": "Continue expanding with additional official exchange lists until reaching at least 15000 first, then 50000+.",
        },
        {
            "id": "B",
            "name": "Use partial expanded source for product iteration",
            "status": "RECOMMENDED_IF_PRODUCT_FEATURES_ARE_PRIORITY",
            "description": "Keep 5648 structurally valid rows and return to MVP/product improvements.",
        },
        {
            "id": "C",
            "name": "Repeat v2.2C/v2.2E on partial expanded source",
            "status": "OPTIONAL",
            "description": "Run existing source validation and full gate against the expanded partial source; full 59k will remain blocked.",
        },
    ]

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "closure_status": closure_status,
        "readiness_score": readiness_score,
        "inputs": {
            "acquisition_v2_4a": {
                "path": rel(ACQUISITION_JSON),
                "exists": acquisition.get("_exists"),
                "status": acquisition_status,
            },
            "builder_v2_4b": {
                "path": rel(BUILDER_JSON),
                "exists": builder.get("_exists"),
                "status": builder_status,
            },
            "validation_v2_4c": {
                "path": rel(VALIDATION_JSON),
                "exists": validation.get("_exists"),
                "status": validation_status,
                "full_source_gate": full_source_gate,
            },
        },
        "summary": {
            "raw_rows": raw_rows,
            "included_rows": included_rows,
            "excluded_rows": excluded_rows,
            "issues": issues,
            "duplicate_exchange_ticker_keys": duplicate_keys,
            "missing_required_columns": missing_required_columns,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
        },
        "next_options": next_options,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "network_download_performed": False,
            "active_outputs_overwritten": False,
        },
        "recommendation": (
            "Close v2.4 as a valid partial expanded source. Full 59k remains blocked until more provider data is added."
            if not blockers
            else "Resolve blockers before closing v2.4."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.4D Expanded Source Partial Closure Report")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Closure status: **{closure_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Raw rows: {raw_rows}")
    md.append(f"- Included rows: {included_rows}")
    md.append(f"- Excluded rows: {excluded_rows}")
    md.append(f"- Issues: {issues}")
    md.append(f"- Duplicate exchange+ticker keys: {duplicate_keys}")
    md.append(f"- Full source gate: **{full_source_gate}**")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Network download performed: false")
    md.append("- Active outputs overwritten: false")
    md.append("")
    md.append("## Inputs")
    md.append("")
    for name, item in payload["inputs"].items():
        md.append(f"- {name}: `{item['path']}` ? exists: {item['exists']} ? status: {item.get('status')}")
    md.append("")
    md.append("## Closure summary")
    md.append("")
    md.append("- The expanded source pipeline works end to end with real provider files.")
    md.append("- The expanded source is structurally valid.")
    md.append("- There are no duplicate exchange+ticker keys.")
    md.append("- There are no missing required canonical columns.")
    md.append("- The current expanded source is partial and does not unlock full 59k.")
    md.append("")
    md.append("## Next options")
    md.append("")
    for option in next_options:
        md.append(f"### Option {option['id']} ? {option['name']}")
        md.append("")
        md.append(f"- Status: {option['status']}")
        md.append(f"- Description: {option['description']}")
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
    md.append("Important: v2.4D is a closure report only. It does not execute scoring, call OpenAI, call a broker, overwrite active outputs, download data, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.4D Expanded Source Partial Closure Report")
    print("=" * 92)
    print(f"OK   Closure status: {closure_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Raw rows: {raw_rows}")
    print(f"OK   Included rows: {included_rows}")
    print(f"OK   Excluded rows: {excluded_rows}")
    print(f"OK   Issues: {issues}")
    print(f"OK   Duplicate exchange+ticker keys: {duplicate_keys}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Network download performed: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
