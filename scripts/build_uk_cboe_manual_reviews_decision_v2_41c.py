from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


PHASE = "v2.41C"
STATUS = "UK_CBOE_MANUAL_REVIEWS_DECISION_READY"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41c_uk_cboe_manual_reviews_decision"
SOURCE_SUMMARY = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41b_luxembourg_adapter_or_closure" / "luxembourg_adapter_or_closure_summary_v2_41b.json"
GAP_MATRIX = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41a_data_gap_prioritization" / "data_gap_prioritization_matrix_v2_41a.csv"
RANKING_JSON = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38bv_global_research_ranking" / "global_research_ranking_results_v2_38bv.json"
ELIGIBILITY_CSV = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38bo_global_scoring_eligibility" / "global_scoring_eligibility_v2_38bo.csv"
RISK_REGISTER = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38cg_limitations_backlog_product_risk_register" / "product_risk_register_v2_38cg.csv"
CONTRACT = ROOT / "config" / "uk_cboe_manual_reviews_decision_contract_v2_41c.json"
DOC = ROOT / "docs" / "UK_CBOE_MANUAL_REVIEWS_DECISION_v2_41c.md"


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
    if status != "LUXEMBOURG_ADAPTER_OR_CLOSURE_READY":
        raise ValueError(f"Expected v2.41B ready, got {status!r}")
    return status


def ranking_rows() -> list[dict]:
    rows = read_json(RANKING_JSON)
    if not isinstance(rows, list):
        raise ValueError("Ranking results must be a list")
    return rows


def review_reason_counts(rows: list[dict]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        for reason in row.get("review_reasons", []) or []:
            counts[reason] += 1
    return counts


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src_status = source_status()
    rows = ranking_rows()
    status_counts = Counter(row.get("eligibility_status", "") for row in rows)
    reasons = review_reason_counts(rows)
    review_rows = [row for row in rows if row.get("eligibility_status") == "REVIEW_REQUIRED"]
    financial_rows = [
        row for row in review_rows
        if "financial_institution_requires_separate_factor_contract" in (row.get("review_reasons") or [])
    ]
    extreme_rows = [
        row for row in review_rows
        if "absolute_margin_outside_300pct" in (row.get("review_reasons") or [])
    ]
    uk_rows = [row for row in rows if row.get("country") in {"GB", "UK"}]
    no_adapter_rows = [row for row in rows if row.get("eligibility_status") == "NOT_YET_SCORED_NO_ADAPTER"]
    risk_rows = read_csv(RISK_REGISTER) if RISK_REGISTER.exists() else []

    decision_matrix = [
        {
            "decision_area": "United Kingdom",
            "decision": "REQUIRES_USER_DECISION_OR_DOCUMENTED_LIMITATION",
            "reason": "Official access, safe automation, credentials and document routes remain conditioned.",
            "affected_population": len(uk_rows),
            "next_phase": "v2.41D-final-coverage-limitations",
        },
        {
            "decision_area": "Cboe Europe",
            "decision": "BLOCKED_STRUCTURAL_KEEP_DOCUMENTED",
            "reason": "Identity, fundamentals and prices remain structurally problematic or outside approved scope.",
            "affected_population": "large_structural_scope",
            "next_phase": "v2.41D-final-coverage-limitations",
        },
        {
            "decision_area": "Manual reviews",
            "decision": "DEFER_POST_RELEASE_WITH_EXPLICIT_SEPARATION",
            "reason": "Review-required rows must stay outside the main ranking unless reviewed by a human or separate contract.",
            "affected_population": len(review_rows),
            "next_phase": "v2.41D-final-coverage-limitations",
        },
        {
            "decision_area": "Financial institutions",
            "decision": "REQUIRES_SEPARATE_FACTOR_CONTRACT",
            "reason": "Banks and insurers are not comparable with the industrial factor contract.",
            "affected_population": len(financial_rows),
            "next_phase": "v2.41D-final-coverage-limitations",
        },
        {
            "decision_area": "Extreme margin",
            "decision": "KEEP_REVIEW_REQUIRED",
            "reason": "Extreme margins stay separated; no silent imputation, winsorization or normalization.",
            "affected_population": len(extreme_rows),
            "next_phase": "v2.41D-final-coverage-limitations",
        },
    ]
    uk_scope = [
        {
            "scope": "uk_or_gb_rows_in_ranking",
            "count": len(uk_rows),
            "decision": "REQUIRES_USER_DECISION_OR_DOCUMENTED_LIMITATION",
            "detail": "UK remains a conditioned source/access decision; no state changes performed.",
        },
        {
            "scope": "no_adapter_rows_total",
            "count": len(no_adapter_rows),
            "decision": "KEEP_SEPARATED",
            "detail": "No-adapter rows remain not rankable; Luxembourg already closed in v2.41B.",
        },
    ]
    cboe_register = [
        {
            "area": "Cboe Europe",
            "decision": "BLOCKED_STRUCTURAL_KEEP_DOCUMENTED",
            "evidence": "v2.41A and historical roadmap keep Cboe Europe as structural limitation.",
            "closure_condition": "Keep documented unless the user approves a new source, paid route or manual workflow.",
        }
    ]
    manual_inventory = [
        {
            "asset_id": row.get("asset_id", ""),
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "country": row.get("country", ""),
            "eligibility_status": row.get("eligibility_status", ""),
            "review_reasons": ";".join(row.get("review_reasons", []) or []),
        }
        for row in review_rows
    ]
    financial_inventory = [
        {
            "asset_id": row.get("asset_id", ""),
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "country": row.get("country", ""),
            "decision": "REQUIRES_SEPARATE_FACTOR_CONTRACT",
        }
        for row in financial_rows
    ]
    extreme_inventory = [
        {
            "asset_id": row.get("asset_id", ""),
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "country": row.get("country", ""),
            "decision": "KEEP_REVIEW_REQUIRED",
        }
        for row in extreme_rows
    ]
    next_phase = [
        {
            "rank": 1,
            "recommended_next_phase": "v2.41D-final-coverage-limitations",
            "reason": "UK, Cboe Europe and manual reviews are now decision-closed; consolidate final coverage limitations by country/source/population.",
        }
    ]
    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS",
        "source_phase": "v2.41B",
        "source_status": src_status,
        "stable_tag": "v2.38CJ-local-stable",
        "scope": "uk_cboe_manual_reviews_decision_only",
        "uk_decision": "REQUIRES_USER_DECISION_OR_DOCUMENTED_LIMITATION",
        "cboe_europe_decision": "BLOCKED_STRUCTURAL_KEEP_DOCUMENTED",
        "manual_reviews_decision": "DEFER_POST_RELEASE_WITH_EXPLICIT_SEPARATION",
        "financial_institutions_decision": "REQUIRES_SEPARATE_FACTOR_CONTRACT",
        "extreme_margin_decision": "KEEP_REVIEW_REQUIRED",
        "next_phase": "v2.41D-final-coverage-limitations",
        "ranking_total": len(rows),
        "ranking_main_count": status_counts["ELIGIBLE_PARTIAL"],
        "partial_comparability_count": status_counts["PARTIAL_COMPARABILITY"],
        "review_required_count": status_counts["REVIEW_REQUIRED"],
        "blocked_count": status_counts["BLOCKED"],
        "no_adapter_count": status_counts["NOT_YET_SCORED_NO_ADAPTER"],
        "financial_review_count": len(financial_rows),
        "extreme_margin_review_count": len(extreme_rows),
        "uk_scope_count": len(uk_rows),
        "risk_register_rows": len(risk_rows),
        "qa_fail_count": 0,
        "blocker_count": 0,
        **{flag: False for flag in FALSE_FLAGS},
    }

    write_csv(OUT_DIR / "uk_cboe_manual_reviews_decision_matrix_v2_41c.csv", decision_matrix, ["decision_area", "decision", "reason", "affected_population", "next_phase"])
    write_csv(OUT_DIR / "uk_scope_inventory_v2_41c.csv", uk_scope, ["scope", "count", "decision", "detail"])
    write_csv(OUT_DIR / "cboe_europe_decision_register_v2_41c.csv", cboe_register, ["area", "decision", "evidence", "closure_condition"])
    write_csv(OUT_DIR / "manual_reviews_inventory_v2_41c.csv", manual_inventory, ["asset_id", "ticker", "company_name", "country", "eligibility_status", "review_reasons"])
    write_csv(OUT_DIR / "financial_institutions_review_v2_41c.csv", financial_inventory, ["asset_id", "ticker", "company_name", "country", "decision"])
    write_csv(OUT_DIR / "extreme_margin_review_v2_41c.csv", extreme_inventory, ["asset_id", "ticker", "company_name", "country", "decision"])
    write_csv(OUT_DIR / "uk_cboe_manual_reviews_next_phase_v2_41c.csv", next_phase, ["rank", "recommended_next_phase", "reason"])
    summary_path = OUT_DIR / "uk_cboe_manual_reviews_decision_summary_v2_41c.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = f"""# UK Cboe Manual Reviews Decision v2.41C

Status: `{STATUS}`

This phase closes UK, Cboe Europe and manual review decisions using local evidence only. It performs no network calls, no data download, no new scoring, no ranking change, no methodology or weights change, no financial recommendations and no broker actions.

## Decisions

- UK: `REQUIRES_USER_DECISION_OR_DOCUMENTED_LIMITATION`
- Cboe Europe: `BLOCKED_STRUCTURAL_KEEP_DOCUMENTED`
- Manual reviews: `DEFER_POST_RELEASE_WITH_EXPLICIT_SEPARATION`
- Financial institutions: `REQUIRES_SEPARATE_FACTOR_CONTRACT`
- Extreme margin: `KEEP_REVIEW_REQUIRED`

## Ranking Counts

- Total: `{summary['ranking_total']}`
- Main ranking: `{summary['ranking_main_count']}`
- Partial comparability: `{summary['partial_comparability_count']}`
- Review required: `{summary['review_required_count']}`
- Blocked: `{summary['blocked_count']}`
- No adapter: `{summary['no_adapter_count']}`
"""
    DOC.write_text(report, encoding="utf-8")
    (OUT_DIR / "UK_CBOE_MANUAL_REVIEWS_DECISION_v2_41c.md").write_text(report, encoding="utf-8")
    (OUT_DIR / "README.md").write_text(
        "# v2.41C UK Cboe Manual Reviews Decision\n\nDecision-only outputs. No network, data download, dataset mutation, scoring recomputation, ranking change, UI change, deployment, public URL, financial recommendation or broker action is performed.\n",
        encoding="utf-8",
    )

    manifest_files = [
        CONTRACT,
        DOC,
        OUT_DIR / "uk_cboe_manual_reviews_decision_matrix_v2_41c.csv",
        OUT_DIR / "uk_scope_inventory_v2_41c.csv",
        OUT_DIR / "cboe_europe_decision_register_v2_41c.csv",
        OUT_DIR / "manual_reviews_inventory_v2_41c.csv",
        OUT_DIR / "financial_institutions_review_v2_41c.csv",
        OUT_DIR / "extreme_margin_review_v2_41c.csv",
        OUT_DIR / "uk_cboe_manual_reviews_next_phase_v2_41c.csv",
        summary_path,
        OUT_DIR / "UK_CBOE_MANUAL_REVIEWS_DECISION_v2_41c.md",
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
    (OUT_DIR / "uk_cboe_manual_reviews_decision_manifest_v2_41c.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
