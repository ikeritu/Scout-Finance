
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase8b_ai_equity_research_memo_blueprint_summary.json"
REPORT_PATH = OUT_DIR / "phase8b_ai_equity_research_memo_blueprint_report.md"
MODULE_MATRIX_PATH = OUT_DIR / "phase8b_ai_equity_research_memo_modules_matrix.csv"
DB_SCHEMA_PATH = OUT_DIR / "phase8b_equity_research_memos_table_schema.json"
MEMO_SCHEMA_PATH = ROOT / "schemas" / "equity_research_memo_schema_v0_1.json"

def ok(msg): print(f"OK   {msg}")
def fail(msg): print(f"FAIL {msg}")
def read_json(path):
    if not path.exists(): return {}
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    print("Scout Finance — Phase 8B AI Equity Research Memo Blueprint checker")
    print("=" * 92)
    for path in [SUMMARY_PATH, REPORT_PATH, MODULE_MATRIX_PATH, DB_SCHEMA_PATH, MEMO_SCHEMA_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary, memo_schema, db_schema = read_json(SUMMARY_PATH), read_json(MEMO_SCHEMA_PATH), read_json(DB_SCHEMA_PATH)

    validations = [
        (summary.get("phase") == "8B", "Summary phase is 8B"),
        (summary.get("status") == "OK", "Summary status OK"),
        (summary.get("phase7g_frozen") is True, "v0.7 frozen detected"),
        (summary.get("phase8a_valid") is True, "8A valid detected"),
        (summary.get("default_top_n") == 3, "Default TOP N OK: 3"),
        (summary.get("modules_count") == 8, "Modules count OK: 8"),
        (summary.get("table_name") == "equity_research_memos", "Table name OK"),
    ]
    for passed, message in validations:
        if not passed:
            fail(message)
            return 1
        ok(message)

    matrix_text = MODULE_MATRIX_PATH.read_text(encoding="utf-8")
    for module in ["src/research_memo.py","src/fundamentals.py","src/valuation.py","src/risk_analysis.py","src/moat_analysis.py","src/growth_analysis.py","src/institutional_view.py","src/earnings_analysis.py"]:
        if module not in matrix_text:
            fail(f"Module missing from matrix: {module}")
            return 1
        ok(f"Module in matrix: {module}")

    for field in ["ticker","company_name","memo_status","business_model","financial_health","moat_analysis","valuation_analysis","growth_analysis","risk_analysis","institutional_view","bull_case","base_case","bear_case","final_verdict","confidence","data_gaps","sources","model_used","estimated_cost"]:
        if field not in memo_schema.get("required_fields", []):
            fail(f"Memo schema missing required field: {field}")
            return 1
        ok(f"Memo schema field OK: {field}")

    db_fields = {f.get("name") for f in db_schema.get("fields", [])}
    for field in ["run_id","ticker","company_name","ranking_position","quant_score","memo_status","financial_health_score","moat_score","valuation_score","growth_score","risk_score","institutional_score","data_gaps","objective_data_json","ai_interpretation_json","prompt_version","schema_version","estimated_cost"]:
        if field not in db_fields:
            fail(f"DB schema missing field: {field}")
            return 1
        ok(f"DB schema field OK: {field}")

    controls = summary.get("controls", {})
    for key in ["openai_called","api_called","yfinance_called","app_modified","filters_modified","pipeline_recalculated","release_modified"]:
        if controls.get(key) is not False:
            fail(f"Invalid control {key}: {controls.get(key)}")
            return 1
        ok(f"Control OK: {key}=False")

    before, after = summary.get("signatures_before", {}), summary.get("signatures_after", {})
    for name in ["app.py", "src/filters.py"]:
        if before.get(name) != after.get(name):
            fail(f"Signature changed unexpectedly: {name}")
            return 1
        ok(f"Signature unchanged: {name}")

    report = REPORT_PATH.read_text(encoding="utf-8")
    for text in ["AI Equity Research Memo Blueprint","equity_research_memos","No inventar datos","TOP 3","Risk analysis obligatorio","8C"]:
        if text not in report:
            fail(f"Report missing text: {text}")
            return 1
        ok(f"Report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    ok("Phase 8B AI Equity Research Memo Blueprint is valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
