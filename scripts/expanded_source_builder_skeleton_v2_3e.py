from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.3E"
METHOD = "expanded_source_builder_skeleton_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "expanded_source_builder_skeleton_v2_3e.json"
OUT_MD = OUT_DIR / "expanded_source_builder_skeleton_v2_3e.md"
OUT_CSV = OUT_DIR / "expanded_source_builder_provider_scan_v2_3e.csv"

INVENTORY_JSON = OUT_DIR / "source_provider_inventory_v2_3d.json"

LOCAL_PROVIDER_ROOT = ROOT / "data" / "raw" / "source_providers"
EXPANDED_SOURCE_DIR = ROOT / "data" / "raw" / "expanded_universe"
EXPANDED_SOURCE_PLACEHOLDER = EXPANDED_SOURCE_DIR / "README_v2_3e.md"

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


def expected_local_files(provider: dict) -> list[Path]:
    provider_id = provider["provider_id"]
    return [
        LOCAL_PROVIDER_ROOT / provider_id / f"{provider_id}.csv",
        LOCAL_PROVIDER_ROOT / provider_id / "source.csv",
        LOCAL_PROVIDER_ROOT / f"{provider_id}.csv",
    ]


def profile_csv(path: Path) -> dict:
    profile = {
        "path": rel(path),
        "exists": path.exists(),
        "readable": False,
        "rows": 0,
        "columns": 0,
        "column_names": [],
        "error": None,
    }

    if not path.exists():
        return profile

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            columns = list(reader.fieldnames or [])

        profile["readable"] = True
        profile["rows"] = len(rows)
        profile["columns"] = len(columns)
        profile["column_names"] = columns
    except Exception as exc:
        profile["error"] = str(exc)

    return profile


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_PROVIDER_ROOT.mkdir(parents=True, exist_ok=True)
    EXPANDED_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    inventory = read_json(INVENTORY_JSON)

    if not inventory.get("_exists"):
        blockers.append(f"Missing required v2.3D inventory artifact: {rel(INVENTORY_JSON)}")
        inventory_status = None
        providers = []
    else:
        inventory_status = inventory.get("inventory_status")
        providers = inventory.get("providers", [])
        positives.append(f"v2.3D inventory found and readable: {rel(INVENTORY_JSON)}")

    if inventory_status == "SOURCE_PROVIDER_INVENTORY_READY":
        positives.append("v2.3D confirms source provider inventory is ready.")
    else:
        blockers.append(f"v2.3D inventory is not ready: {inventory_status}")

    if not providers:
        blockers.append("No providers available in v2.3D inventory.")

    provider_scan: list[dict] = []
    found_local_files = 0
    readable_local_files = 0
    total_local_rows = 0

    for provider in providers:
        provider_id = provider["provider_id"]
        provider_dir = LOCAL_PROVIDER_ROOT / provider_id
        provider_dir.mkdir(parents=True, exist_ok=True)

        expected_files = expected_local_files(provider)
        existing_files = [path for path in expected_files if path.exists()]

        selected_file = existing_files[0] if existing_files else None
        csv_profile = profile_csv(selected_file) if selected_file else None

        if selected_file:
            found_local_files += 1

        if csv_profile and csv_profile["readable"]:
            readable_local_files += 1
            total_local_rows += int(csv_profile["rows"])

        provider_scan.append(
            {
                "provider_id": provider_id,
                "provider_name": provider.get("provider_name"),
                "exchange": provider.get("exchange"),
                "country": provider.get("country"),
                "priority": provider.get("priority"),
                "route": provider.get("route"),
                "first_expansion_candidate": provider.get("first_expansion_candidate"),
                "provider_dir": rel(provider_dir),
                "expected_file_1": rel(expected_files[0]),
                "expected_file_2": rel(expected_files[1]),
                "expected_file_3": rel(expected_files[2]),
                "local_file_found": bool(selected_file),
                "selected_file": rel(selected_file) if selected_file else "",
                "readable": bool(csv_profile and csv_profile["readable"]),
                "rows": csv_profile["rows"] if csv_profile else 0,
                "columns": csv_profile["columns"] if csv_profile else 0,
                "error": csv_profile["error"] if csv_profile else "",
            }
        )

    if found_local_files == 0:
        warnings.append("No local provider source files found yet. This is expected for skeleton phase.")
    else:
        positives.append(f"Local provider files found: {found_local_files}")

    if readable_local_files:
        positives.append(f"Readable local provider files: {readable_local_files}")
        positives.append(f"Total local provider rows detected: {total_local_rows}")

    placeholder_md = [
        "# Scout Finance ? Expanded Universe Source Folder",
        "",
        "This folder is prepared by v2.3E.",
        "",
        "Place expanded provider files under:",
        "",
        "`data/raw/source_providers/<provider_id>/<provider_id>.csv`",
        "",
        "Current v2.3E behavior:",
        "",
        "- no network download",
        "- no OpenAI",
        "- no broker",
        "- no scoring",
        "- no full 59k",
        "- no active output overwrite",
        "",
    ]
    EXPANDED_SOURCE_PLACEHOLDER.write_text("\n".join(placeholder_md), encoding="utf-8")

    if blockers:
        builder_status = "EXPANDED_SOURCE_BUILDER_SKELETON_BLOCKED"
        readiness_score = 0
    elif warnings:
        builder_status = "EXPANDED_SOURCE_BUILDER_SKELETON_READY_WITH_WARNINGS"
        readiness_score = 85
    else:
        builder_status = "EXPANDED_SOURCE_BUILDER_SKELETON_READY"
        readiness_score = 100

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "builder_status": builder_status,
        "readiness_score": readiness_score,
        "inventory_input": {
            "path": rel(INVENTORY_JSON),
            "exists": inventory.get("_exists"),
            "inventory_status": inventory_status,
        },
        "targets": {
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
        },
        "paths": {
            "local_provider_root": rel(LOCAL_PROVIDER_ROOT),
            "expanded_source_dir": rel(EXPANDED_SOURCE_DIR),
            "expanded_source_placeholder": rel(EXPANDED_SOURCE_PLACEHOLDER),
        },
        "provider_count": len(providers),
        "found_local_files": found_local_files,
        "readable_local_files": readable_local_files,
        "total_local_rows": total_local_rows,
        "provider_scan": provider_scan,
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
            "Place provider CSV files under data/raw/source_providers/<provider_id>/, then proceed to v2.3F validation."
            if not blockers
            else "Resolve blockers before using expanded source builder skeleton."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_fields = [
        "provider_id",
        "provider_name",
        "exchange",
        "country",
        "priority",
        "route",
        "first_expansion_candidate",
        "provider_dir",
        "expected_file_1",
        "expected_file_2",
        "expected_file_3",
        "local_file_found",
        "selected_file",
        "readable",
        "rows",
        "columns",
        "error",
    ]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(provider_scan)

    md: list[str] = []
    md.append("# Scout Finance ? v2.3E Expanded Source Builder Skeleton")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Builder status: **{builder_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Provider count: {len(providers)}")
    md.append(f"- Local provider files found: {found_local_files}")
    md.append(f"- Readable local provider files: {readable_local_files}")
    md.append(f"- Total local rows detected: {total_local_rows}")
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
    md.append("## Prepared paths")
    md.append("")
    for key, value in payload["paths"].items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Provider scan")
    md.append("")
    for item in provider_scan:
        md.append(f"### {item['provider_id']}")
        md.append("")
        md.append(f"- Provider dir: `{item['provider_dir']}`")
        md.append(f"- Local file found: {item['local_file_found']}")
        md.append(f"- Selected file: `{item['selected_file']}`")
        md.append(f"- Readable: {item['readable']}")
        md.append(f"- Rows: {item['rows']}")
        md.append(f"- Columns: {item['columns']}")
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
    md.append("Important: v2.3E is a builder skeleton only. It does not download data, execute scoring, call OpenAI, call a broker, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.3E Expanded Source Builder Skeleton")
    print("=" * 92)
    print(f"OK   Builder status: {builder_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Provider count: {len(providers)}")
    print(f"OK   Local provider files found: {found_local_files}")
    print(f"OK   Readable local provider files: {readable_local_files}")
    print(f"OK   Total local rows detected: {total_local_rows}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Provider scan CSV written: {OUT_CSV}")
    print(f"OK   Placeholder written: {EXPANDED_SOURCE_PLACEHOLDER}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Network download performed: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
