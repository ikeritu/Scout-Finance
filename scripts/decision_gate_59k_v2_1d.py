from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.1D"
METHOD = "decision_gate_for_59k_v1"

OUT_DIR = ROOT / "outputs" / "large_universe_mode"
OUT_JSON = OUT_DIR / "decision_gate_59k_v2_1d.json"
OUT_MD = OUT_DIR / "decision_gate_59k_v2_1d.md"

GATE_250_500_1000 = OUT_DIR / "controlled_scale_250_500_1000_v2_1a.json"
GENERATION_250_500_1000 = OUT_DIR / "generate_controlled_scale_outputs_v2_1b.json"
PERFORMANCE_UI = OUT_DIR / "performance_ui_large_mode_readiness_v2_1c.json"
MVP = ROOT / "outputs" / "mvp" / "local_research_mvp_v2_0.json"
SCALE_READINESS = ROOT / "outputs" / "scale_readiness" / "scale_readiness_audit_v1_9a.json"
CONTROLLED_20_50_100 = ROOT / "outputs" / "large_universe" / "controlled_large_universe_audit_v1_9b.json"


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


def check_controls(*payloads: dict) -> tuple[bool, list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []

    for payload in payloads:
        controls = payload.get("controls", {})
        source = payload.get("_path") or payload.get("path") or "unknown"

        if not isinstance(controls, dict):
            warnings.append(f"{source}: missing controls block in legacy artifact")
            continue

        expected_false = [
            "openai_called",
            "broker_called",
            "market_data_recalculated",
            "scoring_recalculated",
            "full_59000_universe_launched",
            "financial_advice",
        ]

        for key in expected_false:
            if key not in controls:
                warnings.append(f"{source}: legacy artifact missing control {key}")
                continue

            if controls.get(key) is not False:
                blockers.append(f"{source}: control {key} is not false")

    return len(blockers) == 0, blockers, warnings


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gate = read_input(GATE_250_500_1000)
    generation = read_input(GENERATION_250_500_1000)
    performance = read_input(PERFORMANCE_UI)
    mvp = read_input(MVP)
    scale = read_input(SCALE_READINESS)
    controlled = read_input(CONTROLLED_20_50_100)

    inputs = {
        "mvp_v2_0": mvp,
        "scale_readiness_v1_9a": scale,
        "controlled_20_50_100_v1_9b": controlled,
        "controlled_250_500_1000_gate_v2_1a": gate,
        "controlled_250_500_1000_generation_v2_1b": generation,
        "performance_ui_v2_1c": performance,
    }

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    required_inputs = [
        ("mvp_v2_0", mvp),
        ("scale_readiness_v1_9a", scale),
        ("controlled_20_50_100_v1_9b", controlled),
        ("controlled_250_500_1000_gate_v2_1a", gate),
        ("controlled_250_500_1000_generation_v2_1b", generation),
        ("performance_ui_v2_1c", performance),
    ]

    for name, payload in required_inputs:
        if not payload.get("_exists") and not payload.get("exists"):
            blockers.append(f"Missing required input: {name}")
        elif payload.get("status") == "READ_ERROR":
            blockers.append(f"Read error in required input: {name}")

    if mvp.get("mvp_status") == "LOCAL_RESEARCH_MVP_READY":
        positives.append("Local Research MVP is ready.")
    else:
        blockers.append("Local Research MVP is not ready.")

    if scale.get("readiness_status") == "READY_FOR_CONTROLLED_SCALE_TEST" and scale.get("readiness_score") == 100:
        positives.append("Scale readiness v1.9A is ready with score 100.")
    else:
        warnings.append("Scale readiness v1.9A is not fully green.")

    if controlled.get("audit_status") == "READY_FOR_NEXT_CONTROLLED_SCALE_STEP" and controlled.get("readiness_score") == 100:
        positives.append("Controlled 20/50/100 audit is ready with score 100.")
    else:
        warnings.append("Controlled 20/50/100 audit is not fully green.")

    if gate.get("audit_status") == "READY_FOR_250_500_1000_REVIEW" and gate.get("readiness_score") == 100:
        positives.append("Controlled 250/500/1000 gate is ready with score 100.")
    else:
        blockers.append("Controlled 250/500/1000 gate is not ready.")

    generation_status = generation.get("generation_status")
    if generation_status in {"CONTROLLED_SCALE_GENERATED", "CONTROLLED_SCALE_GENERATED_WITH_WARNINGS"}:
        positives.append(f"Controlled 250/500/1000 outputs generated: {generation_status}.")
        if generation_status == "CONTROLLED_SCALE_GENERATED_WITH_WARNINGS":
            warnings.append("Controlled scale generation used warnings; treat as structural/performance test.")
    else:
        blockers.append("Controlled 250/500/1000 outputs were not generated.")

    if performance.get("readiness_status") == "READY_FOR_LARGE_MODE_UI_REVIEW" and performance.get("readiness_score") == 100:
        positives.append("Performance/UI large mode readiness is green with score 100.")
    else:
        warnings.append("Performance/UI large mode readiness is not fully green.")

    controls_safe, control_blockers, control_warnings = check_controls(
        mvp,
        scale,
        controlled,
        gate,
        generation,
        performance,
    )

    if controls_safe:
        positives.append("All explicit safety controls are false: no OpenAI, no broker, no scoring recalculation, no 59k launch.")
    else:
        blockers.extend(control_blockers)

    warnings.extend(control_warnings)

    # Decision logic:
    # READY_FOR_59K_DRY_RUN only if there are no blockers and no warnings.
    # CONDITIONALLY_READY if no blockers but warnings remain.
    # NOT_READY if any blocker exists.
    if blockers:
        decision = "NOT_READY_FOR_59K"
        readiness_score = 0
    elif warnings:
        decision = "CONDITIONALLY_READY_FOR_59K_DRY_RUN"
        readiness_score = 85
    else:
        decision = "READY_FOR_59K_DRY_RUN"
        readiness_score = 100

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "decision": decision,
        "readiness_score": readiness_score,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "inputs": {
            key: {
                "path": value.get("_path") or value.get("path"),
                "exists": value.get("_exists", value.get("exists")),
            }
            for key, value in inputs.items()
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
            "A 59k dry-run can be planned as a separate explicit phase, but do not execute it automatically."
            if decision == "READY_FOR_59K_DRY_RUN"
            else "Resolve blockers or warnings before planning any 59k dry-run."
            if decision == "NOT_READY_FOR_59K"
            else "A 59k dry-run may be planned only with caution and explicit safeguards."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.1D Decision Gate for 59k")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Decision: **{decision}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
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
    md.append("## Input gates")
    md.append("")
    for key, value in payload["inputs"].items():
        md.append(f"- {key}: {value['path']} ? exists: {value['exists']}")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: this phase does not execute the 59k universe.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.1D Decision Gate for 59k")
    print("=" * 92)
    print(f"OK   Decision: {decision}")
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
