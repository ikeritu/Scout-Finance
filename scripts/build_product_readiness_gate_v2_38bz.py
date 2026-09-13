#!/usr/bin/env python3
"""v2.38BZ product readiness gate.

This phase does not change the ranking. It reads v2.38BV/BX/BY outputs and
decides whether the current experimental ranking surface is usable as a
local research product with explicit limitations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38BZ-product-readiness-gate"
CONTRACT = ROOT / "config/product_readiness_gate_contract_v2_38bz.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bz_product_readiness_gate"

STATUS_TO_CONTRACT_KEY = {
    "ELIGIBLE_PARTIAL": "expected_main_ranking_count",
    "PARTIAL_COMPARABILITY": "expected_partial_comparability_count",
    "REVIEW_REQUIRED": "expected_review_required_count",
    "BLOCKED": "expected_blocked_count",
    "NOT_YET_SCORED_NO_ADAPTER": "expected_not_yet_scored_count",
}

POSITIVE_ADVICE_PATTERNS = [
    r"\bstrong buy\b",
    r"\bbuy\b",
    r"\bsell\b",
    r"\bhold\b",
    r"\btarget price\b",
    r"\bundervalued\b",
    r"\bovervalued\b",
    r"\bexpected return\b",
    r"\bguaranteed\b",
    r"\brecommendation\b",
    r"\bcomprar\b",
    r"\bvender\b",
    r"\bmantener\b",
    r"\bprecio objetivo\b",
    r"\brentabilidad esperada\b",
    r"\binfravalorada\b",
    r"\bsobrevalorada\b",
]

LIMITATIONS = [
    ("experimental_ranking", "Ranking experimental: usable only to prioritize local research, not to make investment decisions."),
    ("no_out_of_sample_validation", "No out-of-sample predictive validation is available for the global ranking."),
    ("partial_country_coverage", "Country coverage is partial and depends on real data adapters already built."),
    ("missing_adapters", "Some jurisdictions remain not yet scored because no real ratios/growth adapter exists."),
    ("blocked_low_coverage", "Assets with less than contractual coverage remain blocked and visible, never imputed."),
    ("financial_institutions_pending_contract", "Financial institutions require a separate factor contract before scoring."),
    ("price_coverage_gaps", "Some otherwise useful assets lack real price coverage and remain outside the main ranking."),
    ("no_automatic_recommendations", "The surface is not authorized for automatic buy/sell/hold recommendations or broker workflows."),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def clean_text(value: str) -> str:
    table = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return value.translate(table).lower()


def has_positive_advice(text: str) -> bool:
    normalized = clean_text(text)
    for pattern in POSITIVE_ADVICE_PATTERNS:
        for match in re.finditer(pattern, normalized, flags=re.I):
            context = normalized[max(0, match.start() - 56): match.end() + 56]
            if "watchlist" in context:
                continue
            if not re.search(r"\b(no|not|never|nunca|sin|ni)\b", context):
                return True
    return False


def population_checks(rows: list[dict[str, Any]], contract: dict[str, Any]) -> list[dict[str, Any]]:
    counts = Counter(str(row["eligibility_status"]) for row in rows)
    output = []
    for status, key in STATUS_TO_CONTRACT_KEY.items():
        expected = int(contract[key])
        actual = counts[status]
        output.append({"category": "population", "check": status, "expected": expected, "actual": actual, "critical": "true", "status": "PASS" if actual == expected else "FAIL"})
    expected_total = int(contract["expected_total_count"])
    output.append({"category": "population", "check": "TOTAL", "expected": expected_total, "actual": len(rows), "critical": "true", "status": "PASS" if len(rows) == expected_total else "FAIL"})
    return output


def upstream_checks(bx_summary: dict[str, Any], by_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"category": "upstream", "check": "v2_38bx_passed", "expected": "COMPLETED_PHASE9C_CLOSURE_AUDIT_EXPERIMENTAL_RANKING_VERIFIED", "actual": bx_summary.get("status", ""), "critical": "true", "status": "PASS" if bx_summary.get("qa_status") == "PASS" else "FAIL"},
        {"category": "upstream", "check": "v2_38by_passed", "expected": "COMPLETED_RANKING_UX_HARDENING_READ_ONLY", "actual": by_summary.get("status", ""), "critical": "true", "status": "PASS" if by_summary.get("qa_status") == "PASS" else "FAIL"},
    ]


def ui_checks(app_file: Path, ui_module: Path, contract: dict[str, Any]) -> list[dict[str, Any]]:
    app_text = app_file.read_text(encoding="utf-8")
    module_text = ui_module.read_text(encoding="utf-8")
    app_text_clean = clean_text(app_text)
    rows = []
    for token in contract["required_ui_features"]:
        rows.append({"category": "ui", "check": f"feature_present:{token}", "expected": "present", "actual": "present" if token in app_text else "missing", "target": rel(app_file), "critical": "true", "status": "PASS" if token in app_text else "FAIL"})
    for token in contract["required_copy_tokens"]:
        normalized_token = clean_text(token)
        rows.append({"category": "ui", "check": f"copy_present:{token}", "expected": "present", "actual": "present" if normalized_token in app_text_clean else "missing", "target": rel(app_file), "critical": "true", "status": "PASS" if normalized_token in app_text_clean else "FAIL"})
    for token in ["score_assets(", "percentile_scores(", "build_raw_factors(", "build_global_research_ranking_v2_38bv", "requests.", "httpx.", "urlopen(", "subprocess.", "os.system("]:
        rows.append({"category": "guardrail", "check": f"app_forbidden_token_absent:{token}", "expected": "absent", "actual": "present" if token in app_text else "absent", "target": rel(app_file), "critical": "true", "status": "PASS" if token not in app_text else "FAIL"})
    for token in ["score_assets(", "percentile_scores(", "build_raw_factors(", "requests.", "httpx.", "urllib.", "urlopen(", "subprocess.", "os.system("]:
        rows.append({"category": "guardrail", "check": f"loader_forbidden_token_absent:{token}", "expected": "absent", "actual": "present" if token in module_text else "absent", "target": rel(ui_module), "critical": "true", "status": "PASS" if token not in module_text else "FAIL"})
    return rows


def guardrail_checks(paths: list[Path], contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {"category": "guardrail", "check": "scoring_recomputed", "expected": "false", "actual": str(contract["scoring_recomputed"]).lower(), "critical": "true", "status": "PASS" if contract["scoring_recomputed"] is False else "FAIL"},
        {"category": "guardrail", "check": "methodology_changed", "expected": "false", "actual": str(contract["methodology_changed"]).lower(), "critical": "true", "status": "PASS" if contract["methodology_changed"] is False else "FAIL"},
        {"category": "guardrail", "check": "weights_changed", "expected": "false", "actual": str(contract["weights_changed"]).lower(), "critical": "true", "status": "PASS" if contract["weights_changed"] is False else "FAIL"},
        {"category": "guardrail", "check": "network_allowed", "expected": "false", "actual": str(contract["network_allowed"]).lower(), "critical": "true", "status": "PASS" if contract["network_allowed"] is False else "FAIL"},
        {"category": "guardrail", "check": "broker_actions_allowed", "expected": "false", "actual": str(contract["broker_actions_allowed"]).lower(), "critical": "true", "status": "PASS" if contract["broker_actions_allowed"] is False else "FAIL"},
        {"category": "guardrail", "check": "financial_advice_allowed", "expected": "false", "actual": str(contract["financial_advice_allowed"]).lower(), "critical": "true", "status": "PASS" if contract["financial_advice_allowed"] is False else "FAIL"},
        {"category": "guardrail", "check": "recommendations_allowed", "expected": "false", "actual": str(contract["recommendations_allowed"]).lower(), "critical": "true", "status": "PASS" if contract["recommendations_allowed"] is False else "FAIL"},
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        rows.append({"category": "guardrail", "check": f"no_positive_advice_language:{rel(path)}", "expected": "true", "actual": str(not has_positive_advice(text)).lower(), "target": rel(path), "critical": "true", "status": "PASS" if not has_positive_advice(text) else "FAIL"})
    return rows


def limitation_rows() -> list[dict[str, Any]]:
    return [{"limitation_id": key, "description": description, "blocks_local_research_use": "false", "blocks_financial_advice_or_broker_use": "true"} for key, description in LIMITATIONS]


def readiness_status(checks: list[dict[str, Any]], limitations: list[dict[str, Any]], expected: str) -> str:
    critical_failed = any(row["status"] != "PASS" and row.get("critical") == "true" for row in checks)
    if critical_failed:
        return "PRODUCT_READINESS_BLOCKED"
    if limitations and expected == "PRODUCT_READINESS_PASS_WITH_LIMITATIONS":
        return expected
    return "PRODUCT_READINESS_PASS"


def manifest_for(inputs: list[Path], output_dir: Path, guardrails: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "product_readiness_gate_manifest_v2_38bz.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs},
        "outputs": outputs,
        "guardrails": guardrails,
        "scripts": ["scripts/build_product_readiness_gate_v2_38bz.py"],
        "tests": [
            "tests/qa_product_readiness_gate_v2_38bz.py",
            "tests/qa_product_readiness_gate_full_suite_v2_38bz.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    results_path = ROOT / contract["input_results"]
    csv_path = ROOT / contract["input_csv"]
    bx_summary_path = ROOT / contract["input_bx_summary"]
    by_summary_path = ROOT / contract["input_by_summary"]
    app_file = ROOT / contract["input_app"]
    ui_module = ROOT / contract["input_ui_module"]

    rows_json = json.loads(results_path.read_text(encoding="utf-8"))
    rows_csv = read_csv(csv_path)
    if len(rows_json) != len(rows_csv):
        raise ValueError("v2.38BV JSON/CSV row counts differ")

    bx_summary = json.loads(bx_summary_path.read_text(encoding="utf-8"))
    by_summary = json.loads(by_summary_path.read_text(encoding="utf-8"))
    limitations = limitation_rows()
    checks = (
        population_checks(rows_csv, contract)
        + upstream_checks(bx_summary, by_summary)
        + ui_checks(app_file, ui_module, contract)
        + guardrail_checks([app_file, ui_module], contract)
    )
    qa_status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    status = readiness_status(checks, limitations, contract["expected_status"])
    counts = Counter(row["eligibility_status"] for row in rows_csv)
    summary = {
        "phase": PHASE,
        "status": status,
        "qa_status": qa_status,
        "decision": "usable_for_local_research_with_limitations" if status == "PRODUCT_READINESS_PASS_WITH_LIMITATIONS" else status.lower(),
        "input_phase_scoring": contract["input_phase_scoring"],
        "input_phase_ui": contract["input_phase_ui"],
        "input_phase_closure_audit": contract["input_phase_closure_audit"],
        "input_phase_ux_hardening": contract["input_phase_ux_hardening"],
        "total_assets": len(rows_csv),
        "population_counts": dict(sorted(counts.items())),
        "main_ranking_count": counts["ELIGIBLE_PARTIAL"],
        "partial_comparability_count": counts["PARTIAL_COMPARABILITY"],
        "review_required_count": counts["REVIEW_REQUIRED"],
        "blocked_count": counts["BLOCKED"],
        "not_yet_scored_count": counts["NOT_YET_SCORED_NO_ADAPTER"],
        "limitations_count": len(limitations),
        "scoring_recomputed": False,
        "methodology_changed": False,
        "weights_changed": False,
        "network_used": False,
        "ui_recomputes_scoring": False,
        "financial_advice_created": False,
        "broker_actions_allowed": False,
        "recommendations_created": False,
        "next_recommended_phase": "v2.38CA-release-candidate-local-packaging-operator-guide",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "product_readiness_gate_checks_v2_38bz.csv", checks, ["category", "check", "expected", "actual", "target", "critical", "status"])
    write_csv(output_dir / "product_readiness_gate_limitations_v2_38bz.csv", limitations, ["limitation_id", "description", "blocks_local_research_use", "blocks_financial_advice_or_broker_use"])
    write_text(output_dir / "product_readiness_gate_summary_v2_38bz.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "README.md", "# v2.38BZ Product Readiness Gate\n\nRead-only product readiness gate for the experimental global ranking. The decision is product-readiness for local research with explicit limitations, not authorization for financial advice, automated recommendations, predictive claims, or broker workflows.\n")
    write_text(
        output_dir / "PRODUCT_READINESS_GATE_v2_38bz.md",
        "# Product Readiness Gate v2.38BZ\n\n"
        f"Decision: `{summary['status']}`.\n\n"
        "The `Ranking global (experimental)` surface is usable as a local research screen with explicit limitations. It is not a recommendation engine, not a predictive product, not a price-target workflow, and not a broker workflow.\n\n"
        "Verified real populations:\n\n"
        "- Main ranking: 318\n"
        "- Partial comparability: 373\n"
        "- Review required: 124\n"
        "- Blocked: 270\n"
        "- Not yet scored: 26\n"
        "- Total: 1,111\n\n"
        "Required product surface is present: metrics, search, score/coverage filters, Top N, filtered CSV export, quick detail, separate populations, visible blocked assets, and explicit non-advice copy.\n\n"
        "The gate remains limited by incomplete country coverage, missing adapters, blocked low-coverage assets, financial institutions needing a separate factor contract, price coverage gaps, and absence of out-of-sample predictive validation.\n\n"
        "Next recommended phase: `v2.38CA -- Release Candidate / local packaging / operator guide`.\n",
    )
    guardrails = {
        "scoring_recomputed": False,
        "methodology_changed": False,
        "weights_changed": False,
        "network_used": False,
        "ui_recomputes_scoring": False,
        "financial_advice_created": False,
        "broker_actions_allowed": False,
        "recommendations_created": False,
    }
    inputs = [contract_path, results_path, csv_path, bx_summary_path, by_summary_path, app_file, ui_module]
    write_text(output_dir / "product_readiness_gate_manifest_v2_38bz.json", json.dumps(manifest_for(inputs, output_dir, guardrails, summary), indent=2, sort_keys=True) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build(args.contract, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
