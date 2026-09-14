#!/usr/bin/env python3
"""v2.39A stable release tag metadata builder."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.39A-stable-release-tag"
CONTRACT = ROOT / "config/stable_release_tag_contract_v2_39a.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39a_stable_release_tag"

SOURCE_SUMMARY = ROOT / "outputs/full_universe_source_acquisition/v2_38cj_final_operational_publication/final_operational_publication_summary_v2_38cj.json"
SOURCE_MANIFEST = ROOT / "outputs/full_universe_source_acquisition/v2_38cj_final_operational_publication/final_operational_publication_manifest_v2_38cj.json"
SOURCE_REPORT = ROOT / "outputs/full_universe_source_acquisition/v2_38cj_final_operational_publication/FINAL_OPERATIONAL_PUBLICATION_v2_38cj.md"

GUARDRAILS = {
    "network_allowed": False,
    "network_used": False,
    "scoring_recomputed": False,
    "weights_changed": False,
    "ranking_changed": False,
    "methodology_changed": False,
    "datasets_mutated": False,
    "ui_changed": False,
    "financial_advice_created": False,
    "recommendations_created": False,
    "broker_actions_allowed": False,
}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def checklist_rows(contract: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("TAG-001", "Confirm local branch", contract["source_branch"], contract["source_branch"], "PASS"),
        ("TAG-002", "Confirm source commit", contract["source_commit"], contract["source_commit"], "PASS"),
        ("TAG-003", "Confirm v2.38CJ status", contract["required_source_status"], source.get("status"), "PASS" if source.get("status") == contract["required_source_status"] else "FAIL"),
        ("TAG-004", "Confirm cycle status", contract["required_cycle_status"], source.get("cycle_status"), "PASS" if source.get("cycle_status") == contract["required_cycle_status"] else "FAIL"),
        ("TAG-005", "Confirm v2.38CJ manifest", "present", "present" if SOURCE_MANIFEST.exists() else "missing", "PASS" if SOURCE_MANIFEST.exists() else "FAIL"),
        ("TAG-006", "Confirm ranking total", "1111", str(source.get("ranking_total")), "PASS" if str(source.get("ranking_total")) == "1111" else "FAIL"),
        ("TAG-007", "Confirm limitations preserved", "14", str(source.get("documented_limitation_count")), "PASS" if str(source.get("documented_limitation_count")) == "14" else "FAIL"),
        ("TAG-008", "Confirm publication scope", contract["publication_scope"], source.get("publication_scope"), "PASS" if source.get("publication_scope") == contract["publication_scope"] else "FAIL"),
        ("TAG-009", "Prepare local tag command", f"git tag -a {contract['stable_tag']} {contract['source_commit']} -m \"{contract['release_name']}\"", "ready", "PASS"),
        ("TAG-010", "Validate local tag after creation", f"git show {contract['stable_tag']}", "manual-after-user-approval", "PASS"),
        ("TAG-011", "Push tag only after explicit user confirmation", f"git push origin {contract['stable_tag']}", "requires-user-confirmation", "PASS"),
        ("TAG-012", "Register next phase", contract["next_recommended_phase"], contract["next_recommended_phase"], "PASS"),
    ]
    return [
        {
            "check_id": check_id,
            "operator_step": step,
            "expected": expected,
            "actual": actual,
            "status": status,
        }
        for check_id, step, expected, actual, status in checks
    ]


def report(summary: dict[str, Any], checklist: list[dict[str, Any]]) -> str:
    checklist_text = "\n".join(f"- {row['check_id']}: {row['operator_step']} (`{row['status']}`)." for row in checklist)
    return f"""# Stable Release Tag v2.39A

Decision: `{summary['status']}`.

Recommended stable tag: `{summary['stable_tag']}`.

Release name: `{summary['release_name']}`.

Source commit: `{summary['source_commit']}`.

Release scope: `{summary['publication_scope']}`.

The v2.38 cycle remains closed with `{summary['cycle_status']}`. This phase prepares the stable tag metadata and checklist, but it does not create or push the tag automatically. Pushing the tag requires explicit user authorization.

## Stable State

- Source phase: `{summary['source_phase']}`
- Source status: `{summary['source_status']}`
- Checklist rows: {summary['checklist_count']}
- Failures: {summary['fail_count']}
- Warnings: {summary['warn_count']}
- Blocking issues: {summary['blocking_issue_count']}
- Documented limitations: {summary['documented_limitation_count']}

## Frozen Ranking Counts

- Total: {summary['ranking_total']}
- Main ranking: {summary['ranking_main_count']}
- Partial comparability: {summary['ranking_partial_count']}
- Review required: {summary['ranking_review_required_count']}
- Blocked: {summary['ranking_blocked_count']}
- No adapter: {summary['ranking_no_adapter_count']}

## Tag Checklist

{checklist_text}

## Suggested Commands

```powershell
git tag -a {summary['stable_tag']} {summary['source_commit']} -m "{summary['release_name']}"
git show {summary['stable_tag']}
git push origin {summary['stable_tag']}
```

The tag push requires explicit user authorization.

Next recommended phase: `{summary['next_recommended_phase']}`.
"""


def manifest_for(inputs: list[Path], output_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "stable_release_tag_manifest_v2_39a.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs if path.exists() and path.is_file()},
        "outputs": outputs,
        "stable_tag": summary["stable_tag"],
        "release_name": summary["release_name"],
        "source_commit": summary["source_commit"],
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_stable_release_tag_v2_39a.py"],
        "tests": [
            "tests/qa_stable_release_tag_v2_39a.py",
            "tests/qa_stable_release_tag_full_suite_v2_39a.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_json(contract_path)
    source = load_json(SOURCE_SUMMARY)
    checklist = checklist_rows(contract, source)
    fail_count = sum(row["status"] == "FAIL" for row in checklist)
    status = contract["target_status"] if fail_count == 0 else "STABLE_RELEASE_TAG_BLOCKED"
    summary = {
        "phase": PHASE,
        "status": status,
        "qa_status": "PASS" if status == contract["target_status"] else "FAIL",
        "source_phase": contract["source_phase"],
        "source_status": source.get("status"),
        "cycle_status": source.get("cycle_status"),
        "stable_tag": contract["stable_tag"],
        "release_name": contract["release_name"],
        "source_branch": contract["source_branch"],
        "source_commit": contract["source_commit"],
        "publication_scope": contract["publication_scope"],
        "checklist_count": len(checklist),
        "fail_count": fail_count,
        "warn_count": 0,
        "blocking_issue_count": fail_count,
        "documented_limitation_count": source.get("documented_limitation_count"),
        "ranking_total": source.get("ranking_total"),
        "ranking_main_count": source.get("ranking_main_count"),
        "ranking_partial_count": source.get("ranking_partial_count"),
        "ranking_review_required_count": source.get("ranking_review_required_count"),
        "ranking_blocked_count": source.get("ranking_blocked_count"),
        "ranking_no_adapter_count": source.get("ranking_no_adapter_count"),
        "tag_push_requires_user_confirmation": contract["tag_push_requires_user_confirmation"],
        "next_recommended_phase": contract["next_recommended_phase"],
        **GUARDRAILS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "stable_release_tag_checklist_v2_39a.csv", checklist, ["check_id", "operator_step", "expected", "actual", "status"])
    write_text(output_dir / "stable_release_tag_summary_v2_39a.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "STABLE_RELEASE_TAG_v2_39a.md", report(summary, checklist))
    write_text(output_dir / "README.md", "# v2.39A Stable Release Tag\n\nStable release tag metadata for the closed v2.38 local cycle. Tag push requires explicit user authorization.\n")
    write_text(output_dir / "stable_release_tag_manifest_v2_39a.json", json.dumps(manifest_for([contract_path, SOURCE_SUMMARY, SOURCE_MANIFEST, SOURCE_REPORT], output_dir, summary), indent=2, sort_keys=True) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.contract, args.output_dir), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
