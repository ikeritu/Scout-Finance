from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.1B"
METHOD = "generate_controlled_scale_outputs_from_size_100_v1"

SOURCE_SIZE = 100
TARGET_SIZES = [250, 500, 1000]

SCALE_ROOT = ROOT / "outputs" / "scale_tests"
SOURCE_DIR = SCALE_ROOT / f"size_{SOURCE_SIZE}"

OUT_DIR = ROOT / "outputs" / "large_universe_mode"
OUT_JSON = OUT_DIR / "generate_controlled_scale_outputs_v2_1b.json"
OUT_MD = OUT_DIR / "generate_controlled_scale_outputs_v2_1b.md"
OUT_CSV = OUT_DIR / "generate_controlled_scale_outputs_files_v2_1b.csv"

EXPECTED_FILES = [
    "active_real_universe_top_candidates.csv",
    "local_score_v0_breakdown.csv",
    "local_score_v0_candidates.csv",
    "ranking_explainability_candidates.csv",
    "ranking_explainability_factors.csv",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def expand_rows(rows: list[dict[str, str]], target_size: int) -> list[dict[str, str]]:
    if not rows:
        return []

    expanded: list[dict[str, str]] = []
    index = 0

    while len(expanded) < target_size:
        base = dict(rows[index % len(rows)])

        if "ticker" in base:
            base["ticker"] = f"{base['ticker']}_S{len(expanded) + 1:04d}"

        expanded.append(base)
        index += 1

    return expanded


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    generated: list[dict[str, object]] = []

    if not SOURCE_DIR.exists():
        blockers.append(f"Missing source directory: {rel(SOURCE_DIR)}")

    for file_name in EXPECTED_FILES:
        source = SOURCE_DIR / file_name
        if not source.exists():
            blockers.append(f"Missing source file: {rel(source)}")

    if not blockers:
        for size in TARGET_SIZES:
            target_dir = SCALE_ROOT / f"size_{size}"
            target_dir.mkdir(parents=True, exist_ok=True)

            for file_name in EXPECTED_FILES:
                source = SOURCE_DIR / file_name
                target = target_dir / file_name

                fieldnames, rows = read_csv(source)

                if "ticker" not in fieldnames:
                    blockers.append(f"{rel(source)} missing ticker column")
                    continue

                expanded = expand_rows(rows, size)
                write_csv(target, fieldnames, expanded)

                generated.append(
                    {
                        "size": size,
                        "file_name": file_name,
                        "source_path": rel(source),
                        "target_path": rel(target),
                        "source_rows": len(rows),
                        "target_rows": size,
                        "written_rows": len(expanded),
                        "size_bytes": target.stat().st_size,
                        "status": "OK",
                    }
                )

        warnings.append(
            "Generated files are controlled structural scale outputs from size_100, not fresh real-universe data."
        )

    if blockers:
        generation_status = "CONTROLLED_SCALE_GENERATION_BLOCKED"
        readiness_score = 0
    else:
        generation_status = "CONTROLLED_SCALE_GENERATED_WITH_WARNINGS"
        readiness_score = 90

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "generation_status": generation_status,
        "readiness_score": readiness_score,
        "source_size": SOURCE_SIZE,
        "target_sizes": TARGET_SIZES,
        "blockers": blockers,
        "warnings": warnings,
        "generated_files": generated,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
        },
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = [
            "size",
            "file_name",
            "status",
            "source_path",
            "target_path",
            "source_rows",
            "target_rows",
            "written_rows",
            "size_bytes",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(generated)

    md: list[str] = []
    md.append("# Scout Finance ? v2.1B Generate Controlled Scale Outputs")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Generation status: **{generation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Source size: {SOURCE_SIZE}")
    md.append(f"- Target sizes: {', '.join(str(s) for s in TARGET_SIZES)}")
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
    md.append("## Generated files")
    md.append("")
    if generated:
        for item in generated:
            md.append(
                f"- size_{item['size']}/`{item['file_name']}` ? "
                f"{item['status']} ? rows: {item['written_rows']} ? bytes: {item['size_bytes']}"
            )
    else:
        md.append("- No files generated.")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    if blockers:
        md.append("Fix blockers before re-running the v2.1A readiness gate.")
    else:
        md.append("Re-run v2.1A readiness gate to verify the generated 250 / 500 / 1000 outputs.")
        md.append("Treat this as a structural/performance scale test, not as fresh real-universe research.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.1B Generate Controlled Scale Outputs")
    print("=" * 92)
    print(f"OK   Generation status: {generation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Generated files: {len(generated)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   CSV written: {OUT_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
