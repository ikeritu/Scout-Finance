from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.5A"
METHOD = "expanded_source_revalidation_gate_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "expanded_source_revalidation_gate_v2_5a.json"
OUT_MD = OUT_DIR / "expanded_source_revalidation_gate_v2_5a.md"

CLOSURE_V2_4D = OUT_DIR / "expanded_source_partial_closure_v2_4d.json"
VALIDATION_V2_4C = OUT_DIR / "expanded_source_validation_real_v2_4c.json"
EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_4b.csv"

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

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    closure = read_json(CLOSURE_V2_4D)
    validation = read_json(VALIDATION_V2_4C)

    if not closure.get("_exists"):
        blockers.append(f"Missing v2.4D closure artifact: {rel(CLOSURE_V2_4D)}")
    else:
        positives.append(f"v2.4D closure artifact found: {rel(CLOSURE_V2_4D)}")

    if not validation.get("_exists"):
        blockers.append(f"Missing v2.4C validation artifact: {rel(VALIDATION_V2_4C)}")
    else:
        positives.append(f"v2.4C validation artifact found: {rel(VALIDATION_V2_4C)}")

    if not EXPANDED_CSV.exists():
        blockers.append(f"Missing expanded source CSV: {rel(EXPANDED_CSV)}")
    else:
        positives.append(f"Expanded source CSV exists: {rel(EXPANDED_CSV)}")

    closure_status = closure.get("closure_status")
    validation_status = validation.get("validation_status")
    full_source_gate = validation.get("full_source_gate")

    closure_summary = closure.get("summary", {}) if isinstance(closure.get("summary"), dict) else {}
    validation_summary = validation.get("summary", {}) if isinstance(validation.get("summary"), dict) else {}

    included_rows = int(closure_summary.get("included_rows") or validation_summary.get("row_count") or 0)
    issues = int(closure_summary.get("issues") or 0)
    duplicate_keys = int(closure_summary.get("duplicate_exchange_ticker_keys") or validation_summary.get("duplicate_exchange_ticker_keys") or 0)
    missing_required_columns = validation_summary.get("missing_required_columns", [])

    if closure_status == "EXPANDED_SOURCE_PARTIAL_CLOSED_WITH_CONDITIONS":
        positives.append(f"v2.4D closure status accepted: {closure_status}")
    else:
        blockers.append(f"Unexpected v2.4D closure status: {closure_status}")

    if validation_status == "EXPANDED_SOURCE_REAL_VALIDATION_PARTIAL_BELOW_TARGET_WITH_WARNINGS":
        positives.append(f"v2.4C validation status accepted: {validation_status}")
    else:
        blockers.append(f"Unexpected v2.4C validation status: {validation_status}")

    if included_rows > 0:
        positives.append(f"Expanded source has included rows: {included_rows}")
    else:
        blockers.append("Expanded source has no included rows.")

    if issues == 0:
        positives.append("No structural issues detected.")
    else:
        blockers.append(f"Structural issues detected: {issues}")

    if duplicate_keys == 0:
        positives.append("No duplicate exchange+ticker keys detected.")
    else:
        blockers.append(f"Duplicate exchange+ticker keys detected: {duplicate_keys}")

    if not missing_required_columns:
        positives.append("No missing required canonical columns.")
    else:
        blockers.append(f"Missing required canonical columns: {missing_required_columns}")

    if included_rows < TARGET_FIRST_EXPANSION_ROWS:
        warnings.append(f"Expanded source below first expansion target: {included_rows} < {TARGET_FIRST_EXPANSION_ROWS}")

    if included_rows < MIN_FULL_SOURCE_ROWS:
        warnings.append(f"Expanded source below full-source threshold: {included_rows} < {MIN_FULL_SOURCE_ROWS}")

    if full_source_gate == "FULL_SOURCE_BLOCKED_BELOW_FIRST_EXPANSION_TARGET":
        positives.append("Full 59k remains correctly blocked below first expansion target.")
    else:
        warnings.append(f"Unexpected full source gate: {full_source_gate}")

    if blockers:
        gate_decision = "EXPANDED_SOURCE_REVALIDATION_BLOCKED"
        readiness_score = 0
    elif included_rows >= MIN_FULL_SOURCE_ROWS:
        gate_decision = "EXPANDED_SOURCE_REVALIDATED_FULL_GATE_CANDIDATE"
        readiness_score = 100
    elif included_rows >= TARGET_FIRST_EXPANSION_ROWS:
        gate_decision = "EXPANDED_SOURCE_REVALIDATED_PARTIAL_READY"
        readiness_score = 85
    else:
        gate_decision = "EXPANDED_SOURCE_REVALIDATED_PARTIAL_BELOW_TARGET"
        readiness_score = 75

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "gate_decision": gate_decision,
        "readiness_score": readiness_score,
        "expanded_source": {
            "path": rel(EXPANDED_CSV),
            "exists": EXPANDED_CSV.exists(),
            "included_rows": included_rows,
            "issues": issues,
            "duplicate_exchange_ticker_keys": duplicate_keys,
            "missing_required_columns": missing_required_columns,
        },
        "targets": {
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
        },
        "inputs": {
            "v2_4d_closure": {
                "path": rel(CLOSURE_V2_4D),
                "exists": closure.get("_exists"),
                "closure_status": closure_status,
            },
            "v2_4c_validation": {
                "path": rel(VALIDATION_V2_4C),
                "exists": validation.get("_exists"),
                "validation_status": validation_status,
                "full_source_gate": full_source_gate,
            },
        },
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
            "Keep full 59k blocked. Next useful step is either add more providers or return to MVP/product work."
            if not blockers
            else "Resolve blockers before using the expanded source downstream."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.5A Expanded Source Revalidation Gate")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Gate decision: **{gate_decision}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Expanded source: `{rel(EXPANDED_CSV)}`")
    md.append(f"- Included rows: {included_rows}")
    md.append(f"- Issues: {issues}")
    md.append(f"- Duplicate exchange+ticker keys: {duplicate_keys}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full source rows: {MIN_FULL_SOURCE_ROWS}")
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
    md.append("## Positives")
    md.append("")
    for item in positives:
        md.append(f"- {item}")
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
    md.append("Important: v2.5A is a revalidation gate only. It does not execute scoring, call OpenAI, call a broker, download data, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.5A Expanded Source Revalidation Gate")
    print("=" * 92)
    print(f"OK   Gate decision: {gate_decision}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Included rows: {included_rows}")
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
