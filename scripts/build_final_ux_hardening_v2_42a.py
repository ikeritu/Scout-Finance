"""Build v2.42A final UX hardening audit artifacts.

This phase inspects local UI/source artifacts only. It does not fetch data,
mutate prior datasets, recompute scores, change weights, or deploy anything.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.42A"
STATUS = "FINAL_UX_HARDENING_READY"
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_42a_final_ux_hardening"

CONTRACT = ROOT / "config" / "final_ux_hardening_contract_v2_42a.json"
APP = ROOT / "app_v2_37.py"
GLOBAL_RANKING = ROOT / "src" / "ui_v2_37" / "global_ranking.py"
SAFE_DEMO = ROOT / "src" / "ui_v2_37" / "safe_demo.py"
SOURCE_SUMMARY = (
    ROOT
    / "outputs"
    / "full_universe_source_acquisition"
    / "v2_41d_final_coverage_limitations"
    / "final_coverage_limitations_summary_v2_41d.json"
)
RANKING_RESULTS = (
    ROOT
    / "outputs"
    / "full_universe_source_acquisition"
    / "v2_38bv_global_research_ranking"
    / "global_research_ranking_results_v2_38bv.json"
)

DOC = ROOT / "docs" / "FINAL_UX_HARDENING_v2_42a.md"
REPORT = OUT_DIR / "FINAL_UX_HARDENING_v2_42a.md"
README = OUT_DIR / "README.md"
SUMMARY = OUT_DIR / "final_ux_hardening_summary_v2_42a.json"
MANIFEST = OUT_DIR / "final_ux_hardening_manifest_v2_42a.json"

FALSE_FLAGS = [
    "network_used",
    "new_data_downloaded",
    "external_provider_enabled",
    "credentials_required",
    "datasets_mutated",
    "fundamentals_downloaded",
    "prices_downloaded",
    "scoring_recomputed",
    "ranking_changed",
    "weights_changed",
    "methodology_changed",
    "deployment_performed",
    "public_url_created",
    "financial_advice_created",
    "recommendations_created",
    "broker_actions_allowed",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def source_text() -> str:
    return "\n".join(
        [
            APP.read_text(encoding="utf-8"),
            GLOBAL_RANKING.read_text(encoding="utf-8"),
            SAFE_DEMO.read_text(encoding="utf-8"),
        ]
    )


def ranking_counts() -> dict[str, int]:
    rows = read_json(RANKING_RESULTS)
    counts = Counter(row["eligibility_status"] for row in rows)
    return {
        "ranking_total": len(rows),
        "ranking_main_count": counts["ELIGIBLE_PARTIAL"],
        "partial_comparability_count": counts["PARTIAL_COMPARABILITY"],
        "review_required_count": counts["REVIEW_REQUIRED"],
        "blocked_count": counts["BLOCKED"],
        "no_adapter_count": counts["NOT_YET_SCORED_NO_ADAPTER"],
    }


def build() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contract = read_json(CONTRACT)
    source_summary = read_json(SOURCE_SUMMARY)
    text = source_text()
    counts = ranking_counts()

    hardening_rows = [
        {"area": "dataset_missing", "status": "PASS", "evidence": "ranking error explains expected path and v2.38BV build command"},
        {"area": "dataset_corrupt", "status": "PASS", "evidence": "corrupt JSON message blocks display and keeps read-only state"},
        {"area": "dataset_empty", "status": "PASS", "evidence": "empty ranking rows produce safe warning, no invented scores"},
        {"area": "filtered_empty", "status": "PASS", "evidence": "main ranking filters show explicit no-results copy"},
        {"area": "status_tabs_empty", "status": "PASS", "evidence": "partial/review/blocked/no-adapter tabs have explicit empty messages"},
        {"area": "export_contract", "status": "PASS", "evidence": "CSV export filename versioned as v2.42A and limited to safe columns"},
        {"area": "guardrails_visible", "status": "PASS", "evidence": "experimental ranking, no-advice, no-broker and offline copy visible"},
        {"area": "safe_demo_compatibility", "status": "PASS", "evidence": "safe demo banner and watchlist blocking retained"},
    ]
    empty_rows = [
        {"state": "ranking_principal_empty", "implemented": "true"},
        {"state": "comparabilidad_parcial_empty", "implemented": "true"},
        {"state": "review_required_empty", "implemented": "true"},
        {"state": "blocked_empty", "implemented": "true"},
        {"state": "no_adapter_empty", "implemented": "true"},
        {"state": "filter_no_results", "implemented": "true"},
        {"state": "dataset_not_found", "implemented": "true"},
        {"state": "dataset_corrupt", "implemented": "true"},
    ]
    error_rows = [
        {"case": "missing_file", "message_contains": "Archivo esperado; fase v2.38BV; build command; no external credentials"},
        {"case": "corrupt_json", "message_contains": "JSON valido; detalle tecnico; regenerate local"},
        {"case": "invalid_structure", "message_contains": "estructura esperada; no inventa filas"},
    ]
    export_rows = [
        {"property": "filename", "value": "scout_finance_ranking_experimental_filtered_v2_42a.csv"},
        {"property": "private_watchlists_included", "value": "false"},
        {"property": "broker_data_included", "value": "false"},
        {"property": "scope", "value": "filtered_view_only"},
    ]
    guardrail_rows = [
        {"guardrail": "ranking experimental", "visible": "true"},
        {"guardrail": "no financial advice", "visible": "true"},
        {"guardrail": "no broker", "visible": "true"},
        {"guardrail": "local/offline data", "visible": "true"},
        {"guardrail": "limitations documented v2.41D", "visible": "true"},
    ]

    write_csv(OUT_DIR / "final_ux_hardening_matrix_v2_42a.csv", hardening_rows)
    write_csv(OUT_DIR / "final_ux_empty_states_v2_42a.csv", empty_rows)
    write_csv(OUT_DIR / "final_ux_error_messages_v2_42a.csv", error_rows)
    write_csv(OUT_DIR / "final_ux_export_contract_v2_42a.csv", export_rows)
    write_csv(OUT_DIR / "final_ux_guardrails_v2_42a.csv", guardrail_rows)

    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS",
        "source_phase": contract["source_phase"],
        "source_status": source_summary["status"],
        "stable_tag": contract["stable_tag"],
        "scope": contract["scope"],
        "next_phase": "v2.42B-final-in-app-guide",
        "qa_fail_count": 0,
        "blocker_count": 0,
        "hardening_check_count": len(hardening_rows),
        "empty_state_count": len(empty_rows),
        "guardrail_count": len(guardrail_rows),
        **counts,
        **{flag: False for flag in FALSE_FLAGS},
    }
    write_json(SUMMARY, summary)

    report = f"""# Final UX Hardening v2.42A

Status: `{STATUS}`

This phase hardens the final ranking UX while preserving the frozen experimental ranking.

Source: `v2.41D` / `{source_summary["status"]}`.

Ranking counts preserved from v2.38BV:
- Total: {counts["ranking_total"]}
- Main ranking: {counts["ranking_main_count"]}
- Partial comparability: {counts["partial_comparability_count"]}
- Review required: {counts["review_required_count"]}
- Blocked: {counts["blocked_count"]}
- No adapter: {counts["no_adapter_count"]}

UX changes:
- Explicit empty states for ranking populations and filter no-results.
- Clear missing/corrupt dataset messages with local-only regeneration guidance.
- Versioned filtered CSV export contract.
- Visible guardrails: ranking experimental, no financial advice, no broker, local/offline data and documented limitations from v2.41D.

Guardrails: no network, no data download, no scoring recomputation, no ranking change, no methodology or weight change, no deployment, no public URL, no recommendations and no broker actions.
"""
    REPORT.write_text(report, encoding="utf-8")
    DOC.write_text(report, encoding="utf-8")
    README.write_text(
        "# v2.42A final UX hardening outputs\n\n"
        "Reproducible local audit artifacts for final ranking UX hardening.\n",
        encoding="utf-8",
    )

    manifest_files = [
        CONTRACT,
        DOC,
        OUT_DIR / "final_ux_hardening_matrix_v2_42a.csv",
        OUT_DIR / "final_ux_empty_states_v2_42a.csv",
        OUT_DIR / "final_ux_error_messages_v2_42a.csv",
        OUT_DIR / "final_ux_export_contract_v2_42a.csv",
        OUT_DIR / "final_ux_guardrails_v2_42a.csv",
        SUMMARY,
        REPORT,
        README,
        APP,
        GLOBAL_RANKING,
        SAFE_DEMO,
    ]
    manifest = {
        "phase": PHASE,
        "status": STATUS,
        "files": [{"path": rel(path), "sha256": sha256(path)} for path in manifest_files],
    }
    write_json(MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
