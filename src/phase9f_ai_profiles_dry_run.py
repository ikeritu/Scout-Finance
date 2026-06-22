from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


PHASE = "9F"
TITLE = "AI Profiles Dry-run Prompt Packaging"
SCHEMA_VERSION = "ai_profiles_dry_run_v0_1"
DEFAULT_TOP_N = 3
MAX_TOP_N = 3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_SCOUTING_DIR = PROJECT_ROOT / "outputs" / "scouting"
MEMO_9E_EXPORT = OUTPUTS_SCOUTING_DIR / "phase9e_memo_v2_red_flags_export.json"
PROMPT_DIR = OUTPUTS_SCOUTING_DIR / "ai_profiles_dry_run"

CONTROL_FLAGS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "app_modified": False,
    "filters_modified": False,
    "release_modified": False,
}

AI_PROFILES = [
    {
        "profile_id": "value_analyst",
        "display_name": "Value Analyst",
        "purpose": "Review valuation, margin of safety, downside risk and valuation uncertainty.",
        "must_focus_on": [
            "valuation_score",
            "quant_score",
            "red_flags related to valuation",
            "data gaps that prevent valuation confidence",
        ],
    },
    {
        "profile_id": "quality_analyst",
        "display_name": "Quality Analyst",
        "purpose": "Review business quality, margins, cash generation and durability.",
        "must_focus_on": [
            "operating margin",
            "FCF margin",
            "moat/business quality",
            "financial deterioration",
        ],
    },
    {
        "profile_id": "risk_analyst",
        "display_name": "Risk Analyst",
        "purpose": "Review financial, data quality, dilution, leverage and execution risks.",
        "must_focus_on": [
            "debt",
            "dilution",
            "risk score",
            "data quality",
            "high/critical red flags",
        ],
    },
    {
        "profile_id": "skeptic_analyst",
        "display_name": "Skeptic Analyst",
        "purpose": "Challenge the memo, identify weak assumptions and prevent false confidence.",
        "must_focus_on": [
            "why the candidate should not be promoted",
            "missing evidence",
            "contradictions",
            "overconfidence",
            "NEEDS_MORE_DATA conditions",
        ],
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = []
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def compact_memo_context(memo: Dict[str, Any]) -> Dict[str, Any]:
    red_flags = memo.get("red_flags", {})
    red_summary = red_flags.get("summary", {})
    red_items = red_flags.get("items", [])

    return {
        "ticker": memo.get("ticker"),
        "company_name": memo.get("company_name"),
        "ranking_position": memo.get("ranking_position"),
        "quant_score": memo.get("quant_score"),
        "normalized_verdict": memo.get("normalized_verdict"),
        "manual_review_required": memo.get("manual_review_required"),
        "not_financial_advice": memo.get("not_financial_advice"),
        "objective_data": memo.get("objective_data", {}),
        "deterministic_analysis": memo.get("deterministic_analysis", {}),
        "data_gaps": memo.get("data_gaps", []),
        "sources": memo.get("sources", []),
        "red_flags_summary": red_summary,
        "red_flags": red_items,
        "verdict_policy": memo.get("verdict_policy", {}),
    }


def build_prompt_package(memo: Dict[str, Any], profile: Dict[str, Any], index: int) -> Dict[str, Any]:
    context = compact_memo_context(memo)
    ticker = str(context.get("ticker") or f"UNKNOWN_{index}").upper()

    system_prompt = (
        "You are a constrained research-review profile inside Scout Finance. "
        "You must not give financial advice. You must not use buy/sell language. "
        "You must not invent missing facts. If evidence is insufficient, say NEEDS_MORE_DATA. "
        "You only review the provided local context."
    )

    user_prompt = {
        "task": "Review this Scout Finance memo from the perspective of the assigned profile.",
        "profile": {
            "id": profile["profile_id"],
            "name": profile["display_name"],
            "purpose": profile["purpose"],
            "must_focus_on": profile["must_focus_on"],
        },
        "required_output_contract": {
            "profile_id": profile["profile_id"],
            "ticker": ticker,
            "verdict": "WATCHLIST | REJECT | NEEDS_MORE_DATA",
            "confidence": "LOW | MEDIUM | HIGH",
            "main_observations": ["string"],
            "blocking_questions": ["string"],
            "red_flags_to_prioritize": ["string"],
            "data_needed_before_decision": ["string"],
            "not_financial_advice": True,
            "manual_review_required": True,
        },
        "memo_context": context,
    }

    package = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "created_at": utc_now(),
        "dry_run_only": True,
        "execution_allowed": False,
        "profile_id": profile["profile_id"],
        "profile_name": profile["display_name"],
        "ticker": ticker,
        "company_name": context.get("company_name"),
        "source_file": str(MEMO_9E_EXPORT.relative_to(PROJECT_ROOT)),
        "system_prompt": system_prompt,
        "user_prompt_json": user_prompt,
        "safety": {
            "openai_called": False,
            "api_called": False,
            "yfinance_called": False,
            "pipeline_recalculated": False,
            "estimated_cost": 0.0,
            "model_used": None,
            "not_financial_advice": True,
            "manual_review_required": True,
        },
    }
    package["prompt_package_sha256"] = sha256_payload(package)
    return package


def package_markdown(package: Dict[str, Any]) -> str:
    lines = [
        f"# AI Profile Dry-run Package — {package['ticker']} — {package['profile_name']}",
        "",
        f"- Profile: **{package['profile_name']}**",
        f"- Ticker: **{package['ticker']}**",
        f"- Company: **{package['company_name']}**",
        f"- Dry-run only: `{package['dry_run_only']}`",
        f"- Execution allowed: `{package['execution_allowed']}`",
        f"- OpenAI called: `{package['safety']['openai_called']}`",
        f"- API called: `{package['safety']['api_called']}`",
        f"- yfinance called: `{package['safety']['yfinance_called']}`",
        f"- Pipeline recalculated: `{package['safety']['pipeline_recalculated']}`",
        f"- Estimated cost: `{package['safety']['estimated_cost']}`",
        f"- Model used: `{package['safety']['model_used']}`",
        "",
        "## System prompt",
        "",
        "```text",
        package["system_prompt"],
        "```",
        "",
        "## User prompt JSON",
        "",
        "```json",
        json.dumps(package["user_prompt_json"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Safety",
        "",
        "```json",
        json.dumps(package["safety"], indent=2, ensure_ascii=False),
        "```",
        "",
    ]
    return "\n".join(lines)


def write_index_csv(path: Path, packages: List[Dict[str, Any]]) -> None:
    fields = [
        "ticker",
        "company_name",
        "profile_id",
        "profile_name",
        "dry_run_only",
        "execution_allowed",
        "openai_called",
        "api_called",
        "yfinance_called",
        "pipeline_recalculated",
        "estimated_cost",
        "model_used",
        "prompt_package_sha256",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for package in packages:
            safety = package["safety"]
            writer.writerow({
                "ticker": package["ticker"],
                "company_name": package["company_name"],
                "profile_id": package["profile_id"],
                "profile_name": package["profile_name"],
                "dry_run_only": package["dry_run_only"],
                "execution_allowed": package["execution_allowed"],
                "openai_called": safety["openai_called"],
                "api_called": safety["api_called"],
                "yfinance_called": safety["yfinance_called"],
                "pipeline_recalculated": safety["pipeline_recalculated"],
                "estimated_cost": safety["estimated_cost"],
                "model_used": safety["model_used"],
                "prompt_package_sha256": package["prompt_package_sha256"],
            })


def write_report(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# Phase 9F — AI Profiles Dry-run Prompt Packaging",
        "",
        "Status: **OK**",
        "",
        "## Summary",
        "",
        f"- Memos loaded: {summary['memos_loaded']}",
        f"- Profiles: {summary['profile_count']}",
        f"- Prompt packages created: {summary['prompt_packages_created']}",
        f"- Dry-run only: `{summary['dry_run_only_all']}`",
        f"- Execution allowed: `{summary['execution_allowed_any']}`",
        "",
        "## Profiles",
        "",
    ]
    for profile in AI_PROFILES:
        lines.append(f"- `{profile['profile_id']}` — {profile['display_name']}")

    lines.extend([
        "",
        "## Safety controls",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "- app.py modified: False",
        "- filters modified: False",
        "- release modified: False",
        "",
        "## Policy",
        "",
        "- This phase creates prompt packages only.",
        "- It does not execute OpenAI.",
        "- It does not add autonomous agents.",
        "- It does not change any verdict.",
        "- It does not provide financial advice.",
        "",
        "## Next",
        "",
        "Proceed to Phase 9G — v0.9 experimental audit/freeze.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUTS_SCOUTING_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)

    memos_raw = read_json(MEMO_9E_EXPORT, [])
    memos = [m for m in memos_raw if isinstance(m, dict)][:MAX_TOP_N]

    packages: List[Dict[str, Any]] = []
    for memo_index, memo in enumerate(memos, start=1):
        ticker = str(memo.get("ticker") or f"UNKNOWN_{memo_index}").upper()
        for profile in AI_PROFILES:
            package = build_prompt_package(memo, profile, memo_index)
            packages.append(package)
            stem = f"ai_profile_prompt_{memo_index:02d}_{ticker}_{profile['profile_id']}"
            write_json(PROMPT_DIR / f"{stem}.json", package)
            (PROMPT_DIR / f"{stem}.md").write_text(package_markdown(package), encoding="utf-8")

    export_json = OUTPUTS_SCOUTING_DIR / "phase9f_ai_profiles_dry_run_export.json"
    index_csv = OUTPUTS_SCOUTING_DIR / "phase9f_ai_profiles_dry_run_index.csv"
    summary_json = OUTPUTS_SCOUTING_DIR / "phase9f_ai_profiles_dry_run_summary.json"
    audit_json = OUTPUTS_SCOUTING_DIR / "phase9f_ai_profiles_dry_run_audit.json"
    report_md = OUTPUTS_SCOUTING_DIR / "phase9f_ai_profiles_dry_run_report.md"

    write_json(export_json, packages)
    write_index_csv(index_csv, packages)

    summary = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": utc_now(),
        "schema_version": SCHEMA_VERSION,
        "default_top_n": DEFAULT_TOP_N,
        "max_top_n": MAX_TOP_N,
        "source_file": str(MEMO_9E_EXPORT.relative_to(PROJECT_ROOT)),
        "memos_loaded": len(memos),
        "profile_count": len(AI_PROFILES),
        "profiles": [profile["profile_id"] for profile in AI_PROFILES],
        "prompt_packages_created": len(packages),
        "expected_prompt_packages": len(memos) * len(AI_PROFILES),
        "dry_run_only_all": all(package["dry_run_only"] is True for package in packages),
        "execution_allowed_any": any(package["execution_allowed"] is True for package in packages),
        "export_json": str(export_json),
        "index_csv": str(index_csv),
        "prompt_dir": str(PROMPT_DIR),
        **CONTROL_FLAGS,
        "estimated_cost": 0.0,
        "model_used": None,
        "next": "Phase 9G — v0.9 experimental audit/freeze",
    }

    audit = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": summary["created_at"],
        "summary": summary,
        "packages": packages,
    }

    write_json(summary_json, summary)
    write_json(audit_json, audit)
    write_report(report_md, summary)

    print("Scout Finance — Phase 9F AI Profiles Dry-run Prompt Packaging")
    print("=" * 92)
    print()
    print("Dry-run")
    print("-" * 92)
    print("Status: OK")
    print(f"Memos loaded: {summary['memos_loaded']}")
    print(f"Profiles: {summary['profile_count']}")
    print(f"Prompt packages created: {summary['prompt_packages_created']}")
    print(f"Dry-run only all: {summary['dry_run_only_all']}")
    print(f"Execution allowed any: {summary['execution_allowed_any']}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print("Estimated cost: 0.0")
    print("Model used: None")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 9F AI Profiles Dry-run Prompt Packaging is complete.")


if __name__ == "__main__":
    main()
