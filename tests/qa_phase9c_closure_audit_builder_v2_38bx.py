#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_phase9c_closure_audit_v2_38bx.py"


def module():
    spec = importlib.util.spec_from_file_location("build_phase9c_closure_audit_v2_38bx", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "company_name", "country", "eligibility_status", "confidence", "coverage_weight", "total_score", "rank", "review_reasons", "phase"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    mod = module()
    rows = [
        {"asset_id": "A1", "ticker": "AAA", "company_name": "Compugen Ltd.", "country": "US", "eligibility_status": "ELIGIBLE_PARTIAL", "confidence": "HIGH", "coverage_weight": "0.9", "total_score": "82.0", "rank": "1", "review_reasons": "", "phase": "v2.38BV-global-research-ranking"},
        {"asset_id": "A2", "ticker": "NVDA", "company_name": "NVIDIA Corp", "country": "US", "eligibility_status": "PARTIAL_COMPARABILITY", "confidence": "MEDIUM", "coverage_weight": "0.5", "total_score": "94.0", "rank": "", "review_reasons": "", "phase": "v2.38BV-global-research-ranking"},
        {"asset_id": "A3", "ticker": "PLTR", "company_name": "Palantir Technologies Inc", "country": "US", "eligibility_status": "PARTIAL_COMPARABILITY", "confidence": "MEDIUM", "coverage_weight": "0.5", "total_score": "91.0", "rank": "", "review_reasons": "", "phase": "v2.38BV-global-research-ranking"},
        {"asset_id": "A4", "ticker": "ACIC", "company_name": "American Coastal Insurance Corporation", "country": "US", "eligibility_status": "REVIEW_REQUIRED", "confidence": "NOT_RANKABLE", "coverage_weight": "1.0", "total_score": "", "rank": "", "review_reasons": "financial_institution_requires_separate_factor_contract", "phase": "v2.38BV-global-research-ranking"},
        {"asset_id": "A5", "ticker": "ALE", "company_name": "Allegro.eu SA", "country": "LU", "eligibility_status": "NOT_YET_SCORED_NO_ADAPTER", "confidence": "NOT_RANKABLE", "coverage_weight": "0.0", "total_score": "", "rank": "", "review_reasons": "no_fundamentals_growth_ratio_adapter_built_yet_for_this_country", "phase": "v2.38BV-global-research-ranking"},
        {"asset_id": "A6", "ticker": "BLK", "company_name": "Blocked Co", "country": "US", "eligibility_status": "BLOCKED", "confidence": "NOT_RANKABLE", "coverage_weight": "0.0", "total_score": "", "rank": "", "review_reasons": "insufficient_coverage", "phase": "v2.38BV-global-research-ranking"},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        csv_path = root / "ranking.csv"
        results_path = root / "ranking.json"
        report_path = root / "report.json"
        ui_path = root / "global_ranking.py"
        app_path = root / "app.py"
        ui_report_path = root / "ui.md"
        contract_path = root / "contract.json"
        out = root / "out"
        write_csv(csv_path, rows)
        results_path.write_text(json.dumps(rows), encoding="utf-8")
        report_path.write_text(json.dumps({"status": "COMPLETED_GLOBAL_RESEARCH_RANKING_EXPERIMENTAL"}), encoding="utf-8")
        ui_path.write_text('RESULTS_REL = "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json"\n', encoding="utf-8")
        app_path.write_text('heading(st, "Ranking global (experimental)", "Experimental research ranking; not advice.")\n', encoding="utf-8")
        ui_report_path.write_text("Experimental ranking. Never advice.", encoding="utf-8")
        contract = {
            "input_results": str(results_path),
            "input_csv": str(csv_path),
            "input_report": str(report_path),
            "input_ui_module": str(ui_path),
            "input_app": str(app_path),
            "input_ui_report": str(ui_report_path),
            "input_phase_scoring": "v2.38BV",
            "input_phase_ui": "v2.38BW",
            "expected_main_ranking_count": 1,
            "expected_partial_comparability_count": 2,
            "expected_review_required_count": 1,
            "expected_blocked_count": 1,
            "expected_not_yet_scored_count": 1,
            "expected_total_count": 6,
            "sentinel_cases": {"top_ranked_company_asset_id": "A1", "top_ranked_company_name_contains": "Compugen", "nvidia_asset_id": "A2", "palantir_asset_id": "A3", "american_coastal_asset_id": "A4", "allegro_asset_id": "A5"},
            "scoring_recomputed": False,
            "methodology_changed": False,
            "weights_changed": False,
            "network_allowed": False,
            "broker_actions_allowed": False,
            "financial_advice_allowed": False,
            "recommendations_allowed": False,
            "final_status": "COMPLETED_PHASE9C_CLOSURE_AUDIT_EXPERIMENTAL_RANKING_VERIFIED",
        }
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        summary = mod.build(contract_path, out)
        assert summary["qa_status"] == "PASS"
        assert (out / "phase9c_closure_audit_manifest_v2_38bx.json").is_file()
        assert (out / "phase9c_sentinel_cases_v2_38bx.csv").is_file()
    print("PASS: v2.38BX/builder/fixtures/populations-sentinels-readonly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
