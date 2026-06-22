
"""
Scout Finance — Phase 7A.3 Institutional Universe Cleaning.

Purpose:
- Classify and clean the free USA symbol universe before market-data enrichment.
- Separate "out of scope instrument" from "financial rejection".
- Produce an investable clean universe for professional screening.

Input:
    data/raw/universe_source_real.csv

Outputs:
    data/raw/universe_source_real_clean.csv
    data/raw/universe_source_real_excluded.csv
    outputs/scouting/universe_cleaning_summary.json
    outputs/scouting/universe_cleaning_exclusion_log.csv

This module:
- does not call OpenAI;
- does not use paid APIs;
- does not modify app.py;
- does not modify releases/v0.6;
- does not enrich market data.

Run:
    ./.venv/Scripts/python.exe -m src.clean_universe_institutional
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real.csv"
DEFAULT_CLEAN_OUTPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real_clean.csv"
DEFAULT_EXCLUDED_OUTPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real_excluded.csv"

SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"
SUMMARY_PATH = SCOUTING_OUTPUTS_DIR / "universe_cleaning_summary.json"
EXCLUSION_LOG_PATH = SCOUTING_OUTPUTS_DIR / "universe_cleaning_exclusion_log.csv"


OUTPUT_COLUMNS = [
    "Symbol",
    "Name",
    "Exchange",
    "Country",
    "Sector",
    "Industry",
    "Market Cap",
    "Last Sale",
    "Volume",
    "Source",
    "instrument_type",
    "instrument_scope",
    "classification_confidence",
    "classification_reason",
]


EXCLUSION_COLUMNS = OUTPUT_COLUMNS + [
    "decision",
    "reason_code",
    "reason_category",
    "business_explanation",
    "severity",
    "recoverable",
    "decision_layer",
]


INCLUDE_BY_DEFAULT = {
    "COMMON_STOCK",
    "ADR",
    "REIT",
}


EXCLUDE_BY_DEFAULT = {
    "ETF",
    "ETN",
    "FUND",
    "CLOSED_END_FUND",
    "PREFERRED",
    "WARRANT",
    "RIGHT",
    "UNIT",
    "SPAC_OR_BLANK_CHECK",
    "BOND_OR_NOTE",
    "UNKNOWN_SPECIAL_INSTRUMENT",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def _normalize_symbol(symbol: Any) -> str:
    return _safe_text(symbol).upper()


def _contains_any(text: str, patterns: list[str]) -> bool:
    lower = text.lower()
    return any(pattern.lower() in lower for pattern in patterns)


def _symbol_suffix_type(symbol: str) -> str | None:
    """
    Detect common USA instrument suffixes from Nasdaq-style symbols.

    Examples:
    - AACBR = right
    - AACBU = unit
    - AACBW = warrant
    - AAM.PRA / AAM-PA style preferred may appear differently depending on source
    """

    symbol = symbol.upper().strip()

    if not symbol:
        return None

    # Very common NASDAQ convention: U = unit, W = warrant, R = right.
    # We apply this carefully and later combine with name-based evidence.
    if len(symbol) >= 5:
        if symbol.endswith("W") or symbol.endswith("WS"):
            return "WARRANT"
        if symbol.endswith("R"):
            return "RIGHT"
        if symbol.endswith("U"):
            return "UNIT"

    if "-P" in symbol or ".P" in symbol or " PR" in symbol:
        return "PREFERRED"

    return None


def classify_instrument(symbol: str, name: str, source: str = "") -> dict[str, Any]:
    """
    Classify security/instrument type using conservative symbol and name heuristics.
    """

    symbol = _normalize_symbol(symbol)
    name = _safe_text(name)
    source = _safe_text(source)

    lower_name = name.lower()

    # Strong name-based rules first.
    if _contains_any(lower_name, ["warrant", "warrants"]):
        return {
            "instrument_type": "WARRANT",
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "HIGH",
            "classification_reason": "Security name indicates warrant.",
        }

    if _contains_any(lower_name, [" right", " rights", "- rights"]):
        return {
            "instrument_type": "RIGHT",
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "HIGH",
            "classification_reason": "Security name indicates rights.",
        }

    if _contains_any(lower_name, [" unit", " units", "- units"]):
        return {
            "instrument_type": "UNIT",
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "HIGH",
            "classification_reason": "Security name indicates unit.",
        }

    if _contains_any(lower_name, ["preferred", "preference share", "depositary shares each representing"]):
        return {
            "instrument_type": "PREFERRED",
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "HIGH",
            "classification_reason": "Security name indicates preferred/depositary preferred instrument.",
        }

    if _contains_any(lower_name, ["etf", "exchange traded fund", "exchange-traded fund"]):
        return {
            "instrument_type": "ETF",
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "HIGH",
            "classification_reason": "Security name indicates ETF.",
        }

    if _contains_any(lower_name, ["etn", "exchange traded note", "exchange-traded note"]):
        return {
            "instrument_type": "ETN",
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "HIGH",
            "classification_reason": "Security name indicates ETN.",
        }

    if _contains_any(lower_name, ["closed end fund", "closed-end fund", "closed end", "closed-end"]):
        return {
            "instrument_type": "CLOSED_END_FUND",
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "HIGH",
            "classification_reason": "Security name indicates closed-end fund.",
        }

    if _contains_any(lower_name, ["bond", "note due", "notes due", "senior notes", "subordinated notes"]):
        return {
            "instrument_type": "BOND_OR_NOTE",
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "HIGH",
            "classification_reason": "Security name indicates debt security.",
        }

    if _contains_any(
        lower_name,
        [
            "acquisition corp",
            "acquisition corporation",
            "blank check",
            "special purpose acquisition",
            "spac",
        ],
    ):
        return {
            "instrument_type": "SPAC_OR_BLANK_CHECK",
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "MEDIUM",
            "classification_reason": "Security name suggests SPAC / blank check company.",
        }

    if _contains_any(lower_name, ["reit", "real estate investment trust"]):
        return {
            "instrument_type": "REIT",
            "instrument_scope": "IN_SCOPE",
            "classification_confidence": "MEDIUM",
            "classification_reason": "Security name indicates REIT; keep in scope but evaluate later with specific metrics.",
        }

    if _contains_any(lower_name, ["american depositary", "american depositary shares", "ads", "adr"]):
        return {
            "instrument_type": "ADR",
            "instrument_scope": "IN_SCOPE",
            "classification_confidence": "MEDIUM",
            "classification_reason": "Security name indicates ADR/ADS; keep in scope for now.",
        }

    # Symbol suffix rules, lower confidence if name did not explicitly confirm.
    suffix_type = _symbol_suffix_type(symbol)

    if suffix_type in {"WARRANT", "RIGHT", "UNIT", "PREFERRED"}:
        return {
            "instrument_type": suffix_type,
            "instrument_scope": "OUT_OF_SCOPE",
            "classification_confidence": "MEDIUM",
            "classification_reason": f"Symbol suffix suggests {suffix_type.lower()} instrument.",
        }

    # Common stock name hints.
    if _contains_any(lower_name, ["common stock", "ordinary shares", "common shares", "class a common", "class b common"]):
        return {
            "instrument_type": "COMMON_STOCK",
            "instrument_scope": "IN_SCOPE",
            "classification_confidence": "HIGH",
            "classification_reason": "Security name indicates common stock/common shares.",
        }

    # Conservative fallback: keep in scope but mark lower confidence.
    return {
        "instrument_type": "COMMON_STOCK",
        "instrument_scope": "IN_SCOPE",
        "classification_confidence": "LOW",
        "classification_reason": "No out-of-scope instrument markers detected; treated as common stock candidate.",
    }


def _build_exclusion_decision(row: pd.Series) -> dict[str, Any]:
    instrument_type = row.get("instrument_type", "UNKNOWN_SPECIAL_INSTRUMENT")

    return {
        "decision": "EXCLUDED_FROM_UNIVERSE",
        "reason_code": f"OUT_OF_SCOPE_{instrument_type}",
        "reason_category": "INSTRUMENT_SCOPE",
        "business_explanation": (
            f"Instrument classified as {instrument_type}; excluded before market-data enrichment "
            "because it is not part of the initial common-stock scouting universe."
        ),
        "severity": "info",
        "recoverable": True,
        "decision_layer": "UNIVERSE_CLEANING",
    }


def clean_universe_institutional(
    input_path: Path = DEFAULT_INPUT,
    clean_output_path: Path = DEFAULT_CLEAN_OUTPUT,
    excluded_output_path: Path = DEFAULT_EXCLUDED_OUTPUT,
    include_spacs: bool = False,
    include_reits: bool = True,
    include_adrs: bool = True,
) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input universe not found: {input_path}. "
            "Run first: python -m src.download_free_us_universe"
        )

    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(input_path)

    if raw.empty:
        raise ValueError(f"Input universe is empty: {input_path}")

    required_base_columns = [
        "Symbol",
        "Name",
        "Exchange",
        "Country",
        "Sector",
        "Industry",
        "Market Cap",
        "Last Sale",
        "Volume",
        "Source",
    ]

    for column in required_base_columns:
        if column not in raw.columns:
            raw[column] = ""

    work = raw.copy()

    classifications = work.apply(
        lambda row: classify_instrument(
            symbol=row.get("Symbol", ""),
            name=row.get("Name", ""),
            source=row.get("Source", ""),
        ),
        axis=1,
    )

    class_df = pd.DataFrame(list(classifications))
    work = pd.concat([work.reset_index(drop=True), class_df.reset_index(drop=True)], axis=1)

    # Policy overrides.
    if not include_spacs:
        work.loc[work["instrument_type"] == "SPAC_OR_BLANK_CHECK", "instrument_scope"] = "OUT_OF_SCOPE"

    if not include_reits:
        work.loc[work["instrument_type"] == "REIT", "instrument_scope"] = "OUT_OF_SCOPE"

    if not include_adrs:
        work.loc[work["instrument_type"] == "ADR", "instrument_scope"] = "OUT_OF_SCOPE"

    clean = work[work["instrument_scope"] == "IN_SCOPE"].copy()
    excluded = work[work["instrument_scope"] != "IN_SCOPE"].copy()

    exclusion_decisions = []

    if not excluded.empty:
        for _, row in excluded.iterrows():
            decision = _build_exclusion_decision(row)
            exclusion_decisions.append(decision)

        decisions_df = pd.DataFrame(exclusion_decisions)
        excluded = pd.concat([excluded.reset_index(drop=True), decisions_df.reset_index(drop=True)], axis=1)
    else:
        for col in [
            "decision",
            "reason_code",
            "reason_category",
            "business_explanation",
            "severity",
            "recoverable",
            "decision_layer",
        ]:
            excluded[col] = pd.Series(dtype="object")

    clean = clean[OUTPUT_COLUMNS].copy()
    excluded = excluded[EXCLUSION_COLUMNS].copy()

    clean_output_path.parent.mkdir(parents=True, exist_ok=True)
    excluded_output_path.parent.mkdir(parents=True, exist_ok=True)

    clean.to_csv(clean_output_path, index=False, encoding="utf-8-sig")
    excluded.to_csv(excluded_output_path, index=False, encoding="utf-8-sig")
    excluded.to_csv(EXCLUSION_LOG_PATH, index=False, encoding="utf-8-sig")

    instrument_distribution = work["instrument_type"].value_counts(dropna=False).to_dict()
    clean_distribution = clean["instrument_type"].value_counts(dropna=False).to_dict() if not clean.empty else {}
    excluded_distribution = excluded["instrument_type"].value_counts(dropna=False).to_dict() if not excluded.empty else {}

    summary = {
        "phase": "7A.3",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "input_path": str(input_path),
        "clean_output_path": str(clean_output_path),
        "excluded_output_path": str(excluded_output_path),
        "exclusion_log_path": str(EXCLUSION_LOG_PATH),
        "input_rows": int(len(raw)),
        "clean_rows": int(len(clean)),
        "excluded_rows": int(len(excluded)),
        "clean_rate_percent": round((len(clean) / len(raw)) * 100, 2) if len(raw) else 0,
        "excluded_rate_percent": round((len(excluded) / len(raw)) * 100, 2) if len(raw) else 0,
        "include_spacs": include_spacs,
        "include_reits": include_reits,
        "include_adrs": include_adrs,
        "instrument_distribution": instrument_distribution,
        "clean_distribution": clean_distribution,
        "excluded_distribution": excluded_distribution,
        "openai_called": False,
        "paid_api_called": False,
        "app_modified": False,
        "release_v0_6_modified": False,
        "notes": [
            "This is a pre-market-data institutional universe cleaning layer.",
            "Excluded instruments are not financial rejections; they are outside the initial scouting universe.",
            "REITs and ADRs are kept by default but should later have specific metrics/risk treatment.",
        ],
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7A.3 Institutional Universe Cleaning")
    print("=" * 78)
    print(f"Status: {summary.get('status')}")
    print(f"Input rows: {summary.get('input_rows')}")
    print(f"Clean rows: {summary.get('clean_rows')} ({summary.get('clean_rate_percent')}%)")
    print(f"Excluded rows: {summary.get('excluded_rows')} ({summary.get('excluded_rate_percent')}%)")
    print(f"Clean output: {summary.get('clean_output_path')}")
    print(f"Excluded output: {summary.get('excluded_output_path')}")
    print(f"OpenAI called: {summary.get('openai_called')}")
    print(f"Paid API called: {summary.get('paid_api_called')}")
    print()
    print("Instrument distribution")
    print("-" * 78)
    for key, value in summary.get("instrument_distribution", {}).items():
        print(f"{key}: {value}")
    print()
    print("Next command")
    print("-" * 78)
    print(
        ".\\.venv\\Scripts\\python.exe -m src.enrich_market_data_yfinance "
        "--input data/raw/universe_source_real_clean.csv "
        "--output data/raw/universe_source_real_clean_market_enriched.csv "
        "--limit 100 --sleep 0.3"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--clean-output", default=str(DEFAULT_CLEAN_OUTPUT))
    parser.add_argument("--excluded-output", default=str(DEFAULT_EXCLUDED_OUTPUT))
    parser.add_argument("--include-spacs", action="store_true")
    parser.add_argument("--exclude-reits", action="store_true")
    parser.add_argument("--exclude-adrs", action="store_true")
    args = parser.parse_args()

    summary = clean_universe_institutional(
        input_path=Path(args.input),
        clean_output_path=Path(args.clean_output),
        excluded_output_path=Path(args.excluded_output),
        include_spacs=args.include_spacs,
        include_reits=not args.exclude_reits,
        include_adrs=not args.exclude_adrs,
    )

    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
