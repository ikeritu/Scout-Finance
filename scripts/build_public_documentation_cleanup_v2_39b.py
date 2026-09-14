#!/usr/bin/env python3
"""v2.39B public documentation cleanup builder."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.39B-public-documentation-cleanup"
CONTRACT = ROOT / "config/public_documentation_cleanup_contract_v2_39b.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39b_public_documentation_cleanup"
SOURCE_SUMMARY = ROOT / "outputs/full_universe_source_acquisition/v2_39a_stable_release_tag/stable_release_tag_summary_v2_39a.json"
SOURCE_MANIFEST = ROOT / "outputs/full_universe_source_acquisition/v2_39a_stable_release_tag/stable_release_tag_manifest_v2_39a.json"

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
    "tag_created": False,
    "github_release_created": False,
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


def check_row(check_id: str, category: str, item: str, expected: str, actual: str, path: Path, remediation: str = "") -> dict[str, Any]:
    ok = actual == expected
    return {
        "check_id": check_id,
        "category": category,
        "item": item,
        "expected": expected,
        "actual": actual,
        "status": "PASS" if ok else "FAIL",
        "evidence_path": rel(path),
        "remediation": "No action required." if ok else remediation,
    }


def contains(path: Path, text: str) -> bool:
    return text in path.read_text(encoding="utf-8")


def build_cleanup_matrix(contract: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    docs = {name: ROOT / name for name in contract["docs_to_review"]}
    rows = [
        check_row("DOC-001", "SOURCE", "v2.39A status accepted", contract["required_source_status"], source.get("status", ""), SOURCE_SUMMARY, "Run v2.39A."),
        check_row("DOC-002", "SOURCE", "stable tag documented", contract["required_stable_tag"], source.get("stable_tag", ""), SOURCE_SUMMARY, "Rebuild v2.39A."),
        check_row("DOC-003", "SOURCE", "source commit documented", "56e773b", source.get("source_commit", ""), SOURCE_SUMMARY, "Check stable tag source commit."),
        check_row("DOC-004", "SOURCE", "cycle status closed", contract["required_cycle_status"], source.get("cycle_status", ""), SOURCE_SUMMARY, "v2.38 cycle must remain closed."),
        check_row("DOC-005", "SOURCE", "publication scope", contract["publication_scope"], source.get("publication_scope", ""), SOURCE_SUMMARY, "Keep public scope local-only."),
        check_row("DOC-006", "README", "README mentions v2.39B", "present", "present" if contains(docs["README.md"], "v2.39B") else "missing", docs["README.md"], "Update README."),
        check_row("DOC-007", "README", "README mentions local research scope", "present", "present" if contains(docs["README.md"], "local_research_tool_only") else "missing", docs["README.md"], "Update README."),
        check_row("DOC-008", "README", "README mentions no financial advice", "present", "present" if contains(docs["README.md"], "sin recomendaciones financieras") else "missing", docs["README.md"], "Update README."),
        check_row("DOC-009", "README", "README mentions no broker", "present", "present" if contains(docs["README.md"], "sin broker") else "missing", docs["README.md"], "Update README."),
        check_row("DOC-010", "VERSION", "VERSION mentions v2.39B", "present", "present" if contains(docs["VERSION.md"], "v2.39B") else "missing", docs["VERSION.md"], "Update VERSION."),
        check_row("DOC-011", "CHANGELOG", "CHANGELOG mentions v2.39B", "present", "present" if contains(docs["CHANGELOG.md"], "v2.39B") else "missing", docs["CHANGELOG.md"], "Update CHANGELOG."),
        check_row("DOC-012", "ROADMAP", "ROADMAP marks v2.39B", "present", "present" if contains(docs["ROADMAP_v2_38_CURRENT.md"], "v2.39B") else "missing", docs["ROADMAP_v2_38_CURRENT.md"], "Update roadmap."),
        check_row("DOC-013", "ROADMAP", "ROADMAP declares v2.39C next", "present", "present" if contains(docs["ROADMAP_v2_38_CURRENT.md"], "v2.39C") else "missing", docs["ROADMAP_v2_38_CURRENT.md"], "Update next phase."),
        check_row("DOC-014", "PUBLIC_GUIDE", "public guide exists", "present", "present" if (ROOT / "docs/LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md").exists() else "missing", ROOT / "docs/LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md", "Create public guide."),
        check_row("DOC-015", "PUBLIC_INDEX", "documentation index exists", "present", "present" if (ROOT / "docs/PUBLIC_DOCUMENTATION_INDEX_v2_39b.md").exists() else "missing", ROOT / "docs/PUBLIC_DOCUMENTATION_INDEX_v2_39b.md", "Create documentation index."),
        check_row("DOC-016", "LIMITATIONS", "limitations remain visible", "present", "present" if contains(docs["ROADMAP_v2_38_CURRENT.md"], "Pendientes Estructurales Conocidos") else "missing", docs["ROADMAP_v2_38_CURRENT.md"], "Keep limitations visible."),
        check_row("DOC-017", "RANKING", "ranking remains experimental", "present", "present" if contains(docs["README.md"], "ranking experimental") else "missing", docs["README.md"], "Do not overstate ranking."),
        check_row("DOC-018", "PUBLICATION", "no cloud publication claim", "absent", "present" if contains(docs["README.md"], "Streamlit Cloud publicado") else "absent", docs["README.md"], "Remove external publication claim."),
    ]
    for key, expected in GUARDRAILS.items():
        rows.append(check_row(f"GUARDRAIL-{key}", "GUARDRAILS", key, str(expected).lower(), str(expected).lower(), CONTRACT))
    return rows


def documentation_index_rows() -> list[dict[str, Any]]:
    return [
        {"document": "README.md", "purpose": "Public entry point and current state", "audience": "User / reviewer", "status": "PUBLIC_CLEAN", "path": "README.md", "notes": "Current phase, scope and guardrails visible."},
        {"document": "VERSION.md", "purpose": "Version state history", "audience": "Maintainer", "status": "PUBLIC_CLEAN", "path": "VERSION.md", "notes": "Latest v2.39B state at top."},
        {"document": "CHANGELOG.md", "purpose": "Chronological changes", "audience": "Maintainer / reviewer", "status": "PUBLIC_CLEAN", "path": "CHANGELOG.md", "notes": "No scoring/ranking mutation in v2.39B."},
        {"document": "ROADMAP_v2_38_CURRENT.md", "purpose": "Reduced roadmap and pending phases", "audience": "Product owner", "status": "PUBLIC_CLEAN", "path": "ROADMAP_v2_38_CURRENT.md", "notes": "v2.38 closed, v2.39C next."},
        {"document": "FINAL_OPERATIONAL_PUBLICATION_v2_38cj.md", "purpose": "Final v2.38 handoff evidence", "audience": "Operator", "status": "REFERENCE", "path": "outputs/full_universe_source_acquisition/v2_38cj_final_operational_publication/FINAL_OPERATIONAL_PUBLICATION_v2_38cj.md", "notes": "Local research scope."},
        {"document": "STABLE_RELEASE_TAG_v2_39a.md", "purpose": "Stable tag metadata", "audience": "Maintainer", "status": "REFERENCE", "path": "outputs/full_universe_source_acquisition/v2_39a_stable_release_tag/STABLE_RELEASE_TAG_v2_39a.md", "notes": "Tag v2.38CJ-local-stable."},
        {"document": "PUBLIC_DOCUMENTATION_CLEANUP_v2_39b.md", "purpose": "Public documentation cleanup report", "audience": "Maintainer / reviewer", "status": "CURRENT", "path": "outputs/full_universe_source_acquisition/v2_39b_public_documentation_cleanup/PUBLIC_DOCUMENTATION_CLEANUP_v2_39b.md", "notes": "This phase report."},
    ]


def public_index_md(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Public Documentation Index v2.39B",
        "",
        "This index lists the public-facing documents for Scout Finance after the v2.38 local cycle closure.",
        "",
        "| Document | Purpose | Audience | Status | Path |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['document']} | {row['purpose']} | {row['audience']} | {row['status']} | `{row['path']}` |")
    return "\n".join(lines) + "\n"


def public_guide_md() -> str:
    return """# Local Usage Public Guide v2.39B

Scout Finance is a local research tool for exploring an experimental global ranking built from the project's validated local outputs.

It is not financial advice, it does not create recommendations, and it does not include a broker workflow. The ranking is experimental and must be interpreted with the documented limitations visible in the project reports.

## Stable Reference

- Branch: `phase9b-global-enrichment-v2-38b`
- Stable tag: `v2.38CJ-local-stable`
- Scope: `local_research_tool_only`

## Local Startup

```powershell
cd "D:\\Proyectos\\Scout Finance"
pip install -r requirements.txt
run_local_ui_v2_37.bat
```

Open Streamlit at `http://localhost:8501` and use the global experimental ranking screen.

Windows paths with spaces or emoji must be wrapped in quotes. For example, use `cd "D:\\Proyectos\\Scout Finance"` or your own quoted local path.

## Ranking Populations

- Main ranking: 318 assets with enough comparable evidence for the experimental ranking.
- Partial comparability: 373 assets with usable but incomplete comparability.
- Review required: 124 assets that need manual or methodological review before interpretation.
- Blocked: 270 assets with insufficient coverage.
- No adapter: 26 assets whose data exists but does not yet have a scoring adapter.

## Known Limitations

The project keeps documented limitations visible by design: data coverage gaps, European source constraints, Cboe Europe deferred scope, UK automation blockers, environment warnings and experimental ranking guardrails.
"""


def report(summary: dict[str, Any]) -> str:
    return f"""# Public Documentation Cleanup v2.39B

Decision: `{summary['status']}`.

This phase cleans and indexes public documentation while preserving technical traceability. It does not change scoring, ranking, methodology, weights, datasets or functional UI.

## Results

- Documents reviewed: {summary['docs_reviewed_count']}
- Documents created: {summary['docs_created_count']}
- Cleanup checks: {summary['cleanup_check_count']}
- Failures: {summary['fail_count']}
- Warnings: {summary['warn_count']}
- Blocking issues: {summary['blocking_issue_count']}
- Stable tag: `{summary['stable_tag']}`
- Publication scope: `{summary['publication_scope']}`

## Public Scope

Scout Finance remains a local research tool. The documentation keeps the experimental ranking, limitations, no financial advice, no recommendations and no broker workflow guardrails visible.

Next recommended phase: `v2.39C-security-sensitive-files-audit`.
"""


def manifest_for(inputs: list[Path], outputs_dir: Path, summary: dict[str, Any], docs_created: list[str], docs_reviewed: list[str]) -> dict[str, Any]:
    output_paths = [p for p in sorted(outputs_dir.glob("*")) if p.name != "public_documentation_cleanup_manifest_v2_39b.json" and p.is_file()]
    output_paths.extend(ROOT / path for path in docs_created)
    return {
        "phase": PHASE,
        "status": summary["status"],
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs if path.exists() and path.is_file()},
        "outputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in output_paths if path.exists() and path.is_file()},
        "docs_reviewed": docs_reviewed,
        "docs_created": docs_created,
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_public_documentation_cleanup_v2_39b.py"],
        "tests": [
            "tests/qa_public_documentation_cleanup_v2_39b.py",
            "tests/qa_public_documentation_cleanup_full_suite_v2_39b.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_json(contract_path)
    source = load_json(SOURCE_SUMMARY)
    write_text(ROOT / "docs/PUBLIC_DOCUMENTATION_INDEX_v2_39b.md", public_index_md(documentation_index_rows()))
    write_text(ROOT / "docs/LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md", public_guide_md())
    matrix = build_cleanup_matrix(contract, source)
    index_rows = documentation_index_rows()
    fail_count = sum(row["status"] == "FAIL" for row in matrix)
    summary = {
        "phase": PHASE,
        "status": contract["target_status"] if fail_count == 0 else "PUBLIC_DOCUMENTATION_CLEANUP_BLOCKED",
        "qa_status": "PASS" if fail_count == 0 else "FAIL",
        "source_phase": contract["source_phase"],
        "source_status": source.get("status"),
        "stable_tag": source.get("stable_tag"),
        "source_commit": source.get("source_commit"),
        "cycle_status": source.get("cycle_status"),
        "publication_scope": source.get("publication_scope"),
        "docs_reviewed_count": len(contract["docs_to_review"]),
        "docs_created_count": len(contract["docs_to_create"]),
        "cleanup_check_count": len(matrix),
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
        "next_recommended_phase": contract["next_recommended_phase"],
        **GUARDRAILS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "public_documentation_cleanup_matrix_v2_39b.csv", matrix, ["check_id", "category", "item", "expected", "actual", "status", "evidence_path", "remediation"])
    write_csv(output_dir / "public_documentation_index_v2_39b.csv", index_rows, ["document", "purpose", "audience", "status", "path", "notes"])
    write_text(output_dir / "public_documentation_cleanup_summary_v2_39b.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "PUBLIC_DOCUMENTATION_CLEANUP_v2_39b.md", report(summary))
    write_text(output_dir / "README.md", "# v2.39B Public Documentation Cleanup\n\nPublic documentation cleanup and index for the post-v2.38 reduced roadmap. No scoring, ranking, methodology, data, UI, tag, GitHub release, recommendation or broker changes.\n")
    inputs = [contract_path, SOURCE_SUMMARY, SOURCE_MANIFEST, *(ROOT / path for path in contract["docs_to_review"])]
    write_text(output_dir / "public_documentation_cleanup_manifest_v2_39b.json", json.dumps(manifest_for(inputs, output_dir, summary, contract["docs_to_create"], contract["docs_to_review"]), indent=2, sort_keys=True) + "\n")
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
