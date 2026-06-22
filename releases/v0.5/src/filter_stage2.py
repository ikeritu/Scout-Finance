"""
Scout Finance — Phase 5D Stage 2 financial sanity check.

Stage 2 goal:
Classify Stage 1 PASSED companies as:

- PASSED
- WATCHLIST
- REJECTED

using basic financial sanity filters.

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
    SCOUTING_OUTPUTS_DIR,
    STAGES_DIR,
    ensure_funnel_directories,
)


STAGE1_PASSED_PATH = STAGES_DIR / "stage1_passed.csv"

STAGE2_PASSED_PATH = STAGES_DIR / "stage2_passed.csv"
STAGE2_WATCHLIST_PATH = STAGES_DIR / "stage2_watchlist.csv"
STAGE2_REJECTED_PATH = STAGES_DIR / "stage2_rejected.csv"
STAGE2_REJECTION_LOG_PATH = STAGES_DIR / "stage2_rejection_log.csv"
STAGE2_SUMMARY_PATH = SCOUTING_OUTPUTS_DIR / "stage2_summary.json"


DEFAULT_STAGE2_CONFIG = {
    "max_financial_data_age_months": 18,
    "data_completeness_pass": 70,
    "data_completeness_watchlist": 50,
    "min_operating_margin_pass": 0.0,
    "min_operating_margin_watchlist": -0.20,
    "min_fcf_margin_pass": 0.0,
    "min_fcf_margin_watchlist": -0.10,
    "max_net_debt_to_ebitda_pass": 3.0,
    "max_net_debt_to_ebitda_watchlist": 5.0,
    "max_shares_dilution_3y_pass": 0.10,
    "max_shares_dilution_3y_watchlist": 0.30,
    "growth_exception_min_revenue_growth_3y": 0.25,
    "growth_exception_min_gross_margin": 0.40,
    "special_case_sectors": {
        "banks",
        "banking",
        "insurance",
        "reits",
        "reit",
        "biotechnology",
        "utilities",
        "mining",
        "financial services",
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


REQUIRED_STAGE2_COLUMNS = [
    "revenue_ttm",
    "operating_margin",
    "fcf_margin",
    "net_debt_to_ebitda",
    "shares_dilution_3y",
    "data_completeness_score",
    "financial_data_date",
    "special_case",
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

    if text in {"true", "1", "yes", "y", "si", "sí"}:
        return True

    if text in {"false", "0", "no", "n"}:
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


def _sector_special_case(row: pd.Series, config: dict[str, Any]) -> bool:
    special_case_value = _to_bool(row.get("special_case"))

    if special_case_value is True:
        return True

    sector = _clean_text(row.get("sector")).lower()
    industry = _clean_text(row.get("industry")).lower()

    special_sectors = config.get("special_case_sectors", set())

    return sector in special_sectors or industry in special_sectors


def _has_growth_exception(row: pd.Series, config: dict[str, Any]) -> bool:
    revenue_growth_3y = _to_float(row.get("revenue_growth_3y"))
    gross_margin = _to_float(row.get("gross_margin"))
    net_debt_to_ebitda = _to_float(row.get("net_debt_to_ebitda"))

    if revenue_growth_3y is None or gross_margin is None:
        return False

    if revenue_growth_3y < config["growth_exception_min_revenue_growth_3y"]:
        return False

    if gross_margin < config["growth_exception_min_gross_margin"]:
        return False

    if net_debt_to_ebitda is not None and net_debt_to_ebitda > config["max_net_debt_to_ebitda_watchlist"]:
        return False

    return True


def ensure_stage2_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Stage 2 columns if missing, filled with NA.

    This lets the filter produce clear missing-data reasons instead of crashing.
    """

    result = df.copy()

    optional_stage2_columns = [
        "revenue_ttm",
        "revenue_growth_1y",
        "revenue_growth_3y",
        "gross_margin",
        "operating_margin",
        "net_margin",
        "ebitda",
        "free_cash_flow",
        "fcf_margin",
        "total_debt",
        "cash",
        "net_debt",
        "net_debt_to_ebitda",
        "debt_to_equity",
        "current_ratio",
        "interest_coverage",
        "shares_dilution_3y",
        "financial_data_date",
        "data_completeness_score",
        "special_case",
    ]

    for column in optional_stage2_columns:
        if column not in result.columns:
            result[column] = pd.NA

    return result


def classify_stage2_row(
    row: pd.Series,
    config: dict[str, Any] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Classify one company row for Stage 2.

    Returns:
        status, reasons

    status in:
        PASSED, WATCHLIST, REJECTED
    """

    cfg = config or DEFAULT_STAGE2_CONFIG
    reasons: list[dict[str, Any]] = []

    hard_reject = False
    watchlist = False

    special_case = _sector_special_case(row, cfg)
    growth_exception = _has_growth_exception(row, cfg)

    revenue_ttm = _to_float(row.get("revenue_ttm"))
    operating_margin = _to_float(row.get("operating_margin"))
    fcf_margin = _to_float(row.get("fcf_margin"))
    net_debt_to_ebitda = _to_float(row.get("net_debt_to_ebitda"))
    shares_dilution_3y = _to_float(row.get("shares_dilution_3y"))
    data_completeness_score = _to_float(row.get("data_completeness_score"))
    financial_data_date = row.get("financial_data_date")

    # Data completeness
    if data_completeness_score is None:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="MISSING_DATA_COMPLETENESS",
            reason_text="Data completeness score missing.",
            metric_name="data_completeness_score",
            metric_value=data_completeness_score,
            threshold="required",
            severity="high",
            recoverable=True,
        )
    elif data_completeness_score < cfg["data_completeness_watchlist"]:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="LOW_DATA_COMPLETENESS",
            reason_text="Data completeness below Stage 2 minimum.",
            metric_name="data_completeness_score",
            metric_value=data_completeness_score,
            threshold=cfg["data_completeness_watchlist"],
            severity="high",
            recoverable=True,
        )
    elif data_completeness_score < cfg["data_completeness_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="DATA_COMPLETENESS_WATCHLIST_RANGE",
            reason_text="Data completeness below pass threshold but above rejection threshold.",
            metric_name="data_completeness_score",
            metric_value=data_completeness_score,
            threshold=cfg["data_completeness_pass"],
            severity="medium",
            recoverable=True,
        )

    # Financial data date: required for passed; missing goes watchlist, not reject.
    if _is_missing(financial_data_date) or str(financial_data_date).strip() == "":
        watchlist = True
        _add_reason(
            reasons,
            reason_code="MISSING_FINANCIAL_DATA_DATE",
            reason_text="Financial data date missing.",
            metric_name="financial_data_date",
            metric_value=financial_data_date,
            threshold="required",
            severity="medium",
            recoverable=True,
        )

    # Revenue
    if revenue_ttm is None:
        if special_case:
            watchlist = True
            _add_reason(
                reasons,
                reason_code="MISSING_REVENUE_SPECIAL_CASE",
                reason_text="Revenue missing but company is marked as special case.",
                metric_name="revenue_ttm",
                metric_value=revenue_ttm,
                threshold="revenue_ttm > 0 unless special_case",
                severity="medium",
                recoverable=True,
            )
        else:
            hard_reject = True
            _add_reason(
                reasons,
                reason_code="MISSING_REVENUE",
                reason_text="Revenue missing and company is not special case.",
                metric_name="revenue_ttm",
                metric_value=revenue_ttm,
                threshold="revenue_ttm > 0",
                severity="high",
                recoverable=True,
            )
    elif revenue_ttm <= 0:
        if special_case:
            watchlist = True
            _add_reason(
                reasons,
                reason_code="REVENUE_NOT_POSITIVE_SPECIAL_CASE",
                reason_text="Revenue not positive but company is marked as special case.",
                metric_name="revenue_ttm",
                metric_value=revenue_ttm,
                threshold="revenue_ttm > 0 unless special_case",
                severity="medium",
                recoverable=True,
            )
        else:
            hard_reject = True
            _add_reason(
                reasons,
                reason_code="REVENUE_NOT_POSITIVE",
                reason_text="Revenue is not positive.",
                metric_name="revenue_ttm",
                metric_value=revenue_ttm,
                threshold="> 0",
                severity="high",
                recoverable=False,
            )

    # Operating margin
    if operating_margin is None:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="MISSING_OPERATING_MARGIN",
            reason_text="Operating margin missing.",
            metric_name="operating_margin",
            metric_value=operating_margin,
            threshold="required for clean pass",
            severity="medium",
            recoverable=True,
        )
    elif operating_margin < cfg["min_operating_margin_watchlist"]:
        if special_case or growth_exception:
            watchlist = True
            _add_reason(
                reasons,
                reason_code="OPERATING_MARGIN_TOO_NEGATIVE_BUT_RECOVERABLE",
                reason_text="Operating margin is very negative, but company has special/growth exception.",
                metric_name="operating_margin",
                metric_value=operating_margin,
                threshold=cfg["min_operating_margin_watchlist"],
                severity="medium",
                recoverable=True,
            )
        else:
            hard_reject = True
            _add_reason(
                reasons,
                reason_code="OPERATING_MARGIN_TOO_NEGATIVE",
                reason_text="Operating margin below Stage 2 minimum.",
                metric_name="operating_margin",
                metric_value=operating_margin,
                threshold=cfg["min_operating_margin_watchlist"],
                severity="high",
                recoverable=True,
            )
    elif operating_margin < cfg["min_operating_margin_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="OPERATING_MARGIN_WATCHLIST_RANGE",
            reason_text="Operating margin below pass threshold but above rejection threshold.",
            metric_name="operating_margin",
            metric_value=operating_margin,
            threshold=cfg["min_operating_margin_pass"],
            severity="medium",
            recoverable=True,
        )

    # FCF margin
    if fcf_margin is None:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="MISSING_FCF_MARGIN",
            reason_text="FCF margin missing.",
            metric_name="fcf_margin",
            metric_value=fcf_margin,
            threshold="required for clean pass",
            severity="medium",
            recoverable=True,
        )
    elif fcf_margin < cfg["min_fcf_margin_watchlist"]:
        if special_case or growth_exception:
            watchlist = True
            _add_reason(
                reasons,
                reason_code="FCF_MARGIN_TOO_NEGATIVE_BUT_RECOVERABLE",
                reason_text="FCF margin very negative, but company has special/growth exception.",
                metric_name="fcf_margin",
                metric_value=fcf_margin,
                threshold=cfg["min_fcf_margin_watchlist"],
                severity="medium",
                recoverable=True,
            )
        else:
            hard_reject = True
            _add_reason(
                reasons,
                reason_code="FCF_MARGIN_TOO_NEGATIVE",
                reason_text="FCF margin below Stage 2 minimum.",
                metric_name="fcf_margin",
                metric_value=fcf_margin,
                threshold=cfg["min_fcf_margin_watchlist"],
                severity="high",
                recoverable=True,
            )
    elif fcf_margin < cfg["min_fcf_margin_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="FCF_MARGIN_WATCHLIST_RANGE",
            reason_text="FCF margin below pass threshold but above rejection threshold.",
            metric_name="fcf_margin",
            metric_value=fcf_margin,
            threshold=cfg["min_fcf_margin_pass"],
            severity="medium",
            recoverable=True,
        )

    # Debt. Skip hard debt rule for special financial sectors.
    if net_debt_to_ebitda is None:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="MISSING_NET_DEBT_TO_EBITDA",
            reason_text="Net debt to EBITDA missing.",
            metric_name="net_debt_to_ebitda",
            metric_value=net_debt_to_ebitda,
            threshold="required for clean pass",
            severity="medium",
            recoverable=True,
        )
    elif not special_case:
        if net_debt_to_ebitda > cfg["max_net_debt_to_ebitda_watchlist"]:
            hard_reject = True
            _add_reason(
                reasons,
                reason_code="DEBT_TOO_HIGH",
                reason_text="Net debt to EBITDA above Stage 2 maximum.",
                metric_name="net_debt_to_ebitda",
                metric_value=net_debt_to_ebitda,
                threshold=cfg["max_net_debt_to_ebitda_watchlist"],
                severity="high",
                recoverable=True,
            )
        elif net_debt_to_ebitda > cfg["max_net_debt_to_ebitda_pass"]:
            watchlist = True
            _add_reason(
                reasons,
                reason_code="DEBT_WATCHLIST_RANGE",
                reason_text="Net debt to EBITDA above pass threshold but below rejection threshold.",
                metric_name="net_debt_to_ebitda",
                metric_value=net_debt_to_ebitda,
                threshold=cfg["max_net_debt_to_ebitda_pass"],
                severity="medium",
                recoverable=True,
            )

    # Dilution
    if shares_dilution_3y is None:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="MISSING_SHARES_DILUTION",
            reason_text="Shares dilution 3Y missing.",
            metric_name="shares_dilution_3y",
            metric_value=shares_dilution_3y,
            threshold="required for clean pass",
            severity="medium",
            recoverable=True,
        )
    elif shares_dilution_3y > cfg["max_shares_dilution_3y_watchlist"]:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="HIGH_DILUTION",
            reason_text="Shares dilution 3Y above Stage 2 maximum.",
            metric_name="shares_dilution_3y",
            metric_value=shares_dilution_3y,
            threshold=cfg["max_shares_dilution_3y_watchlist"],
            severity="high",
            recoverable=True,
        )
    elif shares_dilution_3y > cfg["max_shares_dilution_3y_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="DILUTION_WATCHLIST_RANGE",
            reason_text="Shares dilution 3Y above pass threshold but below rejection threshold.",
            metric_name="shares_dilution_3y",
            metric_value=shares_dilution_3y,
            threshold=cfg["max_shares_dilution_3y_pass"],
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
        "stage": "stage2",
        "status": status,
        "reason_code": reason.get("reason_code"),
        "reason_text": reason.get("reason_text"),
        "metric_name": reason.get("metric_name"),
        "metric_value": reason.get("metric_value"),
        "threshold": reason.get("threshold"),
        "severity": reason.get("severity"),
        "recoverable": reason.get("recoverable"),
        "special_case": _sector_special_case(row, DEFAULT_STAGE2_CONFIG),
        "sector": _clean_text(row.get("sector")),
        "industry": _clean_text(row.get("industry")),
        "country": _clean_text(row.get("country")),
        "market_cap": row.get("market_cap"),
        "data_date": row.get("financial_data_date"),
        "created_at": _utc_now_iso(),
    }


def run_stage2_filter(
    input_path: Path = STAGE1_PASSED_PATH,
    passed_path: Path = STAGE2_PASSED_PATH,
    watchlist_path: Path = STAGE2_WATCHLIST_PATH,
    rejected_path: Path = STAGE2_REJECTED_PATH,
    rejection_log_path: Path = STAGE2_REJECTION_LOG_PATH,
    summary_path: Path = STAGE2_SUMMARY_PATH,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run Stage 2 filter over Stage 1 PASSED universe.
    """

    ensure_funnel_directories()

    if not input_path.exists():
        raise FileNotFoundError(
            f"Stage 1 passed file not found: {input_path}. "
            "Run Phase 5C first: python -m src.run_stage1_filter"
        )

    df = pd.read_csv(input_path)
    df = ensure_stage2_columns(df)

    statuses = []
    primary_reasons = []
    all_reason_codes = []
    log_rows = []

    for _, row in df.iterrows():
        status, reasons = classify_stage2_row(row, config=config)

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
    result_df["stage2_status"] = statuses
    result_df["stage2_primary_reason"] = primary_reasons
    result_df["stage2_all_reasons"] = all_reason_codes

    passed_df = result_df[result_df["stage2_status"] == "PASSED"].copy()
    watchlist_df = result_df[result_df["stage2_status"] == "WATCHLIST"].copy()
    rejected_df = result_df[result_df["stage2_status"] == "REJECTED"].copy()

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
        "phase": "5D",
        "stage": "stage2",
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
            for key, value in DEFAULT_STAGE2_CONFIG.items()
        },
    }

    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return summary


def print_stage2_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 5D Stage 2 financial sanity check")
    print("=" * 64)
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
