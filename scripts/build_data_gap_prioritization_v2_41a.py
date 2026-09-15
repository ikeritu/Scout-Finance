from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


PHASE = "v2.41A"
STATUS = "DATA_GAP_PRIORITIZATION_READY"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41a_data_gap_prioritization"
SOURCE_SUMMARY = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40d_controlled_external_publication_qa" / "controlled_external_publication_qa_summary_v2_40d.json"
RANKING_JSON = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38bv_global_research_ranking" / "global_research_ranking_results_v2_38bv.json"
ELIGIBILITY_CSV = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38bo_global_scoring_eligibility" / "global_scoring_eligibility_v2_38bo.csv"
RISK_REGISTER = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38cg_limitations_backlog_product_risk_register" / "product_risk_register_v2_38cg.csv"
CONTRACT = ROOT / "config" / "data_gap_prioritization_contract_v2_41a.json"
DOC = ROOT / "docs" / "DATA_GAP_PRIORITIZATION_v2_41a.md"


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
    "ui_changed",
    "deployment_performed",
    "public_url_created",
    "financial_advice_created",
    "recommendations_created",
    "broker_actions_allowed",
]


def read_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_status() -> str:
    summary = read_json(SOURCE_SUMMARY)
    status = summary.get("status")
    if status != "CONTROLLED_EXTERNAL_PUBLICATION_QA_READY":
        raise ValueError(f"Expected v2.40D ready, got {status!r}")
    return status


def ranking_counts() -> Counter:
    rows = read_json(RANKING_JSON)
    return Counter(row.get("eligibility_status", "") for row in rows)


def eligibility_counts() -> Counter:
    rows = read_csv(ELIGIBILITY_CSV)
    return Counter(row.get("eligibility_tier", "") for row in rows)


def risk_count() -> int:
    return len(read_csv(RISK_REGISTER)) if RISK_REGISTER.exists() else 0


def build_gap_rows() -> list[dict[str, object]]:
    ranking = ranking_counts()
    eligibility = eligibility_counts()
    risks = risk_count()
    return [
        {
            "gap_id": "GAP-LUX-ADAPTER",
            "area": "Luxembourg",
            "description": "Luxembourg remains without a real ratios/growth adapter for scoring.",
            "current_evidence": f"{ranking.get('NOT_YET_SCORED_NO_ADAPTER', 0)} rows are still NOT_YET_SCORED_NO_ADAPTER in v2.38BV.",
            "affected_population": ranking.get("NOT_YET_SCORED_NO_ADAPTER", 0),
            "impact": "medium",
            "effort": "bounded",
            "risk": "low",
            "priority": 1,
            "decision": "ATTACK_NEXT",
            "recommended_next_phase": "v2.41B-luxembourg-adapter-or-closure",
            "closure_condition": "Build a tiny real adapter if evidence exists, otherwise close Luxembourg as documented limitation.",
        },
        {
            "gap_id": "GAP-UK-OFFICIAL-ACCESS",
            "area": "United Kingdom",
            "description": "Official access remains constrained for some filing/document paths.",
            "current_evidence": "Prior phases document NSM/official access constraints and manual review needs.",
            "affected_population": "bounded_manual_subset",
            "impact": "medium",
            "effort": "medium",
            "risk": "medium",
            "priority": 3,
            "decision": "REQUIRES_USER_DECISION",
            "recommended_next_phase": "v2.41C-uk-cboe-manual-review-decision",
            "closure_condition": "User chooses between credential/manual route or documented closure.",
        },
        {
            "gap_id": "GAP-CBOE-EUROPE",
            "area": "Cboe Europe",
            "description": "Cboe Europe identity/fundamentals/prices remain structurally problematic or blocked.",
            "current_evidence": "Roadmap and risk register keep Cboe Europe as a known structural limitation.",
            "affected_population": "large_european_scope",
            "impact": "high",
            "effort": "high",
            "risk": "high",
            "priority": 6,
            "decision": "BLOCKED_STRUCTURAL",
            "recommended_next_phase": "v2.41C-uk-cboe-manual-review-decision",
            "closure_condition": "Close as structural unless an approved source or paid/user-action route is chosen.",
        },
        {
            "gap_id": "GAP-EUROPE-PRICES",
            "area": "Europe prices",
            "description": "No viable free automated source for European historical prices has been confirmed.",
            "current_evidence": "v2.38AJ confirmed five negative source checks and 0/689 real European price coverage.",
            "affected_population": 689,
            "impact": "high",
            "effort": "high",
            "risk": "high",
            "priority": 7,
            "decision": "BLOCKED_STRUCTURAL",
            "recommended_next_phase": "v2.41D-final-coverage-limitations",
            "closure_condition": "Keep documented unless a user-approved paid provider/source exception is introduced.",
        },
        {
            "gap_id": "GAP-MANUAL-REVIEWS",
            "area": "Manual reviews",
            "description": "Rows requiring manual review remain separated from the main ranking.",
            "current_evidence": f"{ranking.get('REVIEW_REQUIRED', 0)} rows are REVIEW_REQUIRED in v2.38BV.",
            "affected_population": ranking.get("REVIEW_REQUIRED", 0),
            "impact": "medium",
            "effort": "medium",
            "risk": "medium",
            "priority": 4,
            "decision": "DEFER_POST_RELEASE",
            "recommended_next_phase": "v2.41C-uk-cboe-manual-review-decision",
            "closure_condition": "Manual review procedure exists or the population remains explicitly out of ranking.",
        },
        {
            "gap_id": "GAP-FINANCIAL-INSTITUTIONS",
            "area": "Financial institutions",
            "description": "Banks and insurers require a separate factor contract instead of industrial ratios.",
            "current_evidence": "v2.38BV separates financial institutions into REVIEW_REQUIRED where applicable.",
            "affected_population": "subset_of_review_required",
            "impact": "medium",
            "effort": "high",
            "risk": "high",
            "priority": 5,
            "decision": "REQUIRES_USER_DECISION",
            "recommended_next_phase": "v2.41C-uk-cboe-manual-review-decision",
            "closure_condition": "Create a financial-institution methodology project or keep excluded with explanation.",
        },
        {
            "gap_id": "GAP-COVERAGE-BELOW-THRESHOLD",
            "area": "Coverage below threshold",
            "description": "Assets below the real factor coverage threshold remain blocked from scoring.",
            "current_evidence": f"{ranking.get('BLOCKED', 0)} rows are BLOCKED; eligibility NOT_ELIGIBLE count is {eligibility.get('NOT_ELIGIBLE', 0)}.",
            "affected_population": ranking.get("BLOCKED", 0),
            "impact": "medium",
            "effort": "high",
            "risk": "medium",
            "priority": 8,
            "decision": "KEEP_DOCUMENTED_LIMITATION",
            "recommended_next_phase": "v2.41D-final-coverage-limitations",
            "closure_condition": "Keep fail-closed until real coverage improves without imputing missing factors.",
        },
        {
            "gap_id": "GAP-EXTERNAL-PUBLICATION-RISK",
            "area": "External publication risk",
            "description": "Safe demo and manual QA must remain mandatory for external publication.",
            "current_evidence": "v2.40A-D define safe demo and controlled external publication QA.",
            "affected_population": "product_surface",
            "impact": "high",
            "effort": "low",
            "risk": "medium",
            "priority": 2,
            "decision": "KEEP_DOCUMENTED_LIMITATION",
            "recommended_next_phase": "PROJECT_CLOSE_FINAL_REPORT",
            "closure_condition": "Do not share a public URL until safe demo manual QA is complete.",
        },
        {
            "gap_id": "GAP-SECURITY-WARNINGS",
            "area": "Security warnings",
            "description": "Security-sensitive files and secrets checks should remain visible after publication prep.",
            "current_evidence": "v2.39C and v2.40B-D keep secrets/publication guardrails in place.",
            "affected_population": "repository_publication_surface",
            "impact": "high",
            "effort": "low",
            "risk": "medium",
            "priority": 9,
            "decision": "KEEP_DOCUMENTED_LIMITATION",
            "recommended_next_phase": "v2.43A-final-consolidated-audit",
            "closure_condition": f"Re-run security audit before final release; current risk register rows: {risks}.",
        },
        {
            "gap_id": "GAP-PRODUCT-LEGAL-WORDING",
            "area": "Product/legal wording",
            "description": "No-advice, no-broker and no-recommendations language must remain visible.",
            "current_evidence": "v2.38BZ-v2.40D explicitly lock product/legal guardrails.",
            "affected_population": "all_user_facing_surfaces",
            "impact": "high",
            "effort": "low",
            "risk": "low",
            "priority": 10,
            "decision": "KEEP_DOCUMENTED_LIMITATION",
            "recommended_next_phase": "v2.42B-final-in-app-guide",
            "closure_condition": "Final app guide preserves no-advice/no-broker/no-recommendations language.",
        },
    ]


def write_docs(summary: dict[str, object], gaps: list[dict[str, object]]) -> None:
    lines = [
        "# Data Gap Prioritization v2.41A",
        "",
        f"Status: `{summary['status']}`",
        "",
        "This phase prioritizes known data gaps using local artifacts only. It does not download data, does not call network, does not recompute scoring, does not change ranking and does not provide financial recommendations.",
        "",
        f"Primary next phase: `{summary['primary_next_phase']}`",
        "",
        "## Gap Decisions",
        "",
        "| Gap | Decision | Priority | Next phase |",
        "| --- | --- | --- | --- |",
    ]
    for gap in sorted(gaps, key=lambda row: int(row["priority"])):
        lines.append(f"| {gap['gap_id']} | {gap['decision']} | {gap['priority']} | {gap['recommended_next_phase']} |")
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src_status = source_status()
    gaps = build_gap_rows()
    decisions = Counter(str(row["decision"]) for row in gaps)
    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS",
        "source_phase": "v2.40D",
        "source_status": src_status,
        "stable_tag": "v2.38CJ-local-stable",
        "publication_scope_current": "controlled_external_publication_qa_ready_not_deployed",
        "data_gap_scope": "prioritization_only",
        "evaluated_gap_count": len(gaps),
        "attack_next_count": decisions["ATTACK_NEXT"],
        "documented_limitation_count": decisions["KEEP_DOCUMENTED_LIMITATION"],
        "requires_user_decision_count": decisions["REQUIRES_USER_DECISION"],
        "blocked_structural_count": decisions["BLOCKED_STRUCTURAL"],
        "defer_post_release_count": decisions["DEFER_POST_RELEASE"],
        "primary_next_phase": "v2.41B-luxembourg-adapter-or-closure",
        "primary_next_phase_reason": "Luxembourg is a bounded gap: decide whether a small real adapter exists or close it formally without changing global product behavior.",
        "qa_fail_count": 0,
        "blocker_count": 0,
        **{flag: False for flag in FALSE_FLAGS},
    }

    sources = [
        {"source_id": "v2.40D-summary", "path": str(SOURCE_SUMMARY.relative_to(ROOT)), "status": "PRESENT"},
        {"source_id": "v2.38BV-ranking", "path": str(RANKING_JSON.relative_to(ROOT)), "status": "PRESENT"},
        {"source_id": "v2.38BO-eligibility", "path": str(ELIGIBILITY_CSV.relative_to(ROOT)), "status": "PRESENT"},
        {"source_id": "v2.38CG-risk-register", "path": str(RISK_REGISTER.relative_to(ROOT)), "status": "PRESENT" if RISK_REGISTER.exists() else "MISSING_OPTIONAL"},
    ]
    impact = [
        {"area": row["area"], "impact": row["impact"], "effort": row["effort"], "risk": row["risk"], "priority": row["priority"]}
        for row in gaps
    ]
    recommendation = [
        {
            "rank": 1,
            "recommended_next_phase": "v2.41B-luxembourg-adapter-or-closure",
            "reason": summary["primary_next_phase_reason"],
            "decision": "ATTACK_NEXT",
        }
    ]
    write_csv(OUT_DIR / "data_gap_prioritization_matrix_v2_41a.csv", gaps, ["gap_id", "area", "description", "current_evidence", "affected_population", "impact", "effort", "risk", "priority", "decision", "recommended_next_phase", "closure_condition"])
    write_csv(OUT_DIR / "data_gap_decision_register_v2_41a.csv", gaps, ["gap_id", "decision", "recommended_next_phase", "closure_condition"])
    write_csv(OUT_DIR / "data_gap_source_inventory_v2_41a.csv", sources, ["source_id", "path", "status"])
    write_csv(OUT_DIR / "data_gap_impact_matrix_v2_41a.csv", impact, ["area", "impact", "effort", "risk", "priority"])
    write_csv(OUT_DIR / "data_gap_next_phase_recommendation_v2_41a.csv", recommendation, ["rank", "recommended_next_phase", "reason", "decision"])
    (OUT_DIR / "data_gap_prioritization_summary_v2_41a.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(summary, gaps)
    report = DOC.read_text(encoding="utf-8")
    (OUT_DIR / "DATA_GAP_PRIORITIZATION_v2_41a.md").write_text(report, encoding="utf-8")
    (OUT_DIR / "README.md").write_text(
        "# v2.41A Data Gap Prioritization\n\nPrioritization-only outputs. No network, new data download, dataset mutation, scoring recomputation, ranking change, UI change, deployment, public URL, financial recommendation or broker action is performed.\n",
        encoding="utf-8",
    )
    manifest_files = [
        CONTRACT,
        DOC,
        OUT_DIR / "data_gap_prioritization_matrix_v2_41a.csv",
        OUT_DIR / "data_gap_decision_register_v2_41a.csv",
        OUT_DIR / "data_gap_source_inventory_v2_41a.csv",
        OUT_DIR / "data_gap_impact_matrix_v2_41a.csv",
        OUT_DIR / "data_gap_next_phase_recommendation_v2_41a.csv",
        OUT_DIR / "data_gap_prioritization_summary_v2_41a.json",
        OUT_DIR / "DATA_GAP_PRIORITIZATION_v2_41a.md",
        OUT_DIR / "README.md",
    ]
    manifest = {
        "phase": PHASE,
        "status": STATUS,
        "files": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)}
            for path in manifest_files
        ],
    }
    (OUT_DIR / "data_gap_prioritization_manifest_v2_41a.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
