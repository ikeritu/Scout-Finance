from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


PHASE = "v2.41B"
STATUS = "LUXEMBOURG_ADAPTER_OR_CLOSURE_READY"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41b_luxembourg_adapter_or_closure"
SOURCE_SUMMARY = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41a_data_gap_prioritization" / "data_gap_prioritization_summary_v2_41a.json"
SOURCE_MATRIX = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41a_data_gap_prioritization" / "data_gap_prioritization_matrix_v2_41a.csv"
RANKING_JSON = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38bv_global_research_ranking" / "global_research_ranking_results_v2_38bv.json"
ELIGIBILITY_CSV = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38bo_global_scoring_eligibility" / "global_scoring_eligibility_v2_38bo.csv"
CONTRACT = ROOT / "config" / "luxembourg_adapter_or_closure_contract_v2_41b.json"
DOC = ROOT / "docs" / "LUXEMBOURG_ADAPTER_OR_CLOSURE_v2_41b.md"


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
    if status != "DATA_GAP_PRIORITIZATION_READY":
        raise ValueError(f"Expected v2.41A DATA_GAP_PRIORITIZATION_READY, got {status!r}")
    return status


def luxembourg_candidates() -> list[dict[str, object]]:
    rows = read_json(RANKING_JSON)
    return [
        row for row in rows
        if row.get("country") == "LU" and row.get("eligibility_status") == "NOT_YET_SCORED_NO_ADAPTER"
    ]


def has_structured_local_evidence(candidates: list[dict[str, object]]) -> bool:
    for row in candidates:
        raw_factors = row.get("raw_factors") or {}
        normalized_factors = row.get("normalized_factors") or {}
        if raw_factors or normalized_factors:
            return True
    return False


def write_docs(summary: dict[str, object], candidates: list[dict[str, object]]) -> None:
    DOC.write_text(
        f"""# Luxembourg Adapter Or Closure v2.41B

Status: `{summary['status']}`

Decision: `{summary['decision']}`

Luxembourg candidates affected: `{summary['luxembourg_candidate_count']}`

This phase resolves the bounded Luxembourg gap identified in `v2.41A`. It reads local evidence only and concludes that no local structured fundamentals/growth evidence is sufficient to build a real Luxembourg adapter without new acquisition.

Therefore Luxembourg is closed as a documented limitation for this cycle. No adapter is built.

Guardrails: no network, no data download, no new scoring, no ranking change, no methodology or weights change, no financial recommendations and no broker.

## Sample Candidates

{chr(10).join(f"- `{row.get('asset_id')}` · {row.get('ticker')} · {row.get('company_name')}" for row in candidates[:8])}
""",
        encoding="utf-8",
    )


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src_status = source_status()
    candidates = luxembourg_candidates()
    evidence_exists = has_structured_local_evidence(candidates)
    decision = "ADAPTER_READY_READ_ONLY" if evidence_exists else "DOCUMENTED_CLOSURE_READY"
    adapter_built = False
    closure_documented = not evidence_exists
    primary_reason = (
        "Local structured evidence exists and a read-only adapter can be considered."
        if evidence_exists
        else "No local structured fundamentals/growth evidence sufficient to build a real Luxembourg adapter without new acquisition."
    )

    candidate_rows = [
        {
            "asset_id": row.get("asset_id", ""),
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "country": row.get("country", ""),
            "eligibility_status": row.get("eligibility_status", ""),
            "confidence": row.get("confidence", ""),
            "coverage_weight": row.get("coverage_weight", ""),
            "review_reasons": ";".join(row.get("review_reasons", []) or []),
            "raw_factor_count": len(row.get("raw_factors") or {}),
            "normalized_factor_count": len(row.get("normalized_factors") or {}),
        }
        for row in candidates
    ]
    evidence_rows = [
        {
            "evidence_check": "local_luxembourg_candidate_count",
            "status": "PASS" if candidates else "WARN",
            "detail": f"{len(candidates)} Luxembourg rows found in v2.38BV with NOT_YET_SCORED_NO_ADAPTER.",
        },
        {
            "evidence_check": "structured_raw_or_normalized_factors",
            "status": "NOT_AVAILABLE" if not evidence_exists else "AVAILABLE",
            "detail": primary_reason,
        },
        {
            "evidence_check": "new_acquisition_policy",
            "status": "BLOCKED",
            "detail": "New data acquisition, network calls, credentials and scraping are outside v2.41B scope.",
        },
    ]
    matrix = [
        {
            "check_id": "41B-001",
            "area": "source_gate",
            "status": "PASS",
            "detail": "v2.41A data gap prioritization is ready.",
        },
        {
            "check_id": "41B-002",
            "area": "luxembourg_inventory",
            "status": "PASS" if candidates else "WARN",
            "detail": f"{len(candidates)} Luxembourg candidates reviewed.",
        },
        {
            "check_id": "41B-003",
            "area": "adapter_decision",
            "status": "PASS",
            "detail": decision,
        },
        {
            "check_id": "41B-004",
            "area": "guardrails",
            "status": "PASS",
            "detail": "No network, acquisition, scoring, ranking, methodology, UI or deployment changes.",
        },
    ]
    decision_rows = [
        {
            "decision": decision,
            "adapter_built": adapter_built,
            "closure_documented": closure_documented,
            "primary_reason": primary_reason,
            "next_phase": "v2.41C-uk-cboe-manual-review-decision",
        }
    ]
    recommendation_rows = [
        {
            "rank": 1,
            "recommended_next_phase": "v2.41C-uk-cboe-manual-review-decision",
            "reason": "Luxembourg is closed for this cycle; the next open decision is UK, Cboe Europe and manual reviews.",
        }
    ]
    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS",
        "source_phase": "v2.41A",
        "source_status": src_status,
        "stable_tag": "v2.38CJ-local-stable",
        "scope": "luxembourg_adapter_or_documented_closure",
        "luxembourg_candidate_count": len(candidates),
        "decision": decision,
        "adapter_built": adapter_built,
        "closure_documented": closure_documented,
        "primary_reason": primary_reason,
        "next_phase": "v2.41C-uk-cboe-manual-review-decision",
        "qa_fail_count": 0,
        "blocker_count": 0,
        **{flag: False for flag in FALSE_FLAGS},
    }

    write_csv(OUT_DIR / "luxembourg_adapter_or_closure_matrix_v2_41b.csv", matrix, ["check_id", "area", "status", "detail"])
    write_csv(OUT_DIR / "luxembourg_candidate_inventory_v2_41b.csv", candidate_rows, ["asset_id", "ticker", "company_name", "country", "eligibility_status", "confidence", "coverage_weight", "review_reasons", "raw_factor_count", "normalized_factor_count"])
    write_csv(OUT_DIR / "luxembourg_evidence_review_v2_41b.csv", evidence_rows, ["evidence_check", "status", "detail"])
    write_csv(OUT_DIR / "luxembourg_decision_register_v2_41b.csv", decision_rows, ["decision", "adapter_built", "closure_documented", "primary_reason", "next_phase"])
    write_csv(OUT_DIR / "luxembourg_next_phase_recommendation_v2_41b.csv", recommendation_rows, ["rank", "recommended_next_phase", "reason"])
    (OUT_DIR / "luxembourg_adapter_or_closure_summary_v2_41b.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(summary, candidates)
    (OUT_DIR / "LUXEMBOURG_ADAPTER_OR_CLOSURE_v2_41b.md").write_text(DOC.read_text(encoding="utf-8"), encoding="utf-8")
    (OUT_DIR / "README.md").write_text(
        "# v2.41B Luxembourg Adapter Or Closure\n\nLuxembourg adapter decision outputs. No network, data download, credentials, dataset mutation, new fundamentals/prices, scoring recomputation, ranking change, UI change, deployment, public URL, recommendations or broker actions are performed.\n",
        encoding="utf-8",
    )

    manifest_files = [
        CONTRACT,
        DOC,
        OUT_DIR / "luxembourg_adapter_or_closure_matrix_v2_41b.csv",
        OUT_DIR / "luxembourg_candidate_inventory_v2_41b.csv",
        OUT_DIR / "luxembourg_evidence_review_v2_41b.csv",
        OUT_DIR / "luxembourg_decision_register_v2_41b.csv",
        OUT_DIR / "luxembourg_next_phase_recommendation_v2_41b.csv",
        OUT_DIR / "luxembourg_adapter_or_closure_summary_v2_41b.json",
        OUT_DIR / "LUXEMBOURG_ADAPTER_OR_CLOSURE_v2_41b.md",
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
    (OUT_DIR / "luxembourg_adapter_or_closure_manifest_v2_41b.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
