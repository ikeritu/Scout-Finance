from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.2B"
METHOD = "dry_run_59k_script_skeleton_v1"

PLAN = ROOT / "outputs" / "large_universe_mode" / "dry_run_59k_plan_v2_2a.json"

DRY_RUN_ROOT = ROOT / "outputs" / "large_universe_dry_run_59k"
REPORT_JSON = DRY_RUN_ROOT / "dry_run_59k_skeleton_v2_2b.json"
REPORT_MD = DRY_RUN_ROOT / "dry_run_59k_skeleton_v2_2b.md"

PROTECTED_OUTPUT_DIRS = [
    ROOT / "outputs" / "scouting",
    ROOT / "outputs" / "mvp",
    ROOT / "outputs" / "research",
    ROOT / "outputs" / "scoring",
]

DEFAULT_MAX_LIMIT = 5000
FULL_59K_THRESHOLD = 59000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def count_csv_rows_and_columns(path: Path) -> tuple[int, list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = sum(1 for _ in reader)
        columns = list(reader.fieldnames or [])
    return rows, columns


def is_protected_path(path: Path) -> bool:
    resolved = path.resolve()

    for protected in PROTECTED_OUTPUT_DIRS:
        try:
            resolved.relative_to(protected.resolve())
            return True
        except ValueError:
            continue

    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scout Finance v2.2B safeguarded 59k dry-run skeleton. This script does not execute full 59k by default."
    )

    parser.add_argument(
        "--source",
        type=str,
        default="",
        help="Path to source CSV. Required for validation/execution planning.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum rows to process in a future dry-run batch. Must be explicit.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DRY_RUN_ROOT),
        help="Isolated output directory for dry-run artifacts.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Allow skeleton to perform a controlled validation pass. Does not run scoring.",
    )
    parser.add_argument(
        "--allow-full-59k",
        action="store_true",
        help="Reserved safeguard. Full 59k is still blocked in v2.2B.",
    )
    parser.add_argument(
        "--confirm",
        type=str,
        default="",
        help="Reserved confirmation string for future phases.",
    )

    return parser


def main() -> int:
    started = time.perf_counter()
    args = build_parser().parse_args()

    DRY_RUN_ROOT.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    plan_exists = PLAN.exists()
    plan_status = None

    if not plan_exists:
        blockers.append(f"Missing v2.2A plan: {rel(PLAN)}")
    else:
        try:
            plan = load_json(PLAN)
            plan_status = plan.get("plan_status")
            if plan_status == "DRY_RUN_59K_PLAN_READY":
                positives.append("v2.2A dry-run plan is ready.")
            else:
                blockers.append(f"v2.2A plan status is not ready: {plan_status}")
        except Exception as exc:
            blockers.append(f"Could not read v2.2A plan: {exc}")

    source_path = Path(args.source).expanduser() if args.source else None
    source_info: dict[str, object] = {
        "provided": bool(args.source),
        "path": args.source or None,
        "exists": False,
        "rows": None,
        "columns": [],
        "has_ticker": False,
    }

    if not args.source:
        warnings.append("No --source provided. Skeleton created; source validation remains pending.")
    else:
        source_abs = source_path if source_path and source_path.is_absolute() else ROOT / str(source_path)
        source_info["path"] = rel(source_abs)

        if not source_abs.exists():
            blockers.append(f"Source file does not exist: {rel(source_abs)}")
        elif not source_abs.is_file():
            blockers.append(f"Source path is not a file: {rel(source_abs)}")
        else:
            try:
                rows, columns = count_csv_rows_and_columns(source_abs)
                source_info["exists"] = True
                source_info["rows"] = rows
                source_info["columns"] = columns
                source_info["has_ticker"] = "ticker" in columns

                positives.append(f"Source CSV is readable with {rows} rows.")

                if "ticker" not in columns:
                    blockers.append("Source CSV is missing required column: ticker")

                if rows < 1000:
                    warnings.append("Source has fewer than 1000 rows; useful only for very small validation.")

            except Exception as exc:
                blockers.append(f"Could not inspect source CSV: {exc}")

    output_dir = Path(args.output_dir).expanduser()
    output_abs = output_dir if output_dir.is_absolute() else ROOT / output_dir

    if is_protected_path(output_abs):
        blockers.append(f"Output directory points to protected active outputs: {rel(output_abs)}")
    else:
        positives.append(f"Output directory is isolated: {rel(output_abs)}")

    if args.limit <= 0:
        warnings.append("No positive --limit provided. No batch execution can happen in this skeleton.")
    else:
        positives.append(f"Explicit row limit provided: {args.limit}")

    if args.limit > DEFAULT_MAX_LIMIT and not args.allow_full_59k:
        warnings.append(
            f"Limit {args.limit} exceeds recommended skeleton max {DEFAULT_MAX_LIMIT}; future phase approval required."
        )

    if args.limit >= FULL_59K_THRESHOLD:
        blockers.append("Full 59k execution is blocked in v2.2B, even if --allow-full-59k is provided.")

    if args.allow_full_59k:
        warnings.append("--allow-full-59k was provided, but v2.2B still blocks full execution by design.")

    if args.execute:
        warnings.append("--execute was provided, but v2.2B skeleton performs validation only; no scoring/run executed.")
    else:
        positives.append("Safe default: --execute not provided.")

    dry_run_actions = {
        "source_validation_performed": bool(args.source),
        "batch_execution_performed": False,
        "scoring_performed": False,
        "files_generated_for_59k": False,
        "active_outputs_overwritten": False,
    }

    if blockers:
        skeleton_status = "DRY_RUN_59K_SKELETON_BLOCKED"
        readiness_score = 0
    elif warnings:
        skeleton_status = "DRY_RUN_59K_SKELETON_READY_WITH_WARNINGS"
        readiness_score = 85
    else:
        skeleton_status = "DRY_RUN_59K_SKELETON_READY"
        readiness_score = 100

    elapsed_seconds = round(time.perf_counter() - started, 4)

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "skeleton_status": skeleton_status,
        "readiness_score": readiness_score,
        "elapsed_seconds": elapsed_seconds,
        "arguments": {
            "source": args.source,
            "limit": args.limit,
            "output_dir": str(args.output_dir),
            "execute": bool(args.execute),
            "allow_full_59k": bool(args.allow_full_59k),
            "confirm": args.confirm,
        },
        "source_info": source_info,
        "dry_run_actions": dry_run_actions,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "inputs": {
            "plan_v2_2a": {
                "path": rel(PLAN),
                "exists": plan_exists,
                "plan_status": plan_status,
            }
        },
        "protected_output_dirs": [rel(path) for path in PROTECTED_OUTPUT_DIRS],
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
        },
        "recommendation": (
            "Proceed to v2.2C source validation after providing a real source CSV."
            if not blockers
            else "Resolve blockers before continuing to v2.2C."
        ),
    }

    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.2B 59k Dry Run Script Skeleton")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Skeleton status: **{skeleton_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Elapsed seconds: {elapsed_seconds}")
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
    md.append("## Arguments")
    md.append("")
    for key, value in payload["arguments"].items():
        md.append(f"- {key}: {value}")
    md.append("")
    md.append("## Dry-run actions")
    md.append("")
    for key, value in dry_run_actions.items():
        md.append(f"- {key}: {value}")
    md.append("")
    md.append("## Source info")
    md.append("")
    for key, value in source_info.items():
        if key == "columns":
            md.append(f"- {key}: {len(value)} columns")
        else:
            md.append(f"- {key}: {value}")
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
    md.append("## Protected output directories")
    md.append("")
    for item in payload["protected_output_dirs"]:
        md.append(f"- `{item}`")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.2B does not execute the 59k universe and does not run scoring.")

    REPORT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.2B 59k Dry Run Script Skeleton")
    print("=" * 92)
    print(f"OK   Skeleton status: {skeleton_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Positives: {len(positives)}")
    print(f"OK   JSON written: {REPORT_JSON}")
    print(f"OK   Report written: {REPORT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
