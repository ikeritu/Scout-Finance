#!/usr/bin/env python3
"""Build deterministic static v2.38M macro/geopolitical context."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38M-macro-geopolitical-context"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38m_macro_geopolitical_context"
SHORTLIST = ROOT / "outputs/full_universe_source_acquisition/v2_38l_us_explained_shortlist/us_explained_shortlist_v2_38l.csv"
SHORTLIST_REPORT = ROOT / "outputs/full_universe_source_acquisition/v2_38l_us_explained_shortlist/us_explained_shortlist_aggregate_report_v2_38l.json"
MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38j_us_candidate_feature_matrix/us_candidate_feature_matrix_v2_38j.csv"
ASOF_DATE = "2026-09-03"

TAXONOMY_FIELDS = [
    "theme_id", "theme_name", "region", "country", "sector_hint",
    "opportunity_score", "risk_score", "confidence_level", "context_summary",
    "data_mode", "asof_date", "source_policy", "phase",
]
CONTEXT_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "shortlist_rank",
    "research_rank", "experimental_score", "shortlist_bucket",
    "macro_context_status", "applicable_themes", "macro_opportunity_score",
    "macro_risk_score", "macro_balance", "macro_context_summary",
    "macro_positive_context", "macro_risk_context", "macro_limitations",
    "next_macro_research_steps", "recommendation_generated", "financial_advice",
    "broker_actions_allowed", "phase9c_authorized", "phase",
]
NOTE_FIELDS = [
    "asset_id", "ticker", "theme_id", "note_type", "note",
    "confidence_level", "source_policy", "phase",
]
QUALITY_FIELDS = [
    "asset_id", "ticker", "macro_context_status", "theme_count",
    "macro_opportunity_score", "macro_risk_score", "macro_balance",
    "quality_notes", "phase",
]
REJECTION_FIELDS = ["asset_id", "ticker", "company_name", "exchange", "reason", "phase"]

GENERAL_THEME_IDS = ["INTEREST_RATES", "INFLATION", "USD_STRENGTH", "SMALL_CAP_LIQUIDITY"]
THEME_KEYWORDS = {
    "AI_SEMICONDUCTORS": ["semiconductor", "chip", "ai ", "artificial intelligence", "data center", "processor"],
    "DEFENSE_SECURITY": ["defense", "aerospace", "security", "military"],
    "ENERGY_TRANSITION": ["solar", "renewable", "battery", "ev ", "electric vehicle", "grid"],
    "OIL_GAS_SUPPLY": ["oil", "gas", "drilling", "pipeline", "energy"],
    "CHINA_US_TENSIONS": ["china", "semiconductor", "chip", "manufacturing", "supply"],
    "SUPPLY_CHAIN_RESILIENCE": ["logistics", "manufacturing", "industrial", "supply", "freight"],
    "CYBERSECURITY": ["cyber", "security software", "identity", "cloud security"],
    "HEALTHCARE_REGULATION": ["health", "medical", "biotech", "pharma", "clinical"],
    "BANK_CREDIT_CYCLE": ["bank", "bancorp", "financial", "credit"],
    "INDUSTRIAL_RESHORING": ["industrial", "manufacturing", "automation", "factory"],
    "EUROPE_REGULATORY_DRAG": ["europe", "gdpr", "regulatory"],
    "CLIMATE_POLICY": ["climate", "emissions", "renewable", "carbon"],
    "COMMODITY_INPUT_COSTS": ["steel", "chemical", "materials", "commodity", "agriculture"],
}


def taxonomy() -> list[dict[str, Any]]:
    rows = [
        theme("INTEREST_RATES", "Interest rates", "GLOBAL", "US", "ALL", 45, 70, "MEDIUM", "Higher or volatile interest rates can affect discount rates, financing costs and risk appetite."),
        theme("INFLATION", "Inflation", "GLOBAL", "US", "ALL", 50, 62, "MEDIUM", "Inflation can pressure input costs and consumer demand while helping some pricing-power businesses."),
        theme("USD_STRENGTH", "US dollar strength", "GLOBAL", "US", "ALL", 48, 55, "LOW", "A stronger dollar can pressure foreign revenue translation and help import-heavy cost bases."),
        theme("AI_SEMICONDUCTORS", "AI and semiconductors", "GLOBAL", "US", "technology semiconductors infrastructure", 78, 58, "MEDIUM", "AI infrastructure demand can be a tailwind for chips, compute, data infrastructure and related suppliers."),
        theme("DEFENSE_SECURITY", "Defense and security", "GLOBAL", "US", "defense aerospace security", 72, 45, "MEDIUM", "Security spending can support selected defense, aerospace and dual-use technology suppliers."),
        theme("ENERGY_TRANSITION", "Energy transition", "GLOBAL", "US", "renewables grid storage electrification", 66, 62, "MEDIUM", "Electrification and grid investment can help some energy-transition suppliers but policy support is uneven."),
        theme("OIL_GAS_SUPPLY", "Oil and gas supply", "GLOBAL", "US", "oil gas energy services", 58, 68, "MEDIUM", "Energy supply volatility can affect producers, services and input-sensitive industries."),
        theme("CHINA_US_TENSIONS", "China-US tensions", "GLOBAL", "US", "china supply chain semiconductors manufacturing", 52, 76, "MEDIUM", "Trade and technology restrictions can reshape supply chains and add geopolitical execution risk."),
        theme("SUPPLY_CHAIN_RESILIENCE", "Supply-chain resilience", "GLOBAL", "US", "logistics manufacturing industrial", 64, 50, "MEDIUM", "Reshoring and supplier diversification can support selected industrial and logistics businesses."),
        theme("CYBERSECURITY", "Cybersecurity", "GLOBAL", "US", "software cyber security", 73, 42, "MEDIUM", "Security demand remains structurally relevant as digital infrastructure expands."),
        theme("HEALTHCARE_REGULATION", "Healthcare regulation", "GLOBAL", "US", "healthcare biotech pharma medical", 55, 72, "MEDIUM", "Healthcare and biotech names face policy, reimbursement and trial/regulatory uncertainty."),
        theme("BANK_CREDIT_CYCLE", "Bank credit cycle", "GLOBAL", "US", "banks financial credit", 44, 74, "MEDIUM", "Credit quality and funding costs can materially affect banks and lenders."),
        theme("SMALL_CAP_LIQUIDITY", "Small-cap liquidity", "GLOBAL", "US", "ALL", 54, 70, "MEDIUM", "Smaller and less liquid equities can be more sensitive to risk appetite and financing conditions."),
        theme("INDUSTRIAL_RESHORING", "Industrial reshoring", "GLOBAL", "US", "industrial manufacturing automation", 68, 48, "MEDIUM", "Domestic manufacturing investment can benefit selected industrial suppliers."),
        theme("EUROPE_REGULATORY_DRAG", "Europe regulatory drag", "EUROPE", "", "europe regulation", 35, 66, "LOW", "European regulatory exposure can add compliance cost, but v2.38M does not classify US issuers into this theme unless evidence exists."),
        theme("CLIMATE_POLICY", "Climate policy", "GLOBAL", "US", "energy climate industrial", 57, 65, "LOW", "Climate policy can create both transition demand and compliance risk depending on business model."),
        theme("COMMODITY_INPUT_COSTS", "Commodity input costs", "GLOBAL", "US", "materials industrial consumer", 42, 69, "MEDIUM", "Commodity cost volatility can pressure margin for input-intensive businesses."),
    ]
    return rows


def theme(theme_id: str, name: str, region: str, country: str, sector_hint: str, opportunity: int, risk: int, confidence: str, summary: str) -> dict[str, Any]:
    return {
        "theme_id": theme_id,
        "theme_name": name,
        "region": region,
        "country": country,
        "sector_hint": sector_hint,
        "opportunity_score": opportunity,
        "risk_score": risk,
        "confidence_level": confidence,
        "context_summary": summary,
        "data_mode": "STATIC_TAXONOMY",
        "asof_date": ASOF_DATE,
        "source_policy": "OFFLINE_STATIC_NO_LIVE_NEWS",
        "phase": PHASE,
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"BLOCKED: required input not found: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fields})


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def as_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def rounded(value: float) -> float:
    return round(value, 4)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def match_themes(shortlist_row: dict[str, str], matrix_row: dict[str, str] | None, themes: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    text = " ".join([
        shortlist_row.get("company_name", ""),
        shortlist_row.get("positive_drivers", ""),
        shortlist_row.get("risk_drivers", ""),
        shortlist_row.get("evidence_summary", ""),
        shortlist_row.get("research_explanation", ""),
        shortlist_row.get("next_research_steps", ""),
        (matrix_row or {}).get("fundamental_signal_summary", ""),
        (matrix_row or {}).get("price_signal_summary", ""),
        (matrix_row or {}).get("risk_signal_summary", ""),
    ]).lower()
    selected_ids = list(GENERAL_THEME_IDS)
    for theme_id, keywords in THEME_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            selected_ids.append(theme_id)
    ordered = []
    seen = set()
    for theme_id in selected_ids:
        if theme_id in themes and theme_id not in seen:
            ordered.append(themes[theme_id])
            seen.add(theme_id)
    limitation = "Sector classification is conservative and derived only from existing local text fields; no live external classification was used."
    if len(ordered) == len(GENERAL_THEME_IDS):
        limitation = "No reliable sector-specific theme was inferred; only general US macro themes were applied."
    return ordered, limitation


def context_status(selected: list[dict[str, Any]], limitation: str) -> str:
    if not selected:
        return "MACRO_CONTEXT_BLOCKED"
    if "only general US macro themes" in limitation:
        return "MACRO_CONTEXT_PARTIAL"
    return "MACRO_CONTEXT_READY"


def mean(values: list[float]) -> float:
    return rounded(sum(values) / len(values)) if values else 0.0


def build(shortlist_path: Path, shortlist_report_path: Path, matrix_path: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    shortlist_rows = read_csv(shortlist_path)
    _ = json.loads(shortlist_report_path.read_text(encoding="utf-8")) if shortlist_report_path.exists() else {}
    matrix_rows = {row.get("asset_id", ""): row for row in read_csv(matrix_path)}
    taxonomy_rows = taxonomy()
    themes = {row["theme_id"]: row for row in taxonomy_rows}

    context_rows: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    quality: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in shortlist_rows:
        asset_id = row.get("asset_id", "")
        ticker = row.get("ticker", "")
        if not asset_id or not ticker or asset_id in seen:
            rejections.append(rejection(row, "duplicate_or_invalid_shortlist_identity"))
            continue
        seen.add(asset_id)
        selected, limitation = match_themes(row, matrix_rows.get(asset_id), themes)
        status = context_status(selected, limitation)
        opportunity = mean([float(t["opportunity_score"]) for t in selected])
        risk = mean([float(t["risk_score"]) for t in selected])
        balance = rounded(opportunity - risk)
        applicable = "|".join(str(t["theme_id"]) for t in selected)
        positive = "; ".join(f"{t['theme_id']}: {t['context_summary']}" for t in selected if float(t["opportunity_score"]) >= float(t["risk_score"]))
        risk_text = "; ".join(f"{t['theme_id']}: {t['context_summary']}" for t in selected if float(t["risk_score"]) > float(t["opportunity_score"]))
        context = {
            "asset_id": asset_id,
            "ticker": ticker,
            "company_name": row.get("company_name", ""),
            "exchange": row.get("exchange", ""),
            "shortlist_rank": row.get("shortlist_rank", ""),
            "research_rank": row.get("research_rank", ""),
            "experimental_score": row.get("experimental_score", ""),
            "shortlist_bucket": row.get("shortlist_bucket", ""),
            "macro_context_status": status,
            "applicable_themes": applicable,
            "macro_opportunity_score": opportunity,
            "macro_risk_score": risk,
            "macro_balance": balance,
            "macro_context_summary": f"Static macro/geopolitical context applied using {len(selected)} taxonomy themes as of {ASOF_DATE}.",
            "macro_positive_context": positive or "No dominant macro tailwind in static taxonomy.",
            "macro_risk_context": risk_text or "No dominant macro headwind in static taxonomy.",
            "macro_limitations": limitation,
            "next_macro_research_steps": "Validate sector exposure manually; add sourced live macro/news layer in a later phase; do not alter the v2.38K/v2.38L rank from this static layer.",
            "recommendation_generated": False,
            "financial_advice": False,
            "broker_actions_allowed": False,
            "phase9c_authorized": False,
            "phase": PHASE,
        }
        context_rows.append(context)
        quality.append({
            "asset_id": asset_id,
            "ticker": ticker,
            "macro_context_status": status,
            "theme_count": len(selected),
            "macro_opportunity_score": opportunity,
            "macro_risk_score": risk,
            "macro_balance": balance,
            "quality_notes": "static_context_ready" if status == "MACRO_CONTEXT_READY" else "general_context_only",
            "phase": PHASE,
        })
        for theme_row in selected:
            note_type = "MACRO_OPPORTUNITY" if float(theme_row["opportunity_score"]) >= float(theme_row["risk_score"]) else "MACRO_RISK"
            notes.append(note(row, str(theme_row["theme_id"]), note_type, str(theme_row["context_summary"]), str(theme_row["confidence_level"])))
            if theme_row["theme_id"] in {"CHINA_US_TENSIONS", "DEFENSE_SECURITY", "EUROPE_REGULATORY_DRAG"}:
                notes.append(note(row, str(theme_row["theme_id"]), "GEOPOLITICAL_EXPOSURE", "Exposure theme requires sourced manual review before investment research conclusions.", str(theme_row["confidence_level"])))
        notes.append(note(row, "", "EVIDENCE_LIMITATION", limitation, "MEDIUM"))
        notes.append(note(row, "", "NEXT_RESEARCH_STEP", "Review sourced macro and sector evidence in the next phase before changing any research priority.", "MEDIUM"))
        notes.append(note(row, "", "LANGUAGE_GUARDRAIL", "Static context only; no final action language or external event claim is generated.", "HIGH"))

    write_csv(output_dir / "macro_geopolitical_taxonomy_v2_38m.csv", TAXONOMY_FIELDS, taxonomy_rows)
    write_csv(output_dir / "us_shortlist_macro_context_v2_38m.csv", CONTEXT_FIELDS, context_rows)
    write_csv(output_dir / "us_shortlist_macro_notes_v2_38m.csv", NOTE_FIELDS, notes)
    write_csv(output_dir / "macro_geopolitical_quality_v2_38m.csv", QUALITY_FIELDS, quality)
    write_csv(output_dir / "macro_geopolitical_rejections_v2_38m.csv", REJECTION_FIELDS, rejections)

    counts = Counter(row["macro_context_status"] for row in context_rows)
    report = {
        "phase": PHASE,
        "status": "COMPLETED_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS",
        "shortlist_assets": len(shortlist_rows),
        "macro_context_ready": counts.get("MACRO_CONTEXT_READY", 0),
        "macro_context_partial": counts.get("MACRO_CONTEXT_PARTIAL", 0),
        "macro_context_review_required": counts.get("MACRO_CONTEXT_REVIEW_REQUIRED", 0),
        "macro_context_blocked": counts.get("MACRO_CONTEXT_BLOCKED", 0),
        "themes_defined": len(taxonomy_rows),
        "notes": len(notes),
        "rejected_rows": len(rejections),
        "live_news_used": False,
        "recommendations_generated": False,
        "guardrails": {
            "network_calls": 0,
            "recommendation_generated": False,
            "recommendations_generated": False,
            "financial_advice": False,
            "broker_actions_allowed": False,
            "phase9c_authorized": False,
            "ranking_modified": False,
            "scoring_modified": False,
            "live_news_used": False,
            "llm_runtime_classification": False,
        },
    }
    (output_dir / "macro_geopolitical_aggregate_report_v2_38m.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    write_docs(output_dir, report)
    write_manifest(output_dir, report)
    print(json.dumps({
        "status": report["status"],
        "shortlist_assets": report["shortlist_assets"],
        "macro_context_ready": report["macro_context_ready"],
        "themes_defined": report["themes_defined"],
        "live_news_used": False,
        "recommendations_generated": False,
    }, sort_keys=True))
    return report


def rejection(row: dict[str, str], reason: str) -> dict[str, str]:
    return {
        "asset_id": row.get("asset_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "exchange": row.get("exchange", ""),
        "reason": reason,
        "phase": PHASE,
    }


def note(row: dict[str, str], theme_id: str, note_type: str, text: str, confidence: str) -> dict[str, str]:
    return {
        "asset_id": row.get("asset_id", ""),
        "ticker": row.get("ticker", ""),
        "theme_id": theme_id,
        "note_type": note_type,
        "note": text,
        "confidence_level": confidence,
        "source_policy": "OFFLINE_STATIC_NO_LIVE_NEWS",
        "phase": PHASE,
    }


def write_docs(output_dir: Path, report: dict[str, Any]) -> None:
    (output_dir / "README.md").write_text("# v2.38M macro/geopolitical context\n\nBuilds a static, offline macro/geopolitical context layer for the v2.38L US research shortlist. It adds taxonomy-based context only; it does not use live news, network calls, runtime LLM classification, broker actions or final recommendation language.\n", encoding="utf-8", newline="\n")
    (output_dir / "MACRO_GEOPOLITICAL_CONTEXT_CONTRACT_v2_38m.md").write_text("# Macro/Geopolitical Context Contract v2.38M\n\nThis phase applies a static taxonomy of macro and geopolitical themes to the US research shortlist. It preserves existing v2.38K scores and v2.38L ranks, exposes limitations, and prepares a later sourced live-context layer.\n", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9M Macro/Geopolitical Gate v2.38M

Status: {report['status']}

- Shortlist assets: {report['shortlist_assets']}
- Macro context ready: {report['macro_context_ready']}
- Macro context partial: {report['macro_context_partial']}
- Themes defined: {report['themes_defined']}
- Notes: {report['notes']}
- Rejected rows: {report['rejected_rows']}

Guardrails: no network calls, no live news, no runtime LLM classification, no ranking/scoring modification, no broker actions and no phase 9C authorization.
"""
    (output_dir / "PHASE9M_MACRO_GEOPOLITICAL_GATE_v2_38m.md").write_text(gate, encoding="utf-8", newline="\n")


def write_manifest(output_dir: Path, report: dict[str, Any]) -> None:
    public = [
        "README.md",
        "MACRO_GEOPOLITICAL_CONTEXT_CONTRACT_v2_38m.md",
        "PHASE9M_MACRO_GEOPOLITICAL_GATE_v2_38m.md",
        "macro_geopolitical_taxonomy_v2_38m.csv",
        "us_shortlist_macro_context_v2_38m.csv",
        "us_shortlist_macro_notes_v2_38m.csv",
        "macro_geopolitical_quality_v2_38m.csv",
        "macro_geopolitical_rejections_v2_38m.csv",
        "macro_geopolitical_aggregate_report_v2_38m.json",
    ]
    manifest = {
        "phase": PHASE,
        "outputs": {name: {"bytes": (output_dir / name).stat().st_size, "sha256": sha256(output_dir / name)} for name in public},
        "guardrails": report["guardrails"],
    }
    (output_dir / "macro_geopolitical_manifest_v2_38m.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shortlist-path", type=Path, default=SHORTLIST)
    parser.add_argument("--shortlist-report-path", type=Path, default=SHORTLIST_REPORT)
    parser.add_argument("--matrix-path", type=Path, default=MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    build(args.shortlist_path, args.shortlist_report_path, args.matrix_path, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
