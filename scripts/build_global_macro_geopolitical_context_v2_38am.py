#!/usr/bin/env python3
"""Build deterministic static v2.38AM global macro/geopolitical context.

v2.38M built this same idea -- a static, offline, keyword-matched taxonomy
of macro/geopolitical themes -- but only ever applied it to the old
50-company US "explained shortlist" (v2.38L), because that was the only
population that existed at the time. Since then this pipeline has grown a
real, identity-resolved population that spans far more than the US: the
v2.38AL global coverage matrix now tracks 1,244 companies with a real,
verified identity (555 US via SEC CIK matching, 689 Europe via Xetra/GLEIF).
This script generalizes v2.38M's engine to that whole population, the same
way this project has repeatedly generalized narrow country-specific work
(GLEIF identity resolution, the fundamentals concept-alias system) once a
second real case showed the original scope was too narrow.

Two real, honest limitations carried forward from v2.38M, made explicit
rather than hidden:

1. Sector-keyword matching depends on descriptive text. The US population
   has real narrative fields (v2.38J's fundamental/price/risk signal
   summaries); Europe's fundamentals extraction never captured anything
   like that, so Europe's sector-theme matching relies on company_name
   text alone -- weaker, and reported as such via macro_limitations.
2. This is a STATIC_TAXONOMY, offline, with no live news and no runtime
   LLM classification -- exactly v2.38M's own discipline, preserved
   unchanged. The new country-specific themes added here (EU single-market
   regulation, Eurozone monetary policy, UK post-Brexit trade friction,
   Swiss franc safe-haven dynamics) are evergreen structural facts about
   these jurisdictions, not time-specific claims about current events --
   the same distinction v2.38M's own existing themes (interest rates,
   inflation, USD strength) already relied on.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import lzma
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38AM-global-macro-geopolitical-context"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38am_global_macro_geopolitical_context"
COVERAGE_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38al_global_coverage_matrix/global_coverage_matrix_v2_38al.csv.xz"
US_SIGNAL_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38j_us_candidate_feature_matrix/us_candidate_feature_matrix_v2_38j.csv"
GB_SIC_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38an_europe_gb_sic_codes/europe_gb_sic_codes_v2_38an.csv"
FRANCE_SECTOR_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ao_europe_france_sector_codes/europe_france_sector_codes_v2_38ao.csv"
NETHERLANDS_SECTOR_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38aq_europe_netherlands_wikidata_sector/europe_netherlands_wikidata_sector_v2_38aq.csv"
ASOF_DATE = "2026-09-06"

# Real, stable, uncontroversial EU/Eurozone membership as of this project's
# real in-scope Europe country list (v2.38AB, 13 countries, 689 assets).
# These are geographic/political facts, not time-sensitive claims.
EU_MEMBER_COUNTRIES = {"DE", "FR", "NL", "IT", "AT", "BE", "ES", "IE", "FI", "SE", "DK"}
EUROZONE_COUNTRIES = {"DE", "FR", "NL", "IT", "AT", "BE", "ES", "IE", "FI"}  # EU members that actually use the euro; SE/DK keep their own currencies

TAXONOMY_FIELDS = [
    "theme_id", "theme_name", "region", "applies_countries", "sector_hint",
    "opportunity_score", "risk_score", "confidence_level", "context_summary",
    "data_mode", "asof_date", "source_policy", "phase",
]
CONTEXT_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "country",
    "identity_status", "overall_coverage_status", "sector_text_source",
    "macro_context_status", "applicable_themes", "macro_opportunity_score",
    "macro_risk_score", "macro_balance", "macro_context_summary",
    "macro_positive_context", "macro_risk_context", "macro_limitations",
    "next_macro_research_steps", "recommendation_generated", "financial_advice",
    "broker_actions_allowed", "phase9c_authorized", "phase",
]
NOTE_FIELDS = ["asset_id", "ticker", "theme_id", "note_type", "note", "confidence_level", "source_policy", "phase"]
QUALITY_FIELDS = ["asset_id", "ticker", "country", "macro_context_status", "theme_count", "macro_opportunity_score", "macro_risk_score", "macro_balance", "quality_notes", "phase"]
REJECTION_FIELDS = ["asset_id", "ticker", "company_name", "country", "reason", "phase"]

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
    "CONSTRUCTION_INFRASTRUCTURE": ["construction", "bau", "infrastructure", "cement", "porr", "strabag"],
    "CLIMATE_POLICY": ["climate", "emissions", "renewable", "carbon"],
    "COMMODITY_INPUT_COSTS": ["steel", "chemical", "materials", "commodity", "agriculture"],
}


def taxonomy() -> list[dict[str, Any]]:
    return [
        theme("INTEREST_RATES", "Interest rates", "GLOBAL", "ALL", "ALL", 45, 70, "MEDIUM", "Higher or volatile interest rates can affect discount rates, financing costs and risk appetite worldwide."),
        theme("INFLATION", "Inflation", "GLOBAL", "ALL", "ALL", 50, 62, "MEDIUM", "Inflation can pressure input costs and consumer demand while helping some pricing-power businesses."),
        theme("USD_STRENGTH", "US dollar strength", "GLOBAL", "ALL", "ALL", 48, 55, "LOW", "A stronger dollar can pressure foreign-revenue translation for non-US exporters and help import-heavy cost bases."),
        theme("AI_SEMICONDUCTORS", "AI and semiconductors", "GLOBAL", "ALL", "technology semiconductors infrastructure", 78, 58, "MEDIUM", "AI infrastructure demand can be a tailwind for chips, compute, data infrastructure and related suppliers."),
        theme("DEFENSE_SECURITY", "Defense and security", "GLOBAL", "ALL", "defense aerospace security", 72, 45, "MEDIUM", "Security spending can support selected defense, aerospace and dual-use technology suppliers."),
        theme("ENERGY_TRANSITION", "Energy transition", "GLOBAL", "ALL", "renewables grid storage electrification", 66, 62, "MEDIUM", "Electrification and grid investment can help some energy-transition suppliers but policy support is uneven."),
        theme("OIL_GAS_SUPPLY", "Oil and gas supply", "GLOBAL", "ALL", "oil gas energy services", 58, 68, "MEDIUM", "Energy supply volatility can affect producers, services and input-sensitive industries."),
        theme("CHINA_US_TENSIONS", "China-US tensions", "GLOBAL", "ALL", "china supply chain semiconductors manufacturing", 52, 76, "MEDIUM", "Trade and technology restrictions can reshape supply chains and add geopolitical execution risk for companies with China exposure, wherever they are listed."),
        theme("SUPPLY_CHAIN_RESILIENCE", "Supply-chain resilience", "GLOBAL", "ALL", "logistics manufacturing industrial", 64, 50, "MEDIUM", "Reshoring and supplier diversification can support selected industrial and logistics businesses."),
        theme("CYBERSECURITY", "Cybersecurity", "GLOBAL", "ALL", "software cyber security", 73, 42, "MEDIUM", "Security demand remains structurally relevant as digital infrastructure expands."),
        theme("HEALTHCARE_REGULATION", "Healthcare regulation", "GLOBAL", "ALL", "healthcare biotech pharma medical", 55, 72, "MEDIUM", "Healthcare and biotech names face policy, reimbursement and trial/regulatory uncertainty."),
        theme("BANK_CREDIT_CYCLE", "Bank credit cycle", "GLOBAL", "ALL", "banks financial credit", 44, 74, "MEDIUM", "Credit quality and funding costs can materially affect banks and lenders."),
        theme("SMALL_CAP_LIQUIDITY", "Small-cap liquidity", "GLOBAL", "ALL", "ALL", 54, 70, "MEDIUM", "Smaller and less liquid equities can be more sensitive to risk appetite and financing conditions."),
        theme("INDUSTRIAL_RESHORING", "Industrial reshoring", "GLOBAL", "ALL", "industrial manufacturing automation", 68, 48, "MEDIUM", "Domestic manufacturing investment can benefit selected industrial suppliers."),
        theme("CONSTRUCTION_INFRASTRUCTURE", "Construction and infrastructure", "GLOBAL", "ALL", "construction infrastructure cement", 60, 55, "MEDIUM", "Public and private infrastructure investment cycles can support construction and building-materials suppliers, but are sensitive to financing costs."),
        theme("CLIMATE_POLICY", "Climate policy", "GLOBAL", "ALL", "energy climate industrial", 57, 65, "LOW", "Climate policy can create both transition demand and compliance risk depending on business model."),
        theme("COMMODITY_INPUT_COSTS", "Commodity input costs", "GLOBAL", "ALL", "materials industrial consumer", 42, 69, "MEDIUM", "Commodity cost volatility can pressure margin for input-intensive businesses."),
        theme("EU_SINGLE_MARKET_REGULATION", "EU single-market regulation", "EUROPE", "|".join(sorted(EU_MEMBER_COUNTRIES)), "ALL", 40, 58, "MEDIUM", "EU-wide rules (competition, data protection, sustainability disclosure) add compliance cost but also create a large harmonized market -- a structural condition of EU membership, not a dated event."),
        theme("EUROZONE_ECB_MONETARY_POLICY", "Eurozone monetary policy", "EUROPE", "|".join(sorted(EUROZONE_COUNTRIES)), "ALL", 45, 62, "MEDIUM", "Eurozone companies are exposed to ECB policy specifically, which can diverge from the US Federal Reserve cycle -- a structural fact of sharing the euro, not a dated event."),
        theme("UK_POST_BREXIT_TRADE_FRICTION", "UK post-Brexit trade friction", "EUROPE", "GB", "ALL", 38, 60, "MEDIUM", "Customs and regulatory divergence from the EU single market since Brexit is a structural, ongoing condition for UK-domiciled companies trading with the EU."),
        theme("CHF_SAFE_HAVEN_DYNAMICS", "Swiss franc safe-haven dynamics", "EUROPE", "CH", "ALL", 42, 50, "LOW", "The Swiss franc's structural role as a safe-haven currency can pressure export competitiveness for Swiss issuers during periods of global risk aversion."),
    ]


def theme(theme_id: str, name: str, region: str, applies_countries: str, sector_hint: str, opportunity: int, risk: int, confidence: str, summary: str) -> dict[str, Any]:
    return {
        "theme_id": theme_id, "theme_name": name, "region": region, "applies_countries": applies_countries,
        "sector_hint": sector_hint, "opportunity_score": opportunity, "risk_score": risk,
        "confidence_level": confidence, "context_summary": summary, "data_mode": "STATIC_TAXONOMY",
        "asof_date": ASOF_DATE, "source_policy": "OFFLINE_STATIC_NO_LIVE_NEWS", "phase": PHASE,
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_coverage(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"BLOCKED: required v2.38AL global coverage matrix not found: {path}")
    opener = lzma.open if path.suffix == ".xz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_csv_index(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {row["asset_id"]: row for row in csv.DictReader(f)}


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fields})
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def rounded(value: float) -> float:
    return round(value, 4)


def mean(values: list[float]) -> float:
    return rounded(sum(values) / len(values)) if values else 0.0


def match_themes(company_name: str, extra_text: str, country: str, themes: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], str, bool]:
    text = f"{company_name} {extra_text}".lower()
    selected_ids = list(GENERAL_THEME_IDS)
    sector_matched = False
    for theme_id, keywords in THEME_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            selected_ids.append(theme_id)
            sector_matched = True
    if country in EU_MEMBER_COUNTRIES:
        selected_ids.append("EU_SINGLE_MARKET_REGULATION")
    if country in EUROZONE_COUNTRIES:
        selected_ids.append("EUROZONE_ECB_MONETARY_POLICY")
    if country == "GB":
        selected_ids.append("UK_POST_BREXIT_TRADE_FRICTION")
    if country == "CH":
        selected_ids.append("CHF_SAFE_HAVEN_DYNAMICS")
    ordered, seen = [], set()
    for theme_id in selected_ids:
        if theme_id in themes and theme_id not in seen:
            ordered.append(themes[theme_id])
            seen.add(theme_id)
    if not extra_text and not sector_matched:
        limitation = "No narrative signal text is available for this company (Europe's fundamentals extraction never captured descriptive text); sector classification relied on company_name keywords only, and none matched."
    elif not sector_matched:
        limitation = "No sector-specific theme was inferred from available text; only general macro themes and any country-specific structural themes were applied."
    elif not extra_text:
        limitation = "Sector classification is based on company_name keywords only (no narrative signal text available for this company); confirm sector fit manually."
    else:
        limitation = "Sector classification is conservative and derived only from existing local text fields; no live external classification was used."
    return ordered, limitation, sector_matched


def context_status(sector_matched: bool) -> str:
    return "MACRO_CONTEXT_READY" if sector_matched else "MACRO_CONTEXT_PARTIAL"


def build(coverage_path: Path, us_signal_path: Path, gb_sic_path: Path, france_sector_path: Path, netherlands_sector_path: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    coverage_rows = read_coverage(coverage_path)
    us_signal_idx = read_csv_index(us_signal_path)
    gb_sic_idx = read_csv_index(gb_sic_path)
    france_sector_idx = read_csv_index(france_sector_path)
    netherlands_sector_idx = read_csv_index(netherlands_sector_path)
    taxonomy_rows = taxonomy()
    themes = {row["theme_id"]: row for row in taxonomy_rows}

    context_rows: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    quality: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    seen: set[str] = set()

    identity_resolved = [r for r in coverage_rows if r.get("identity_status") == "RESOLVED"]
    for row in identity_resolved:
        asset_id = row.get("asset_id", "")
        ticker = row.get("ticker", "")
        company_name = row.get("company_name", "")
        country = row.get("country", "")
        if not asset_id or not company_name or asset_id in seen:
            rejections.append({"asset_id": asset_id, "ticker": ticker, "company_name": company_name, "country": country, "reason": "duplicate_or_invalid_identity", "phase": PHASE})
            continue
        seen.add(asset_id)
        signal_row = us_signal_idx.get(asset_id)
        gb_sic_row = gb_sic_idx.get(asset_id)
        france_sector_row = france_sector_idx.get(asset_id)
        netherlands_sector_row = netherlands_sector_idx.get(asset_id)
        extra_text_parts = [
            (signal_row or {}).get("fundamental_signal_summary", ""),
            (signal_row or {}).get("price_signal_summary", ""),
            (signal_row or {}).get("risk_signal_summary", ""),
            (gb_sic_row or {}).get("sic_descriptions", ""),
            (france_sector_row or {}).get("naf_description_en", ""),
            (netherlands_sector_row or {}).get("industries", "").replace(";", " "),
        ]
        extra_text = " ".join(part for part in extra_text_parts if part).strip()
        sector_source = "v2.38J" if signal_row else "v2.38AN" if gb_sic_row else "v2.38AO" if france_sector_row else "v2.38AQ" if netherlands_sector_row else ""
        selected, limitation, sector_matched = match_themes(company_name, extra_text, country, themes)
        if sector_source == "v2.38AQ":
            limitation = f"{limitation} {(netherlands_sector_row or {}).get('non_official_source_caveat', '')}".strip()
        status = context_status(sector_matched)
        opportunity = mean([float(t["opportunity_score"]) for t in selected])
        risk = mean([float(t["risk_score"]) for t in selected])
        balance = rounded(opportunity - risk)
        positive = "; ".join(f"{t['theme_id']}: {t['context_summary']}" for t in selected if float(t["opportunity_score"]) >= float(t["risk_score"]))
        risk_text = "; ".join(f"{t['theme_id']}: {t['context_summary']}" for t in selected if float(t["risk_score"]) > float(t["opportunity_score"]))
        context = {
            "asset_id": asset_id, "ticker": ticker, "company_name": company_name,
            "exchange": row.get("exchange", ""), "country": country,
            "identity_status": row.get("identity_status", ""), "overall_coverage_status": row.get("overall_coverage_status", ""),
            "sector_text_source": sector_source,
            "macro_context_status": status, "applicable_themes": "|".join(str(t["theme_id"]) for t in selected),
            "macro_opportunity_score": opportunity, "macro_risk_score": risk, "macro_balance": balance,
            "macro_context_summary": f"Static macro/geopolitical context applied using {len(selected)} taxonomy themes as of {ASOF_DATE}.",
            "macro_positive_context": positive or "No dominant macro tailwind in static taxonomy.",
            "macro_risk_context": risk_text or "No dominant macro headwind in static taxonomy.",
            "macro_limitations": limitation,
            "next_macro_research_steps": "Validate sector exposure manually; add a sourced live macro/news layer in a later phase; do not use this static layer to alter any fundamentals or growth feature already computed.",
            "recommendation_generated": False, "financial_advice": False, "broker_actions_allowed": False,
            "phase9c_authorized": False, "phase": PHASE,
        }
        context_rows.append(context)
        quality.append({
            "asset_id": asset_id, "ticker": ticker, "country": country, "macro_context_status": status,
            "theme_count": len(selected), "macro_opportunity_score": opportunity, "macro_risk_score": risk,
            "macro_balance": balance, "quality_notes": "sector_theme_matched" if sector_matched else "general_and_country_themes_only", "phase": PHASE,
        })
        for theme_row in selected:
            note_type = "MACRO_OPPORTUNITY" if float(theme_row["opportunity_score"]) >= float(theme_row["risk_score"]) else "MACRO_RISK"
            notes.append(note(asset_id, ticker, str(theme_row["theme_id"]), note_type, str(theme_row["context_summary"]), str(theme_row["confidence_level"])))
            if theme_row["theme_id"] in {"CHINA_US_TENSIONS", "DEFENSE_SECURITY", "EU_SINGLE_MARKET_REGULATION", "EUROZONE_ECB_MONETARY_POLICY", "UK_POST_BREXIT_TRADE_FRICTION", "CHF_SAFE_HAVEN_DYNAMICS"}:
                notes.append(note(asset_id, ticker, str(theme_row["theme_id"]), "GEOPOLITICAL_EXPOSURE", "Exposure theme requires sourced manual review before any research conclusion.", str(theme_row["confidence_level"])))
        notes.append(note(asset_id, ticker, "", "EVIDENCE_LIMITATION", limitation, "MEDIUM"))
        notes.append(note(asset_id, ticker, "", "LANGUAGE_GUARDRAIL", "Static context only; no final action language or external event claim is generated.", "HIGH"))

    write_csv(output_dir / "global_macro_geopolitical_taxonomy_v2_38am.csv", TAXONOMY_FIELDS, taxonomy_rows)
    write_csv(output_dir / "global_macro_geopolitical_context_v2_38am.csv", CONTEXT_FIELDS, context_rows)
    write_csv(output_dir / "global_macro_geopolitical_notes_v2_38am.csv", NOTE_FIELDS, notes)
    write_csv(output_dir / "global_macro_geopolitical_quality_v2_38am.csv", QUALITY_FIELDS, quality)
    write_csv(output_dir / "global_macro_geopolitical_rejections_v2_38am.csv", REJECTION_FIELDS, rejections)

    counts = Counter(row["macro_context_status"] for row in context_rows)
    by_country_ready = Counter(row["country"] for row in context_rows if row["macro_context_status"] == "MACRO_CONTEXT_READY")
    report = {
        "phase": PHASE,
        "status": "COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS",
        "identity_resolved_companies_input": len(identity_resolved),
        "companies_context_built": len(context_rows),
        "macro_context_ready": counts.get("MACRO_CONTEXT_READY", 0),
        "macro_context_partial": counts.get("MACRO_CONTEXT_PARTIAL", 0),
        "themes_defined": len(taxonomy_rows),
        "notes": len(notes),
        "rejected_rows": len(rejections),
        "sector_theme_matched_by_country_top": dict(sorted(by_country_ready.items(), key=lambda kv: -kv[1])[:10]),
        "sector_text_source_counts": dict(sorted(Counter(row["sector_text_source"] or "NONE" for row in context_rows).items())),
        "live_news_used": False, "recommendations_generated": False,
        "guardrails": {
            "network_calls": 0, "recommendations_generated": False, "financial_advice": False,
            "broker_actions_allowed": False, "phase9c_authorized": False, "ranking_modified": False,
            "scoring_modified": False, "live_news_used": False, "llm_runtime_classification": False,
        },
        "note": "Generalizes v2.38M (which only ever covered the old 50-company US shortlist) to every identity-resolved company in the v2.38AL global coverage matrix (1,244: 555 US + 689 Europe). Reconstructed twice to attack the 0/689 Europe sector-match finding from this phase's first run: v2.38AN's real UK Companies House SIC codes (29 companies, official source), v2.38AO's real French NAF/NACE codes (18 companies, official source), and v2.38AQ's Wikidata industry data (44 Netherlands companies, a user-approved non-official-source exception after KVK's real API turned out to require a paid subscription) now feed the same keyword matcher as the US's v2.38J narrative text. Germany (413 companies) was investigated and confirmed structurally non-public (v2.38AP): its WZ classification is never disclosed per-company by any German government source. The remaining 598 Europe companies (29 CH, 22 IT, 21 DK, 20 AT, 17 IE, 15 ES, 6 BE, 5 FI, 4 SE) still have no sector-classification source confirmed and stay on company_name-only matching, honestly reported via macro_limitations. Four country-specific structural themes remain (EU single-market regulation, Eurozone monetary policy, UK post-Brexit trade friction, Swiss franc safe-haven dynamics) -- evergreen jurisdictional facts, not dated event claims, matching v2.38M's own static/offline discipline.",
    }
    write_text(output_dir / "global_macro_geopolitical_aggregate_report_v2_38am.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_docs(output_dir, report)
    write_manifest(output_dir, report)
    return report


def note(asset_id: str, ticker: str, theme_id: str, note_type: str, text: str, confidence: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "theme_id": theme_id, "note_type": note_type, "note": text, "confidence_level": confidence, "source_policy": "OFFLINE_STATIC_NO_LIVE_NEWS", "phase": PHASE}


def write_docs(output_dir: Path, report: dict[str, Any]) -> None:
    write_text(output_dir / "README.md", "# v2.38AM global macro/geopolitical context\n\nGeneralizes v2.38M's static, offline macro/geopolitical taxonomy from the old 50-company US shortlist to every identity-resolved company in the v2.38AL global coverage matrix (US + Europe). No live news, no network calls, no runtime LLM classification, no broker actions, no recommendation language.\n")
    write_text(output_dir / "GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_CONTRACT_v2_38am.md", "# Global Macro/Geopolitical Context Contract v2.38AM\n\nApplies a static taxonomy of macro and geopolitical themes to every identity-resolved company on file. Never modifies any fundamentals or growth feature computed elsewhere, never authorizes phase 9C, scoring, ranking or recommendations.\n")
    gate = f"""# Phase 9AM Global Macro/Geopolitical Gate v2.38AM

Status: {report['status']}

- Identity-resolved companies input: {report['identity_resolved_companies_input']}
- Companies with context built: {report['companies_context_built']}
- Macro context ready (sector theme matched): {report['macro_context_ready']}
- Macro context partial (general/country themes only): {report['macro_context_partial']}
- Themes defined: {report['themes_defined']}
- Notes: {report['notes']}
- Rejected rows: {report['rejected_rows']}

Guardrails: no network calls, no live news, no runtime LLM classification, no ranking/scoring modification, no broker actions and no phase 9C authorization.
"""
    write_text(output_dir / "PHASE9AM_GLOBAL_MACRO_GEOPOLITICAL_GATE_v2_38am.md", gate)


def write_manifest(output_dir: Path, report: dict[str, Any]) -> None:
    public = [
        "README.md", "GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_CONTRACT_v2_38am.md", "PHASE9AM_GLOBAL_MACRO_GEOPOLITICAL_GATE_v2_38am.md",
        "global_macro_geopolitical_taxonomy_v2_38am.csv", "global_macro_geopolitical_context_v2_38am.csv",
        "global_macro_geopolitical_notes_v2_38am.csv", "global_macro_geopolitical_quality_v2_38am.csv",
        "global_macro_geopolitical_rejections_v2_38am.csv", "global_macro_geopolitical_aggregate_report_v2_38am.json",
    ]
    manifest = {"phase": PHASE, "outputs": {name: {"bytes": (output_dir / name).stat().st_size, "sha256": sha256(output_dir / name)} for name in public if (output_dir / name).exists()}, "guardrails": report["guardrails"]}
    write_text(output_dir / "global_macro_geopolitical_manifest_v2_38am.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-input", type=Path, default=COVERAGE_INPUT)
    parser.add_argument("--us-signal-input", type=Path, default=US_SIGNAL_INPUT)
    parser.add_argument("--gb-sic-input", type=Path, default=GB_SIC_INPUT)
    parser.add_argument("--france-sector-input", type=Path, default=FRANCE_SECTOR_INPUT)
    parser.add_argument("--netherlands-sector-input", type=Path, default=NETHERLANDS_SECTOR_INPUT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.coverage_input, args.us_signal_input, args.gb_sic_input, args.france_sector_input, args.netherlands_sector_input, args.output_dir)
    print(json.dumps({k: report[k] for k in ("phase", "status", "companies_context_built", "macro_context_ready", "macro_context_partial")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
