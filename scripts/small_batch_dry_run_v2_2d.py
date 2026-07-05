from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.2D"
METHOD = "small_batch_dry_run_v1"

DEFAULT_SOURCE = ROOT / "data" / "raw" / "universe_source_real_clean.csv"
SOURCE_VALIDATION = ROOT / "outputs" / "large_universe_dry_run_59k" / "source_validation_v2_2c.json"

DRY_RUN_ROOT = ROOT / "outputs" / "large_universe_dry_run_59k"
BATCH_ROOT = DRY_RUN_ROOT / "batches"

DEFAULT_LIMIT = 1000
MAX_ALLOWED_LIMIT = 5000

PROTECTED_OUTPUT_DIRS = [
    ROOT / "outputs" / "scouting",
    ROOT / "outputs" / "mvp",
    ROOT / "outputs" / "research",
    ROOT / "outputs" / "scoring",
]

COLUMN_MAPPING = {
    "Symbol": "ticker",
    "Name": "company_name",
    "Exchange": "exchange",
    "Country": "country",
    "Sector": "sector",
    "Industry": "industry",
    "Market Cap": "market_cap",
    "Source": "source",
    "instrument_type": "instrument_type",
    "instrument_scope": "instrument_scope",
    "classification_confidence": "classification_confidence",
    "classification_reason": "classification_reason",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def is_protected_path(path: Path) -> bool:
    resolved = path.resolve()

    for protected in PROTECTED_OUTPUT_DIRS:
        try:
            resolved.relative_to(protected.resolve())
            return True
        except ValueError:
            continue

    return False


def normalize_row(row: dict[str, str], index: int) -> dict[str, object]:
    normalized: dict[str, object] = {
        "dry_run_rank": index,
    }

    for source_col, canonical_col in COLUMN_MAPPING.items():
        normalized[canonical_col] = (row.get(source_col) or "").strip()

    normalized["ticker"] = str(normalized.get("ticker") or "").upper().strip()
    normalized["dry_run_status"] = "SOURCE_ONLY"
    normalized["scoring_performed"] = False
    normalized["openai_called"] = False
    normalized["broker_called"] = False
    normalized["financial_advice"] = False

    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scout Finance v2.2D small batch dry-run. No scoring, no OpenAI, no broker.")
    parser.add_argument(
        "--source",
        type=str,
        default=str(DEFAULT_SOURCE),
        help="Source CSV for small batch dry-run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Maximum rows to include in the small batch dry-run.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="Optional isolated output directory. Defaults to outputs/large_universe_dry_run_59k/batches/batch_<limit>.",
    )
    parser.add_argument(
        "--confirm",
        type=str,
        default="",
        help="Must be RUN_SMALL_BATCH_DRY_RUN to write batch outputs.",
    )
    return parser


def main() -> int:
    started = time.perf_counter()
    args = build_parser().parse_args()

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    source = resolve_path(args.source)

    if args.output_dir:
        output_dir = resolve_path(args.output_dir)
    else:
        output_dir = BATCH_ROOT / f"batch_{args.limit}"

    batch_csv = output_dir / "small_batch_universe_v2_2d.csv"
    report_json = output_dir / "small_batch_dry_run_v2_2d.json"
    report_md = output_dir / "small_batch_dry_run_v2_2d.md"

    if args.confirm != "RUN_SMALL_BATCH_DRY_RUN":
        blockers.append("Missing confirmation: use --confirm RUN_SMALL_BATCH_DRY_RUN")

    if args.limit <= 0:
        blockers.append("Limit must be positive.")

    if args.limit > MAX_ALLOWED_LIMIT:
        blockers.append(f"Limit {args.limit} exceeds max allowed small-batch limit {MAX_ALLOWED_LIMIT}.")

    if is_protected_path(output_dir):
        blockers.append(f"Output directory points to protected active outputs: {rel(output_dir)}")
    else:
        positives.append(f"Output directory is isolated: {rel(output_dir)}")

    validation_exists = SOURCE_VALIDATION.exists()
    validation_status = None
    validation_scope = None

    if not validation_exists:
        blockers.append(f"Missing v2.2C source validation artifact: {rel(SOURCE_VALIDATION)}")
    else:
        validation = load_json(SOURCE_VALIDATION)
        validation_status = validation.get("validation_status")
        validation_scope = validation.get("source", {}).get("source_scope")

        if validation_status == "SOURCE_VALID_FOR_SMALL_BATCH_WITH_WARNINGS":
            positives.append("v2.2C source validation allows small batch with warnings.")
            warnings.append("Source is partial real source, not full 59k.")
        elif validation_status == "SOURCE_VALID_FOR_59K_DRY_RUN":
            positives.append("v2.2C source validation allows full-source dry-run planning.")
        else:
            blockers.append(f"v2.2C source validation is not usable: {validation_status}")

    columns: list[str] = []
    rows: list[dict[str, str]] = []

    if not source.exists():
        blockers.append(f"Source file does not exist: {rel(source)}")
    elif not source.is_file():
        blockers.append(f"Source path is not a file: {rel(source)}")
    else:
        try:
            columns, rows = read_csv(source)
            positives.append(f"Source CSV readable: {rel(source)}")
        except Exception as exc:
            blockers.append(f"Could not read source CSV: {exc}")

    if rows:
        if "Symbol" not in columns:
            blockers.append("Source CSV missing required mapped column: Symbol")
        else:
            positives.append("Required mapped ticker column exists: Symbol -> ticker")

        if len(rows) < args.limit:
            warnings.append(f"Requested limit {args.limit} exceeds source rows {len(rows)}; using all available rows.")

    written_rows = 0
    output_size_bytes = None
    normalized_rows: list[dict[str, object]] = []

    if not blockers:
        output_dir.mkdir(parents=True, exist_ok=True)

        selected_rows = rows[: min(args.limit, len(rows))]
        normalized_rows = [normalize_row(row, index + 1) for index, row in enumerate(selected_rows)]

        fieldnames = [
            "dry_run_rank",
            "ticker",
            "company_name",
            "exchange",
            "country",
            "sector",
            "industry",
            "market_cap",
            "source",
            "instrument_type",
            "instrument_scope",
            "classification_confidence",
            "classification_reason",
            "dry_run_status",
            "scoring_performed",
            "openai_called",
            "broker_called",
            "financial_advice",
        ]

        write_csv(batch_csv, fieldnames, normalized_rows)
        written_rows = len(normalized_rows)
        output_size_bytes = batch_csv.stat().st_size

        positives.append(f"Small batch CSV written with {written_rows} rows.")

    elapsed_seconds = round(time.perf_counter() - started, 4)

    if blockers:
        dry_run_status = "SMALL_BATCH_DRY_RUN_BLOCKED"
        readiness_score = 0
    elif warnings:
        dry_run_status = "SMALL_BATCH_DRY_RUN_COMPLETED_WITH_WARNINGS"
        readiness_score = 85
    else:
        dry_run_status = "SMALL_BATCH_DRY_RUN_COMPLETED"
        readiness_score = 100

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "dry_run_status": dry_run_status,
        "readiness_score": readiness_score,
        "elapsed_seconds": elapsed_seconds,
        "source": {
            "path": rel(source),
            "rows": len(rows),
            "columns": len(columns),
            "validation_status": validation_status,
            "validation_scope": validation_scope,
        },
        "batch": {
            "requested_limit": args.limit,
            "written_rows": written_rows,
            "output_dir": rel(output_dir),
            "batch_csv": rel(batch_csv),
            "output_size_bytes": output_size_bytes,
        },
        "dry_run_actions": {
            "source_validation_used": validation_exists,
            "batch_csv_written": written_rows > 0,
            "batch_execution_performed": True if written_rows > 0 else False,
            "scoring_performed": False,
            "openai_called": False,
            "broker_called": False,
            "active_outputs_overwritten": False,
            "full_59000_universe_launched": False,
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
        },
        "recommendation": (
            "Proceed to v2.2E full dry-run gate. Do not execute full 59k."
            if not blockers
            else "Resolve blockers before any further dry-run step."
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.2D Small Batch Dry Run")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Dry-run status: **{dry_run_status}**")
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
    md.append("## Source")
    md.append("")
    for key, value in payload["source"].items():
        md.append(f"- {key}: {value}")
    md.append("")
    md.append("## Batch")
    md.append("")
    for key, value in payload["batch"].items():
        md.append(f"- {key}: {value}")
    md.append("")
    md.append("## Dry-run actions")
    md.append("")
    for key, value in payload["dry_run_actions"].items():
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
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.2D writes only an isolated source-normalized batch CSV. It does not run scoring, OpenAI, broker calls, or full 59k.")

    report_md.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.2D Small Batch Dry Run")
    print("=" * 92)
    print(f"OK   Dry-run status: {dry_run_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Source rows: {len(rows)}")
    print(f"OK   Written rows: {written_rows}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Batch CSV: {batch_csv}")
    print(f"OK   JSON written: {report_json}")
    print(f"OK   Report written: {report_md}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
