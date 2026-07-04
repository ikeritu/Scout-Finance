from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.2A"
METHOD = "dry_run_59k_plan_v1"

OUT_DIR = ROOT / "outputs" / "large_universe_mode"
OUT_JSON = OUT_DIR / "dry_run_59k_plan_v2_2a.json"
OUT_MD = OUT_DIR / "dry_run_59k_plan_v2_2a.md"

CLOSURE = OUT_DIR / "large_universe_mode_closure_v2_1e.json"
DECISION = OUT_DIR / "decision_gate_59k_v2_1d.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_optional_json(path: Path) -> dict:
    if not path.exists():
        return {
            "exists": False,
            "path": rel(path),
            "status": "MISSING",
        }

    try:
        data = load_json(path)
        data["_exists"] = True
        data["_path"] = rel(path)
        return data
    except Exception as exc:
        return {
            "exists": True,
            "path": rel(path),
            "status": "READ_ERROR",
            "error": str(exc),
        }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    closure = read_optional_json(CLOSURE)
    decision = read_optional_json(DECISION)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    closure_status = closure.get("closure_status")
    decision_59k = decision.get("decision")

    if closure_status == "LARGE_UNIVERSE_MODE_CLOSED_WITH_CONDITIONS":
        positives.append("v2.1 closure exists and allows conditional planning.")
    elif closure_status == "LARGE_UNIVERSE_MODE_CLOSED":
        positives.append("v2.1 closure exists and is fully closed.")
    else:
        blockers.append("v2.1 closure is missing or not valid.")

    if decision_59k == "CONDITIONALLY_READY_FOR_59K_DRY_RUN":
        positives.append("v2.1D allows planning a conditional 59k dry-run.")
        warnings.append("59k dry-run must remain conditional until source validation and safeguards are implemented.")
    elif decision_59k == "READY_FOR_59K_DRY_RUN":
        positives.append("v2.1D allows planning a 59k dry-run.")
    else:
        blockers.append("v2.1D does not allow planning a 59k dry-run.")

    plan_status = "DRY_RUN_59K_PLAN_READY" if not blockers else "DRY_RUN_59K_PLAN_BLOCKED"
    readiness_score = 90 if not blockers else 0

    dry_run_folder = "outputs/large_universe_dry_run_59k"

    source_requirements = [
        "A real source file or dataset containing approximately 59k companies must be identified.",
        "The source must include at least a ticker column.",
        "Optional but recommended columns: company_name, exchange, sector, industry, country, market_cap.",
        "The source must be read-only during dry-run generation.",
        "The source must be validated before any batch execution.",
    ]

    safety_rules = [
        "Do not call OpenAI during v2.2 dry-run planning or first execution.",
        "Do not call any broker or trading API.",
        "Do not overwrite active MVP outputs.",
        "Write all 59k dry-run outputs to a separate folder.",
        "Keep scoring deterministic.",
        "Do not recalculate production scoring unless explicitly approved.",
        "Require a clean git checkpoint before any execution.",
        "Record runtime, row counts, file sizes, and errors.",
        "Stop immediately if memory/runtime/file-size limits are exceeded.",
    ]

    execution_limits = {
        "first_batch_limit_rows": 1000,
        "second_batch_limit_rows": 5000,
        "full_dry_run_rows": 59000,
        "max_single_output_file_mb_warning": 100,
        "max_total_output_mb_warning": 1000,
        "max_runtime_minutes_warning": 60,
    }

    phases = [
        {
            "phase": "v2.2B",
            "name": "59k Dry Run Script Skeleton",
            "purpose": "Create a safeguarded dry-run script with no execution by default.",
            "executes_59k": False,
        },
        {
            "phase": "v2.2C",
            "name": "59k Source Validation",
            "purpose": "Validate source rows, required columns and duplicate tickers.",
            "executes_59k": False,
        },
        {
            "phase": "v2.2D",
            "name": "Small Batch Dry Run",
            "purpose": "Run a controlled batch, initially 1k rows.",
            "executes_59k": False,
        },
        {
            "phase": "v2.2E",
            "name": "Full Dry Run Gate",
            "purpose": "Decide whether full 59k dry-run is allowed.",
            "executes_59k": False,
        },
        {
            "phase": "v2.2F",
            "name": "Full 59k Dry Run",
            "purpose": "Execute full dry-run only after explicit approval.",
            "executes_59k": True,
            "requires_explicit_approval": True,
        },
    ]

    rollback_plan = [
        "Keep current tag v2.1_large_universe_mode_closed as rollback anchor.",
        "Create a new checkpoint tag before any full 59k dry-run.",
        "Never overwrite outputs/scouting or outputs/mvp during dry-run.",
        "If the dry-run fails, delete only outputs/large_universe_dry_run_59k.",
        "Return to the last clean commit if code changes are introduced.",
    ]

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "plan_status": plan_status,
        "readiness_score": readiness_score,
        "source_requirements": source_requirements,
        "safety_rules": safety_rules,
        "execution_limits": execution_limits,
        "dry_run_folder": dry_run_folder,
        "planned_phases": phases,
        "rollback_plan": rollback_plan,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "inputs": {
            "closure_v2_1e": {
                "path": closure.get("_path") or closure.get("path"),
                "exists": closure.get("_exists", closure.get("exists")),
                "closure_status": closure_status,
            },
            "decision_gate_v2_1d": {
                "path": decision.get("_path") or decision.get("path"),
                "exists": decision.get("_exists", decision.get("exists")),
                "decision": decision_59k,
            },
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
            "Proceed to v2.2B script skeleton. Do not execute the 59k universe yet."
            if not blockers
            else "Resolve blockers before preparing any 59k dry-run scripts."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.2A 59k Dry Run Plan")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Plan status: **{plan_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Dry-run folder: `{dry_run_folder}`")
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
    md.append("## Source requirements")
    md.append("")
    for item in source_requirements:
        md.append(f"- {item}")
    md.append("")
    md.append("## Safety rules")
    md.append("")
    for item in safety_rules:
        md.append(f"- {item}")
    md.append("")
    md.append("## Execution limits")
    md.append("")
    for key, value in execution_limits.items():
        md.append(f"- {key}: {value}")
    md.append("")
    md.append("## Planned phases")
    md.append("")
    for item in phases:
        md.append(f"- **{item['phase']} ? {item['name']}**: {item['purpose']}")
    md.append("")
    md.append("## Rollback plan")
    md.append("")
    for item in rollback_plan:
        md.append(f"- {item}")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: this plan does not execute the 59k universe.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.2A 59k Dry Run Plan")
    print("=" * 92)
    print(f"OK   Plan status: {plan_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
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
