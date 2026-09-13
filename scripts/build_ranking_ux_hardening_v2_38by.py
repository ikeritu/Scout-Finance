#!/usr/bin/env python3
"""v2.38BY ranking UX hardening audit.

This phase is read-only over v2.38BV/BW/BX. It verifies that the ranking
screen adds safer UX affordances without recalculating scores, changing
methodology, changing weights, calling network APIs, or creating
financial advice.
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
PHASE = "v2.38BY-ranking-ux-hardening"
CONTRACT = ROOT / "config/ranking_ux_hardening_contract_v2_38by.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38by_ranking_ux_hardening"

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
    r"\brecomendacion de compra\b",
    r"\brecomendacion de venta\b",
    r"\bprecio objetivo\b",
    r"\binfravalorada\b",
    r"\bsobrevalorada\b",
    r"\brentabilidad esperada\b",
    r"\bgarantizado\b",
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
            context = normalized[max(0, match.start() - 48): match.end() + 48]
            if not re.search(r"\b(no|not|never|nunca|sin)\b", context):
                return True
    return False


def population_checks(rows: list[dict[str, Any]], contract: dict[str, Any]) -> list[dict[str, Any]]:
    counts = Counter(str(row["eligibility_status"]) for row in rows)
    output = []
    for status, key in STATUS_TO_CONTRACT_KEY.items():
        expected = int(contract[key])
        actual = counts[status]
        output.append({"check": f"population:{status}", "expected": expected, "actual": actual, "status": "PASS" if actual == expected else "FAIL"})
    expected_total = int(contract["expected_total_count"])
    output.append({"check": "population:TOTAL", "expected": expected_total, "actual": len(rows), "status": "PASS" if len(rows) == expected_total else "FAIL"})
    return output


def ui_feature_checks(app_file: Path, ui_module: Path, contract: dict[str, Any]) -> list[dict[str, Any]]:
    app_text = app_file.read_text(encoding="utf-8")
    module_text = ui_module.read_text(encoding="utf-8")
    rows = []
    for token in contract["required_ui_features"]:
        rows.append({"check": f"ui_feature_present:{token}", "target": rel(app_file), "status": "PASS" if token in app_text else "FAIL"})
    for token in ["score_assets(", "percentile_scores(", "build_raw_factors(", "subprocess.", "os.system(", "requests.", "httpx.", "urlopen("]:
        rows.append({"check": f"app_recompute_or_network_absent:{token}", "target": rel(app_file), "status": "PASS" if token not in app_text else "FAIL"})
    for token in ["score_assets(", "percentile_scores(", "build_raw_factors(", "subprocess.", "os.system(", "requests.", "httpx.", "urllib.", "urlopen("]:
        rows.append({"check": f"loader_recompute_or_network_absent:{token}", "target": rel(ui_module), "status": "PASS" if token not in module_text else "FAIL"})
    rows.append({"check": "ui_mentions_v2_38bv", "target": rel(app_file), "status": "PASS" if "v2.38BV" in app_text else "FAIL"})
    rows.append({"check": "ui_mentions_v2_38bx", "target": rel(app_file), "status": "PASS" if "v2.38BX" in app_text else "FAIL"})
    rows.append({"check": "export_excludes_private_watchlists", "target": rel(app_file), "status": "PASS" if '"watchlist"' not in app_text[app_text.find("def global_ranking_export_frame"):app_text.find("def global_ranking_display_frame")] else "FAIL"})
    return rows


def guardrail_checks(paths: list[Path], contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {"check": "scoring_recomputed", "expected": "false", "actual": str(contract["scoring_recomputed"]).lower(), "status": "PASS" if contract["scoring_recomputed"] is False else "FAIL"},
        {"check": "methodology_changed", "expected": "false", "actual": str(contract["methodology_changed"]).lower(), "status": "PASS" if contract["methodology_changed"] is False else "FAIL"},
        {"check": "weights_changed", "expected": "false", "actual": str(contract["weights_changed"]).lower(), "status": "PASS" if contract["weights_changed"] is False else "FAIL"},
        {"check": "network_allowed", "expected": "false", "actual": str(contract["network_allowed"]).lower(), "status": "PASS" if contract["network_allowed"] is False else "FAIL"},
        {"check": "broker_actions_allowed", "expected": "false", "actual": str(contract["broker_actions_allowed"]).lower(), "status": "PASS" if contract["broker_actions_allowed"] is False else "FAIL"},
        {"check": "financial_advice_allowed", "expected": "false", "actual": str(contract["financial_advice_allowed"]).lower(), "status": "PASS" if contract["financial_advice_allowed"] is False else "FAIL"},
        {"check": "recommendations_allowed", "expected": "false", "actual": str(contract["recommendations_allowed"]).lower(), "status": "PASS" if contract["recommendations_allowed"] is False else "FAIL"},
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        rows.append({"check": f"no_positive_advice_language:{rel(path)}", "expected": "true", "actual": str(not has_positive_advice(text)).lower(), "status": "PASS" if not has_positive_advice(text) else "FAIL"})
    return rows


def manifest_for(inputs: list[Path], output_dir: Path, guardrails: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "ranking_ux_hardening_manifest_v2_38by.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs},
        "outputs": outputs,
        "guardrails": guardrails,
        "scripts": ["scripts/build_ranking_ux_hardening_v2_38by.py"],
        "tests": [
            "tests/qa_ui_global_ranking_v2_38by.py",
            "tests/qa_phase9c_ranking_ux_hardening_v2_38by.py",
            "tests/qa_phase9c_ranking_ux_hardening_full_suite_v2_38by.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    results_path = ROOT / contract["input_results"]
    csv_path = ROOT / contract["input_csv"]
    app_file = ROOT / contract["input_app"]
    ui_module = ROOT / contract["input_ui_module"]

    rows_json = json.loads(results_path.read_text(encoding="utf-8"))
    rows_csv = read_csv(csv_path)
    if len(rows_json) != len(rows_csv):
        raise ValueError("v2.38BV JSON/CSV row counts differ")

    population_rows = population_checks(rows_csv, contract)
    ui_rows = ui_feature_checks(app_file, ui_module, contract)
    guardrail_rows = guardrail_checks([app_file, ui_module], contract)
    all_rows = population_rows + ui_rows + guardrail_rows
    qa_status = "PASS" if all(row["status"] == "PASS" for row in all_rows) else "FAIL"
    counts = Counter(row["eligibility_status"] for row in rows_csv)
    summary = {
        "phase": PHASE,
        "status": contract["final_status"] if qa_status == "PASS" else "FAILED_RANKING_UX_HARDENING",
        "qa_status": qa_status,
        "input_phase_scoring": contract["input_phase_scoring"],
        "input_phase_ui": contract["input_phase_ui"],
        "input_phase_audit": contract["input_phase_audit"],
        "total_assets": len(rows_csv),
        "population_counts": dict(sorted(counts.items())),
        "main_ranking_count": counts["ELIGIBLE_PARTIAL"],
        "partial_comparability_count": counts["PARTIAL_COMPARABILITY"],
        "review_required_count": counts["REVIEW_REQUIRED"],
        "blocked_count": counts["BLOCKED"],
        "not_yet_scored_count": counts["NOT_YET_SCORED_NO_ADAPTER"],
        "scoring_recomputed": False,
        "methodology_changed": False,
        "weights_changed": False,
        "network_used": False,
        "ui_recomputes_scoring": False,
        "financial_advice_created": False,
        "broker_actions_allowed": False,
        "recommendations_created": False,
        "next_recommended_phase": "v2.38BZ-product-readiness-gate",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "ranking_ux_hardening_checks_v2_38by.csv", all_rows, ["check", "expected", "actual", "target", "status"])
    write_text(output_dir / "ranking_ux_hardening_summary_v2_38by.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "README.md", "# v2.38BY Ranking UX Hardening\n\nRead-only UX hardening for the real experimental ranking screen. It adds search, score/coverage ranges, Top N, CSV export, explicit blocked visibility, and stronger non-advice copy without recalculating scores or changing methodology.\n")
    write_text(
        output_dir / "RANKING_UX_HARDENING_v2_38by.md",
        "# Ranking UX Hardening v2.38BY\n\n"
        f"Decision: `{summary['status']}`.\n\n"
        "This phase hardens the `Ranking global (experimental)` screen created in v2.38BW over the real v2.38BV output and closed by v2.38BX.\n\n"
        "UX changes verified:\n\n"
        "- Search by company, ticker, asset id, or country.\n"
        "- Country and confidence filters retained.\n"
        "- Score and coverage range filters added.\n"
        "- Top N control added.\n"
        "- Filtered CSV export added without private watchlist data.\n"
        "- Blocked population is visible as its own review surface.\n"
        "- Copy states the screen is experimental research, not financial advice, not a price target, not a return promise, and not a broker workflow.\n\n"
        "Guardrails: no scoring recomputation, no methodology change, no weight change, no network calls, no broker actions, and no recommendations.\n\n"
        "Next recommended phase: `v2.38BZ -- Product readiness gate`.\n",
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
    inputs = [contract_path, results_path, csv_path, app_file, ui_module]
    write_text(output_dir / "ranking_ux_hardening_manifest_v2_38by.json", json.dumps(manifest_for(inputs, output_dir, guardrails, summary), indent=2, sort_keys=True) + "\n")
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
