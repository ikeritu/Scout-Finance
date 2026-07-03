from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.1E"
METHOD = "large_universe_mode_closure_report_v1"

OUT_DIR = ROOT / "outputs" / "large_universe_mode"
OUT_JSON = OUT_DIR / "large_universe_mode_closure_v2_1e.json"
OUT_MD = OUT_DIR / "large_universe_mode_closure_v2_1e.md"

MVP = ROOT / "outputs" / "mvp" / "local_research_mvp_v2_0.json"
GATE_250_500_1000 = OUT_DIR / "controlled_scale_250_500_1000_v2_1a.json"
GENERATION_250_500_1000 = OUT_DIR / "generate_controlled_scale_outputs_v2_1b.json"
PERFORMANCE_UI = OUT_DIR / "performance_ui_large_mode_readiness_v2_1c.json"
DECISION_59K = OUT_DIR / "decision_gate_59k_v2_1d.json"

INPUTS = {
    "local_research_mvp_v2_0": MVP,
    "controlled_scale_gate_v2_1a": GATE_250_500_1000,
    "controlled_scale_generation_v2_1b": GENERATION_250_500_1000,
    "performance_ui_readiness_v2_1c": PERFORMANCE_UI,
    "decision_gate_59k_v2_1d": DECISION_59K,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_input(path: Path) -> dict:
    if not path.exists():
        return {
            "path": rel(path),
            "exists": False,
            "status": "MISSING",
        }

    try:
        data = load_json(path)
        data["_path"] = rel(path)
        data["_exists"] = True
        return data
    except Exception as exc:
        return {
            "path": rel(path),
            "exists": True,
            "status": "READ_ERROR",
            "error": str(exc),
        }


def collect_controls(payloads: list[dict]) -> dict[str, bool]:
    control_keys = [
        "openai_called",
        "broker_called",
        "market_data_recalculated",
        "scoring_recalculated",
        "full_59000_universe_launched",
        "financial_advice",
    ]

    combined = {key: False for key in control_keys}

    for payload in payloads:
        controls = payload.get("controls", {})
        if not isinstance(controls, dict):
            continue

        for key in control_keys:
            if controls.get(key) is True:
                combined[key] = True

    return combined


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    loaded = {name: read_input(path) for name, path in INPUTS.items()}
    payloads = list(loaded.values())

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    for name, payload in loaded.items():
        if not payload.get("_exists", payload.get("exists", False)):
            blockers.append(f"Missing input: {name}")
        elif payload.get("status") == "READ_ERROR":
            blockers.append(f"Read error: {name}")

    mvp = loaded["local_research_mvp_v2_0"]
    gate = loaded["controlled_scale_gate_v2_1a"]
    generation = loaded["controlled_scale_generation_v2_1b"]
    performance = loaded["performance_ui_readiness_v2_1c"]
    decision = loaded["decision_gate_59k_v2_1d"]

    if mvp.get("mvp_status") == "LOCAL_RESEARCH_MVP_READY":
        positives.append("v2.0 Local Research MVP is ready.")
    else:
        warnings.append("v2.0 Local Research MVP is not fully ready.")

    if gate.get("audit_status") == "READY_FOR_250_500_1000_REVIEW":
        positives.append("v2.1A controlled scale gate passed for 250 / 500 / 1000.")
    else:
        warnings.append("v2.1A controlled scale gate did not pass cleanly.")

    generation_status = generation.get("generation_status")
    if generation_status in {"CONTROLLED_SCALE_GENERATED", "CONTROLLED_SCALE_GENERATED_WITH_WARNINGS"}:
        positives.append(f"v2.1B controlled scale outputs generated: {generation_status}.")
        if generation_status == "CONTROLLED_SCALE_GENERATED_WITH_WARNINGS":
            warnings.append("v2.1B generated structural/performance test outputs, not fresh real-universe data.")
    else:
        blockers.append("v2.1B controlled scale outputs were not generated.")

    if performance.get("readiness_status") == "READY_FOR_LARGE_MODE_UI_REVIEW":
        positives.append("v2.1C performance/UI readiness passed.")
    else:
        warnings.append("v2.1C performance/UI readiness did not pass cleanly.")

    decision_value = decision.get("decision")
    if decision_value == "READY_FOR_59K_DRY_RUN":
        positives.append("v2.1D decision gate says ready for a future 59k dry-run.")
    elif decision_value == "CONDITIONALLY_READY_FOR_59K_DRY_RUN":
        positives.append("v2.1D decision gate says conditionally ready for a future 59k dry-run.")
        warnings.append("59k dry-run is conditional and requires explicit safeguards.")
    else:
        blockers.append("v2.1D decision gate does not allow a 59k dry-run.")

    controls = collect_controls(payloads)

    for key, value in controls.items():
        if value is True:
            blockers.append(f"Safety control violated: {key} is true")

    if not any(controls.values()):
        positives.append("Safety controls remain clean across closure inputs.")

    mandatory_conditions = [
        "Create a separate explicit 59k dry-run phase before any execution.",
        "Do not call OpenAI during the first 59k dry-run.",
        "Do not call any broker during the first 59k dry-run.",
        "Keep scoring deterministic and avoid recalculating production scoring unless explicitly approved.",
        "Use dry-run outputs in a separate folder, not overwriting active MVP outputs.",
        "Add runtime, memory and file-size measurement to the dry-run.",
        "Keep a rollback/checkpoint commit before running any 59k process.",
        "Document whether the 59k source is real universe data or structural test data.",
    ]

    if blockers:
        closure_status = "LARGE_UNIVERSE_MODE_CLOSURE_BLOCKED"
        readiness_score = 0
    elif warnings:
        closure_status = "LARGE_UNIVERSE_MODE_CLOSED_WITH_CONDITIONS"
        readiness_score = 90
    else:
        closure_status = "LARGE_UNIVERSE_MODE_CLOSED"
        readiness_score = 100

    report = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "closure_status": closure_status,
        "readiness_score": readiness_score,
        "decision_59k": decision_value,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "mandatory_conditions_before_59k": mandatory_conditions,
        "inputs": {
            name: {
                "path": payload.get("_path") or payload.get("path"),
                "exists": payload.get("_exists", payload.get("exists")),
            }
            for name, payload in loaded.items()
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
            "Close v2.1 as conditionally ready. Next phase should be v2.2A 59k Dry Run Plan, not execution."
            if closure_status == "LARGE_UNIVERSE_MODE_CLOSED_WITH_CONDITIONS"
            else "Close v2.1 and prepare v2.2A 59k Dry Run Plan."
            if closure_status == "LARGE_UNIVERSE_MODE_CLOSED"
            else "Resolve blockers before closing v2.1."
        ),
    }

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.1E Large Universe Mode Closure Report")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {report['created_at']}")
    md.append(f"- Closure status: **{closure_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- 59k decision: **{decision_value}**")
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
    md.append("## Warnings / Conditions")
    md.append("")
    if warnings:
        for item in warnings:
            md.append(f"- {item}")
    else:
        md.append("- No warnings detected.")
    md.append("")
    md.append("## Mandatory conditions before any 59k run")
    md.append("")
    for item in mandatory_conditions:
        md.append(f"- {item}")
    md.append("")
    md.append("## Input artifacts")
    md.append("")
    for name, value in report["inputs"].items():
        md.append(f"- {name}: {value['path']} ? exists: {value['exists']}")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(report["recommendation"])
    md.append("")
    md.append("Important: this closure report does not execute the 59k universe.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.1E Large Universe Mode Closure Report")
    print("=" * 92)
    print(f"OK   Closure status: {closure_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   59k decision: {decision_value}")
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
