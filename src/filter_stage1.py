# PHASE 7B.8.1 EXACT BALANCED STAGE 1 POLICY APPLIED
"""
Scout Finance — Phase 5C Stage 1 filter.

Stage 1 goal:
Classify validated global universe companies as:

- PASSED
- WATCHLIST
- REJECTED

using only cheap market/investability filters.

This module does not call OpenAI.
It does not modify app.py.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.funnel_paths import (
    GLOBAL_UNIVERSE_VALIDATED_PATH,
    SCOUTING_OUTPUTS_DIR,
    STAGES_DIR,
    ensure_funnel_directories,
)


STAGE1_PASSED_PATH = STAGES_DIR / "stage1_passed.csv"
STAGE1_WATCHLIST_PATH = STAGES_DIR / "stage1_watchlist.csv"
STAGE1_REJECTED_PATH = STAGES_DIR / "stage1_rejected.csv"
STAGE1_REJECTION_LOG_PATH = STAGES_DIR / "stage1_rejection_log.csv"
STAGE1_SUMMARY_PATH = SCOUTING_OUTPUTS_DIR / "stage1_summary.json"


DEFAULT_STAGE1_CONFIG = {
    "target_pass_rate": 0.20,
    "min_market_cap_pass": 500_000_000,
    "min_market_cap_watchlist": 150_000_000,
    "min_price_pass": 3.0,
    "min_price_watchlist": 1.5,
    "min_dollar_volume_pass": 5_000_000,
    "min_dollar_volume_watchlist": 1_000_000,
    "allowed_asset_types": {"common_stock"},
    "allow_adr": True,
    "allow_otc": False,
    "allowed_exchanges": {
        "NYSE",
        "NASDAQ",
        "AMEX",
        "ARCA",
        "CBOE",
        "LSE",
        "TSX",
        "XETRA",
        "EURONEXT",
        "SIX",
        "HKEX",
        "TSE",
        "ASX",
    },
}


REJECTION_COLUMNS = [
    "ticker",
    "name",
    "stage",
    "status",
    "reason_code",
    "reason_text",
    "metric_name",
    "metric_value",
    "threshold",
    "severity",
    "recoverable",
    "special_case",
    "sector",
    "industry",
    "country",
    "market_cap",
    "data_date",
    "created_at",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _is_missing(value: Any) -> bool:
    try:
        return pd.isna(value)
    except Exception:
        return value is None


def _to_bool(value: Any) -> bool | None:
    if _is_missing(value):
        return None

    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()

    if text in {"true", "1", "yes", "y", "si", "sí", "active", "activo"}:
        return True

    if text in {"false", "0", "no", "n", "inactive", "inactivo"}:
        return False

    return None


def _to_float(value: Any) -> float | None:
    if _is_missing(value):
        return None

    try:
        return float(value)
    except Exception:
        return None


def _clean_text(value: Any, default: str = "") -> str:
    if _is_missing(value):
        return default

    return str(value).strip()


def _add_reason(
    reasons: list[dict[str, Any]],
    *,
    reason_code: str,
    reason_text: str,
    metric_name: str,
    metric_value: Any,
    threshold: Any,
    severity: str,
    recoverable: bool,
) -> None:
    reasons.append(
        {
            "reason_code": reason_code,
            "reason_text": reason_text,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "threshold": threshold,
            "severity": severity,
            "recoverable": recoverable,
        }
    )


def classify_stage1_row(
    row: pd.Series,
    config: dict[str, Any] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Classify one company row for Stage 1.

    Returns:
        status, reasons

    status in:
        PASSED, WATCHLIST, REJECTED
    """

    cfg = config or DEFAULT_STAGE1_CONFIG
    reasons: list[dict[str, Any]] = []
    hard_reject = False
    watchlist = False

    ticker = _clean_text(row.get("ticker")).upper()
    asset_type = _clean_text(row.get("asset_type")).lower()
    exchange = _clean_text(row.get("exchange")).upper()
    is_active = _to_bool(row.get("is_active"))

    market_cap = _to_float(row.get("market_cap"))
    price = _to_float(row.get("price"))
    avg_volume_90d = _to_float(row.get("avg_volume_90d"))
    dollar_volume_90d = _to_float(row.get("dollar_volume_90d"))

    if dollar_volume_90d is None and price is not None and avg_volume_90d is not None:
        dollar_volume_90d = price * avg_volume_90d

    # Hard rules
    if not ticker:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="MISSING_TICKER",
            reason_text="Ticker missing.",
            metric_name="ticker",
            metric_value=ticker,
            threshold="required",
            severity="critical",
            recoverable=False,
        )

    if is_active is False:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="INACTIVE_SECURITY",
            reason_text="Security is not active.",
            metric_name="is_active",
            metric_value=is_active,
            threshold=True,
            severity="critical",
            recoverable=False,
        )

    if asset_type not in cfg["allowed_asset_types"]:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="NOT_COMMON_STOCK",
            reason_text="Asset type is not allowed for Stage 1.",
            metric_name="asset_type",
            metric_value=asset_type,
            threshold=sorted(cfg["allowed_asset_types"]),
            severity="high",
            recoverable=False,
        )

    if not cfg.get("allow_otc", False) and ("OTC" in exchange or exchange == "PINK"):
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="OTC_NOT_ALLOWED",
            reason_text="OTC/Pink Sheet security excluded in Stage 1.",
            metric_name="exchange",
            metric_value=exchange,
            threshold="non-OTC",
            severity="high",
            recoverable=False,
        )

    # Exchange rule: if exchange missing or not in known list, watchlist rather than reject.
    if not exchange:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="MISSING_EXCHANGE",
            reason_text="Exchange missing.",
            metric_name="exchange",
            metric_value=exchange,
            threshold="known exchange",
            severity="medium",
            recoverable=True,
        )
    elif exchange not in cfg["allowed_exchanges"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="EXCHANGE_NOT_IN_ALLOWED_LIST",
            reason_text="Exchange is not in the default allowed list.",
            metric_name="exchange",
            metric_value=exchange,
            threshold=sorted(cfg["allowed_exchanges"]),
            severity="medium",
            recoverable=True,
        )

    # Market cap
    if market_cap is None:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="MISSING_MARKET_CAP",
            reason_text="Market cap missing.",
            metric_name="market_cap",
            metric_value=market_cap,
            threshold="required",
            severity="high",
            recoverable=True,
        )
    elif market_cap < cfg["min_market_cap_watchlist"]:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="MARKET_CAP_BELOW_MINIMUM",
            reason_text="Market cap below Stage 1 minimum.",
            metric_name="market_cap",
            metric_value=market_cap,
            threshold=cfg["min_market_cap_watchlist"],
            severity="high",
            recoverable=False,
        )
    elif market_cap < cfg["min_market_cap_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="MARKET_CAP_WATCHLIST_RANGE",
            reason_text="Market cap is below pass threshold but above rejection threshold.",
            metric_name="market_cap",
            metric_value=market_cap,
            threshold=cfg["min_market_cap_pass"],
            severity="medium",
            recoverable=True,
        )

    # Price
    if price is None:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="MISSING_PRICE",
            reason_text="Price missing.",
            metric_name="price",
            metric_value=price,
            threshold="required",
            severity="high",
            recoverable=True,
        )
    elif price < cfg["min_price_watchlist"]:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="PRICE_BELOW_MINIMUM",
            reason_text="Price below Stage 1 minimum.",
            metric_name="price",
            metric_value=price,
            threshold=cfg["min_price_watchlist"],
            severity="high",
            recoverable=False,
        )
    elif price < cfg["min_price_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="PRICE_STRONG_WATCHLIST_RANGE",
            reason_text="Price is below pass threshold but above rejection threshold.",
            metric_name="price",
            metric_value=price,
            threshold=cfg["min_price_pass"],
            severity="medium",
            recoverable=True,
        )
    elif price < 5.0:
        _add_reason(
            reasons,
            reason_code="PRICE_WEAK_WATCHLIST_RANGE",
            reason_text="Price is below weak warning threshold but does not trigger watchlist by itself.",
            metric_name="price",
            metric_value=price,
            threshold=5.0,
            severity="low",
            recoverable=True,
        )

    # Dollar volume
    if dollar_volume_90d is None:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="MISSING_DOLLAR_VOLUME",
            reason_text="Dollar volume cannot be calculated.",
            metric_name="dollar_volume_90d",
            metric_value=dollar_volume_90d,
            threshold="required",
            severity="high",
            recoverable=True,
        )
    elif dollar_volume_90d < cfg["min_dollar_volume_watchlist"]:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="LOW_DOLLAR_VOLUME",
            reason_text="Dollar volume below Stage 1 minimum.",
            metric_name="dollar_volume_90d",
            metric_value=dollar_volume_90d,
            threshold=cfg["min_dollar_volume_watchlist"],
            severity="high",
            recoverable=False,
        )
    elif dollar_volume_90d < cfg["min_dollar_volume_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="DOLLAR_VOLUME_WATCHLIST_RANGE",
            reason_text="Dollar volume is below pass threshold but above rejection threshold.",
            metric_name="dollar_volume_90d",
            metric_value=dollar_volume_90d,
            threshold=cfg["min_dollar_volume_pass"],
            severity="medium",
            recoverable=True,
        )

    if hard_reject:
        return "REJECTED", reasons

    if watchlist:
        return "WATCHLIST", reasons

    return "PASSED", reasons


def _build_rejection_log_row(
    row: pd.Series,
    status: str,
    reason: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ticker": _clean_text(row.get("ticker")).upper(),
        "name": _clean_text(row.get("name")),
        "stage": "stage1",
        "status": status,
        "reason_code": reason.get("reason_code"),
        "reason_text": reason.get("reason_text"),
        "metric_name": reason.get("metric_name"),
        "metric_value": reason.get("metric_value"),
        "threshold": reason.get("threshold"),
        "severity": reason.get("severity"),
        "recoverable": reason.get("recoverable"),
        "special_case": False,
        "sector": _clean_text(row.get("sector")),
        "industry": _clean_text(row.get("industry")),
        "country": _clean_text(row.get("country")),
        "market_cap": row.get("market_cap"),
        "data_date": row.get("last_updated"),
        "created_at": _utc_now_iso(),
    }


def run_stage1_filter(
    input_path: Path = GLOBAL_UNIVERSE_VALIDATED_PATH,
    passed_path: Path = STAGE1_PASSED_PATH,
    watchlist_path: Path = STAGE1_WATCHLIST_PATH,
    rejected_path: Path = STAGE1_REJECTED_PATH,
    rejection_log_path: Path = STAGE1_REJECTION_LOG_PATH,
    summary_path: Path = STAGE1_SUMMARY_PATH,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run Stage 1 filter over validated global universe.
    """

    ensure_funnel_directories()

    if not input_path.exists():
        raise FileNotFoundError(
            f"Validated universe not found: {input_path}. "
            "Run Phase 5B first: python -m src.load_global_universe"
        )

    df = pd.read_csv(input_path)

    if "dollar_volume_90d" not in df.columns:
        df["dollar_volume_90d"] = (
            pd.to_numeric(df.get("price"), errors="coerce")
            * pd.to_numeric(df.get("avg_volume_90d"), errors="coerce")
        )

    statuses = []
    primary_reasons = []
    all_reason_codes = []
    log_rows = []

    for _, row in df.iterrows():
        status, reasons = classify_stage1_row(row, config=config)

        statuses.append(status)

        if reasons:
            primary_reasons.append(reasons[0]["reason_code"])
            all_reason_codes.append("|".join(reason["reason_code"] for reason in reasons))
        else:
            primary_reasons.append("")
            all_reason_codes.append("")

        for reason in reasons:
            log_rows.append(_build_rejection_log_row(row, status, reason))

    result_df = df.copy()
    result_df["stage1_status"] = statuses
    result_df["stage1_primary_reason"] = primary_reasons
    result_df["stage1_all_reasons"] = all_reason_codes

    passed_df = result_df[result_df["stage1_status"] == "PASSED"].copy()
    watchlist_df = result_df[result_df["stage1_status"] == "WATCHLIST"].copy()
    rejected_df = result_df[result_df["stage1_status"] == "REJECTED"].copy()

    passed_df.to_csv(passed_path, index=False, encoding="utf-8-sig")
    watchlist_df.to_csv(watchlist_path, index=False, encoding="utf-8-sig")
    rejected_df.to_csv(rejected_path, index=False, encoding="utf-8-sig")

    log_df = pd.DataFrame(log_rows, columns=REJECTION_COLUMNS)
    log_df.to_csv(rejection_log_path, index=False, encoding="utf-8-sig")

    input_count = int(len(result_df))
    passed_count = int(len(passed_df))
    watchlist_count = int(len(watchlist_df))
    rejected_count = int(len(rejected_df))

    top_reasons = (
        log_df["reason_code"].value_counts().head(20).to_dict()
        if not log_df.empty
        else {}
    )

    summary = {
        "phase": "5C",
        "stage": "stage1",
        "created_at": _utc_now_iso(),
        "input_companies": input_count,
        "passed_companies": passed_count,
        "watchlist_companies": watchlist_count,
        "rejected_companies": rejected_count,
        "pass_rate": passed_count / input_count if input_count else 0,
        "watchlist_rate": watchlist_count / input_count if input_count else 0,
        "rejection_rate": rejected_count / input_count if input_count else 0,
        "top_rejection_or_watchlist_reasons": top_reasons,
        "output_files": {
            "passed": str(passed_path),
            "watchlist": str(watchlist_path),
            "rejected": str(rejected_path),
            "rejection_log": str(rejection_log_path),
            "summary": str(summary_path),
        },
        "config": config or {
            key: sorted(value) if isinstance(value, set) else value
            for key, value in DEFAULT_STAGE1_CONFIG.items()
        },
    }

    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return summary


def print_stage1_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 5C Stage 1 filter")
    print("=" * 52)
    print(f"Input companies: {summary.get('input_companies')}")
    print(f"PASSED: {summary.get('passed_companies')}")
    print(f"WATCHLIST: {summary.get('watchlist_companies')}")
    print(f"REJECTED: {summary.get('rejected_companies')}")
    print(f"Pass rate: {summary.get('pass_rate'):.2%}")
    print(f"Watchlist rate: {summary.get('watchlist_rate'):.2%}")
    print(f"Rejection rate: {summary.get('rejection_rate'):.2%}")
    print()
    print("Output files:")
    for label, path in summary.get("output_files", {}).items():
        print(f"- {label}: {path}")
