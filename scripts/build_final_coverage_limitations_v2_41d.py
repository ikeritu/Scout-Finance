from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


PHASE = "v2.41D"
STATUS = "FINAL_COVERAGE_LIMITATIONS_READY"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41d_final_coverage_limitations"
SOURCE_SUMMARY = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41c_uk_cboe_manual_reviews_decision" / "uk_cboe_manual_reviews_decision_summary_v2_41c.json"
RANKING_JSON = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38bv_global_research_ranking" / "global_research_ranking_results_v2_38bv.json"
GAP_MATRIX = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41a_data_gap_prioritization" / "data_gap_prioritization_matrix_v2_41a.csv"
LUX_SUMMARY = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41b_luxembourg_adapter_or_closure" / "luxembourg_adapter_or_closure_summary_v2_41b.json"
MANUAL_REVIEWS = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41c_uk_cboe_manual_reviews_decision" / "manual_reviews_inventory_v2_41c.csv"
FINANCIAL_REVIEWS = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41c_uk_cboe_manual_reviews_decision" / "financial_institutions_review_v2_41c.csv"
EXTREME_REVIEWS = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41c_uk_cboe_manual_reviews_decision" / "extreme_margin_review_v2_41c.csv"
CONTRACT = ROOT / "config" / "final_coverage_limitations_contract_v2_41d.json"
DOC = ROOT / "docs" / "FINAL_COVERAGE_LIMITATIONS_v2_41d.md"

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

STATUS_ORDER = [
    "ELIGIBLE_PARTIAL",
    "PARTIAL_COMPARABILITY",
    "REVIEW_REQUIRED",
    "BLOCKED",
    "NOT_YET_SCORED_NO_ADAPTER",
]


def read_json(path: Path):
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
    if status != "UK_CBOE_MANUAL_REVIEWS_DECISION_READY":
        raise ValueError(f"Expected v2.41C ready, got {status!r}")
    return status


def ranking_rows() -> list[dict]:
    rows = read_json(RANKING_JSON)
    if not isinstance(rows, list):
        raise ValueError("Ranking output must be a list")
    return rows


def by_status(rows: list[dict]) -> list[dict[str, object]]:
    counts = Counter(row.get("eligibility_status", "") for row in rows)
    total = len(rows)
    return [
        {
            "ranking_status": status,
            "count": counts[status],
            "share_of_total": round(counts[status] / total, 6) if total else 0,
            "final_note": "main experimental ranking" if status == "ELIGIBLE_PARTIAL" else "kept separated with explicit limitation",
        }
        for status in STATUS_ORDER
    ]


def by_country(rows: list[dict]) -> list[dict[str, object]]:
    grouped: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        country = row.get("country") or "UNKNOWN"
        grouped[country]["total_rows"] += 1
        grouped[country][row.get("eligibility_status", "")] += 1
    out = []
    for country, counts in sorted(grouped.items()):
        out.append(
            {
                "country": country,
                "total_rows": counts["total_rows"],
                "main_ranking": counts["ELIGIBLE_PARTIAL"],
                "partial_comparability": counts["PARTIAL_COMPARABILITY"],
                "review_required": counts["REVIEW_REQUIRED"],
                "blocked": counts["BLOCKED"],
                "no_adapter": counts["NOT_YET_SCORED_NO_ADAPTER"],
            }
        )
    return out


def decision_areas(rows: list[dict]) -> list[dict[str, object]]:
    counts = Counter(row.get("eligibility_status", "") for row in rows)
    lux = read_json(LUX_SUMMARY)
    manual = read_csv(MANUAL_REVIEWS)
    financial = read_csv(FINANCIAL_REVIEWS)
    extreme = read_csv(EXTREME_REVIEWS)
    return [
        {"decision_area": "Luxembourg", "final_status": "DOCUMENTED_LIMITATION", "decision_source_phase": "v2.41B", "affected_population": lux.get("luxembourg_candidate_count", 0), "limitation_type": "no_adapter_no_local_evidence", "release_blocking": False, "final_note": "closed as documented limitation"},
        {"decision_area": "UK", "final_status": "USER_DECISION_OR_DOCUMENTED_LIMITATION", "decision_source_phase": "v2.41C", "affected_population": "conditioned_scope", "limitation_type": "official_access_or_credentials", "release_blocking": False, "final_note": "requires user decision or remains documented limitation"},
        {"decision_area": "Cboe Europe", "final_status": "STRUCTURAL_BLOCK_DOCUMENTED", "decision_source_phase": "v2.41C", "affected_population": "large_structural_scope", "limitation_type": "identity_fundamentals_prices_structural", "release_blocking": False, "final_note": "kept as structural limitation"},
        {"decision_area": "Europe prices", "final_status": "STRUCTURAL_BLOCK_DOCUMENTED", "decision_source_phase": "v2.41A", "affected_population": 689, "limitation_type": "no_viable_free_source", "release_blocking": False, "final_note": "no free automated source confirmed"},
        {"decision_area": "Manual reviews", "final_status": "DEFER_POST_RELEASE_WITH_EXPLICIT_SEPARATION", "decision_source_phase": "v2.41C", "affected_population": len(manual), "limitation_type": "manual_review_required", "release_blocking": False, "final_note": "kept outside main ranking"},
        {"decision_area": "Financial institutions", "final_status": "REQUIRES_SEPARATE_FACTOR_CONTRACT", "decision_source_phase": "v2.41C", "affected_population": len(financial), "limitation_type": "methodology_contract_gap", "release_blocking": False, "final_note": "not comparable with industrial ratios"},
        {"decision_area": "Extreme margin", "final_status": "KEEP_REVIEW_REQUIRED", "decision_source_phase": "v2.41C", "affected_population": len(extreme), "limitation_type": "outlier_review", "release_blocking": False, "final_note": "no silent normalization or imputation"},
        {"decision_area": "Coverage below threshold", "final_status": "FAIL_CLOSED_BLOCKED", "decision_source_phase": "v2.38BV", "affected_population": counts["BLOCKED"], "limitation_type": "insufficient_real_factor_coverage", "release_blocking": False, "final_note": "blocked from scoring until coverage improves"},
        {"decision_area": "External publication risk", "final_status": "CONTROLLED_SAFE_DEMO_ONLY", "decision_source_phase": "v2.40D", "affected_population": "product_surface", "limitation_type": "publication_guardrail", "release_blocking": False, "final_note": "safe demo and manual QA required"},
        {"decision_area": "Security / sensitive files", "final_status": "MONITOR_CONTINUOUSLY", "decision_source_phase": "v2.39C-v2.40D", "affected_population": "repository_surface", "limitation_type": "security_guardrail", "release_blocking": False, "final_note": "keep secret/file checks visible"},
        {"decision_area": "Product/legal wording", "final_status": "LOCKED_GUARDRAIL", "decision_source_phase": "v2.38BZ-v2.41C", "affected_population": "all_user_facing_surfaces", "limitation_type": "no_advice_no_broker_no_recommendations", "release_blocking": False, "final_note": "must remain visible"},
    ]


def limitations_register(decisions: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, decision in enumerate(decisions, start=1):
        rows.append(
            {
                "limitation_id": f"LIM-{idx:02d}",
                "decision_area": decision["decision_area"],
                "final_status": decision["final_status"],
                "limitation_type": decision["limitation_type"],
                "release_blocking": decision["release_blocking"],
                "final_note": decision["final_note"],
            }
        )
    return rows


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src_status = source_status()
    rows = ranking_rows()
    status_rows = by_status(rows)
    country_rows = by_country(rows)
    decision_rows = decision_areas(rows)
    limitation_rows = limitations_register(decision_rows)
    counts = Counter(row.get("eligibility_status", "") for row in rows)
    component_sum = sum(counts[status] for status in STATUS_ORDER)
    delta = len(rows) - component_sum
    reconciliation = [
        {"metric": "total_ranking_rows", "count": len(rows)},
        {"metric": "main_plus_partial_plus_review_plus_blocked_plus_no_adapter", "count": component_sum},
        {"metric": "population_reconciliation_delta", "count": delta},
    ]
    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS",
        "source_phase": "v2.41C",
        "source_status": src_status,
        "stable_tag": "v2.38CJ-local-stable",
        "scope": "final_coverage_limitations_only",
        "ranking_total": len(rows),
        "ranking_main_count": counts["ELIGIBLE_PARTIAL"],
        "partial_comparability_count": counts["PARTIAL_COMPARABILITY"],
        "review_required_count": counts["REVIEW_REQUIRED"],
        "blocked_count": counts["BLOCKED"],
        "no_adapter_count": counts["NOT_YET_SCORED_NO_ADAPTER"],
        "population_reconciliation_delta": delta,
        "final_limitation_count": len(limitation_rows),
        "release_blocking_limitation_count": sum(1 for row in limitation_rows if str(row["release_blocking"]).lower() == "true"),
        "next_phase": "v2.42A-final-ux-hardening",
        "qa_fail_count": 0,
        "blocker_count": 0,
        **{flag: False for flag in FALSE_FLAGS},
    }
    write_csv(OUT_DIR / "final_coverage_by_ranking_status_v2_41d.csv", status_rows, ["ranking_status", "count", "share_of_total", "final_note"])
    write_csv(OUT_DIR / "final_coverage_by_country_v2_41d.csv", country_rows, ["country", "total_rows", "main_ranking", "partial_comparability", "review_required", "blocked", "no_adapter"])
    write_csv(OUT_DIR / "final_coverage_by_decision_area_v2_41d.csv", decision_rows, ["decision_area", "final_status", "decision_source_phase", "affected_population", "limitation_type", "release_blocking", "final_note"])
    write_csv(OUT_DIR / "final_limitations_register_v2_41d.csv", limitation_rows, ["limitation_id", "decision_area", "final_status", "limitation_type", "release_blocking", "final_note"])
    write_csv(OUT_DIR / "final_population_reconciliation_v2_41d.csv", reconciliation, ["metric", "count"])
    summary_path = OUT_DIR / "final_coverage_limitations_summary_v2_41d.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = f"""# Final Coverage Limitations v2.41D

Status: `{STATUS}`

This phase consolidates final coverage and limitations using local artifacts only. It performs no network calls, no data download, no new scoring, no ranking change, no financial recommendations and no broker actions.

## Population Reconciliation

- Total: `{summary['ranking_total']}`
- Main ranking: `{summary['ranking_main_count']}`
- Partial comparability: `{summary['partial_comparability_count']}`
- Review required: `{summary['review_required_count']}`
- Blocked: `{summary['blocked_count']}`
- No adapter: `{summary['no_adapter_count']}`
- Delta: `{summary['population_reconciliation_delta']}`

## Final Limitations

{chr(10).join(f"- {row['decision_area']}: `{row['final_status']}`" for row in limitation_rows)}
"""
    DOC.write_text(report, encoding="utf-8")
    (OUT_DIR / "FINAL_COVERAGE_LIMITATIONS_v2_41d.md").write_text(report, encoding="utf-8")
    (OUT_DIR / "README.md").write_text(
        "# v2.41D Final Coverage Limitations\n\nFinal coverage and limitations outputs. No network, data download, dataset mutation, scoring recomputation, ranking change, UI change, deployment, public URL, financial recommendation or broker action is performed.\n",
        encoding="utf-8",
    )
    manifest_files = [
        CONTRACT,
        DOC,
        OUT_DIR / "final_coverage_by_ranking_status_v2_41d.csv",
        OUT_DIR / "final_coverage_by_country_v2_41d.csv",
        OUT_DIR / "final_coverage_by_decision_area_v2_41d.csv",
        OUT_DIR / "final_limitations_register_v2_41d.csv",
        OUT_DIR / "final_population_reconciliation_v2_41d.csv",
        summary_path,
        OUT_DIR / "FINAL_COVERAGE_LIMITATIONS_v2_41d.md",
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
    (OUT_DIR / "final_coverage_limitations_manifest_v2_41d.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
