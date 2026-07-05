from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.2E"
METHOD = "full_59k_dry_run_gate_v1"

DRY_RUN_ROOT = ROOT / "outputs" / "large_universe_dry_run_59k"
OUT_JSON = DRY_RUN_ROOT / "full_59k_dry_run_gate_v2_2e.json"
OUT_MD = DRY_RUN_ROOT / "full_59k_dry_run_gate_v2_2e.md"

PLAN = ROOT / "outputs" / "large_universe_mode" / "dry_run_59k_plan_v2_2a.json"
SKELETON = DRY_RUN_ROOT / "dry_run_59k_skeleton_v2_2b.json"
SOURCE_VALIDATION = DRY_RUN_ROOT / "source_validation_v2_2c.json"
SMALL_BATCH = DRY_RUN_ROOT / "batches" / "batch_1000" / "small_batch_dry_run_v2_2d.json"

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {
            "_exists": False,
            "_path": rel(path),
            "status": "MISSING",
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_exists"] = True
        data["_path"] = rel(path)
        return data
    except Exception as exc:
        return {
            "_exists": True,
            "_path": rel(path),
            "status": "READ_ERROR",
            "error": str(exc),
        }


def controls_are_clean(payloads: list[dict]) -> tuple[bool, list[str]]:
    problems: list[str] = []

    expected_false = [
        "openai_called",
        "broker_called",
        "market_data_recalculated",
        "scoring_recalculated",
        "full_59000_universe_launched",
        "financial_advice",
    ]

    for payload in payloads:
        source = payload.get("_path", "unknown")
        controls = payload.get("controls", {})

        if not isinstance(controls, dict):
            problems.append(f"{source}: missing controls block")
            continue

        for key in expected_false:
            if controls.get(key) is not False:
                problems.append(f"{source}: control {key} is not false")

    return len(problems) == 0, problems


def main() -> int:
    DRY_RUN_ROOT.mkdir(parents=True, exist_ok=True)

    plan = read_json(PLAN)
    skeleton = read_json(SKELETON)
    source_validation = read_json(SOURCE_VALIDATION)
    small_batch = read_json(SMALL_BATCH)

    inputs = {
        "plan_v2_2a": plan,
        "skeleton_v2_2b": skeleton,
        "source_validation_v2_2c": source_validation,
        "small_batch_v2_2d": small_batch,
    }

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    for name, payload in inputs.items():
        if not payload.get("_exists"):
            blockers.append(f"Missing required input: {name} ({payload.get('_path')})")
        elif payload.get("status") == "READ_ERROR":
            blockers.append(f"Could not read required input: {name} ({payload.get('_path')})")

    if plan.get("plan_status") == "DRY_RUN_59K_PLAN_READY":
        positives.append("v2.2A 59k dry-run plan is ready.")
    else:
        blockers.append("v2.2A 59k dry-run plan is not ready.")

    skeleton_status = skeleton.get("skeleton_status")
    if skeleton_status in {"DRY_RUN_59K_SKELETON_READY", "DRY_RUN_59K_SKELETON_READY_WITH_WARNINGS"}:
        positives.append(f"v2.2B skeleton is available: {skeleton_status}.")
    else:
        blockers.append("v2.2B skeleton is not ready.")

    source_status = source_validation.get("validation_status")
    source_info = source_validation.get("source", {}) if isinstance(source_validation.get("source"), dict) else {}
    source_rows = int(source_info.get("rows") or 0)
    source_scope = source_info.get("source_scope")

    if source_status == "SOURCE_VALID_FOR_59K_DRY_RUN":
        positives.append("v2.2C source validation says source is valid for full 59k dry-run.")
    elif source_status == "SOURCE_VALID_FOR_SMALL_BATCH_WITH_WARNINGS":
        positives.append("v2.2C source validation says source is valid for small batch.")
        blockers.append(
            f"Source has {source_rows} rows and scope {source_scope}; full 59k requires approximately {EXPECTED_FULL_ROWS} rows."
        )
    else:
        blockers.append(f"v2.2C source validation is not usable: {source_status}")

    if source_rows >= MIN_FULL_SOURCE_ROWS:
        positives.append(f"Source row count is sufficient for full dry-run threshold: {source_rows}.")
    else:
        blockers.append(f"Source row count below full dry-run threshold: {source_rows} < {MIN_FULL_SOURCE_ROWS}.")

    small_batch_status = small_batch.get("dry_run_status")
    batch_info = small_batch.get("batch", {}) if isinstance(small_batch.get("batch"), dict) else {}
    written_rows = int(batch_info.get("written_rows") or 0)

    if small_batch_status in {"SMALL_BATCH_DRY_RUN_COMPLETED", "SMALL_BATCH_DRY_RUN_COMPLETED_WITH_WARNINGS"}:
        positives.append(f"v2.2D small batch completed: {small_batch_status}.")
    else:
        blockers.append(f"v2.2D small batch is not completed: {small_batch_status}")

    if written_rows >= 1000:
        positives.append(f"Small batch has expected written rows: {written_rows}.")
    else:
        blockers.append(f"Small batch written rows below expected threshold: {written_rows}.")

    clean_controls, control_problems = controls_are_clean([plan, skeleton, source_validation, small_batch])

    if clean_controls:
        positives.append("All safety controls are clean across v2.2A/B/C/D.")
    else:
        blockers.extend(control_problems)

    warnings.append("Full 59k execution remains blocked until a real full-size source is validated.")
    warnings.append("Current available source is a partial real source suitable for small-batch testing only.")

    if blockers:
        decision = "NOT_READY_FOR_FULL_59K_DRY_RUN"
        readiness_score = 0
    elif warnings:
        decision = "CONDITIONALLY_READY_FOR_FULL_59K_DRY_RUN"
        readiness_score = 85
    else:
        decision = "READY_FOR_FULL_59K_DRY_RUN"
        readiness_score = 100

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "decision": decision,
        "readiness_score": readiness_score,
        "expected_full_rows": EXPECTED_FULL_ROWS,
        "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
        "source_rows": source_rows,
        "source_scope": source_scope,
        "small_batch_written_rows": written_rows,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "inputs": {
            name: {
                "path": payload.get("_path"),
                "exists": payload.get("_exists"),
            }
            for name, payload in inputs.items()
        },
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
        },
        "recommendation": (
            "Do not run full 59k. Locate or build a real full-size source first, then repeat v2.2C and this gate."
            if decision == "NOT_READY_FOR_FULL_59K_DRY_RUN"
            else "Full 59k may be planned only with explicit approval and safeguards."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.2E Full 59k Dry Run Gate")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Decision: **{decision}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Source rows: {source_rows}")
    md.append(f"- Source scope: **{source_scope}**")
    md.append(f"- Small batch written rows: {written_rows}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
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
    md.append("## Input artifacts")
    md.append("")
    for name, value in payload["inputs"].items():
        md.append(f"- {name}: {value['path']} ? exists: {value['exists']}")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.2E is a gate only. It does not execute full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.2E Full 59k Dry Run Gate")
    print("=" * 92)
    print(f"OK   Decision: {decision}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Source rows: {source_rows}")
    print(f"OK   Small batch written rows: {written_rows}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Positives: {len(positives)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
