"""
Scout Finance — Phase 5E Stage 3 opportunity scoring.

Stage 3 goal:
Score Stage 2 PASSED companies and generate final scouting candidates.

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


STAGE2_PASSED_PATH = STAGES_DIR / "stage2_passed.csv"

STAGE3_PASSED_PATH = STAGES_DIR / "stage3_passed.csv"
STAGE3_WATCHLIST_PATH = STAGES_DIR / "stage3_watchlist.csv"
STAGE3_REJECTED_PATH = STAGES_DIR / "stage3_rejected.csv"
STAGE3_REJECTION_LOG_PATH = STAGES_DIR / "stage3_rejection_log.csv"
STAGE3_SUMMARY_PATH = SCOUTING_OUTPUTS_DIR / "stage3_summary.json"

TOP_20_DEEP_RESEARCH_PATH = SCOUTING_OUTPUTS_DIR / "top_20_deep_research.csv"
TOP_50_WATCHLIST_PATH = SCOUTING_OUTPUTS_DIR / "top_50_watchlist.csv"
TOP_100_CANDIDATES_PATH = SCOUTING_OUTPUTS_DIR / "top_100_candidates.csv"
TOP_RECOVERABLE_CANDIDATES_PATH = SCOUTING_OUTPUTS_DIR / "top_recoverable_candidates.csv"


DEFAULT_STAGE3_CONFIG = {
    "target_pass_count": 450,
    "max_risk_score_pass": 7.5,
    "max_risk_score_watchlist": 8.5,
    "min_data_quality_score_pass": 5.0,
    "min_data_quality_score_watchlist": 3.5,
    "min_final_score_pass": 60.0,
    "min_final_score_watchlist": 45.0,
    "weights": {
        "business_quality_score": 0.20,
        "financial_health_score": 0.15,
        "growth_score": 0.15,
        "valuation_score": 0.15,
        "moat_proxy_score": 0.15,
        "momentum_score": 0.10,
        "data_quality_score": 0.10,
    },
    "risk_penalty_multiplier": 0.5,
    "top_deep_research_count": 20,
    "top_watchlist_count": 50,
    "top_candidates_count": 100,
    "top_recoverable_count": 100,
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


def _clip_score(value: float | None) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(10.0, float(value)))


def _scale_between(value: float | None, low: float, high: float) -> float:
    """
    Scale value to 0-10 between low and high.
    Values below low -> 0.
    Values above high -> 10.
    """
    if value is None:
        return 0.0
    if high == low:
        return 0.0
    return _clip_score(((value - low) / (high - low)) * 10.0)


def _inverse_scale_between(value: float | None, low: float, high: float) -> float:
    """
    Inverse scale to 0-10.
    low -> 10, high -> 0.
    """
    if value is None:
        return 0.0
    return _clip_score(10.0 - _scale_between(value, low, high))


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


def ensure_stage3_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure optional Stage 3 input columns exist.
    """

    result = df.copy()

    optional_columns = [
        "pe_ratio",
        "forward_pe",
        "ev_ebitda",
        "price_sales",
        "fcf_yield",
        "price_change_6m",
        "price_change_12m",
        "relative_strength_6m",
        "drawdown_from_52w_high",
    ]

    for column in optional_columns:
        if column not in result.columns:
            result[column] = pd.NA

    return result


def calculate_stage3_scores(row: pd.Series) -> dict[str, float]:
    """
    Calculate Stage 3 scoring blocks from available financial fields.

    These are pragmatic proxy scores, not final investment recommendations.
    """

    gross_margin = _to_float(row.get("gross_margin"))
    operating_margin = _to_float(row.get("operating_margin"))
    net_margin = _to_float(row.get("net_margin"))
    fcf_margin = _to_float(row.get("fcf_margin"))
    revenue_growth_1y = _to_float(row.get("revenue_growth_1y"))
    revenue_growth_3y = _to_float(row.get("revenue_growth_3y"))
    net_debt_to_ebitda = _to_float(row.get("net_debt_to_ebitda"))
    interest_coverage = _to_float(row.get("interest_coverage"))
    current_ratio = _to_float(row.get("current_ratio"))
    shares_dilution_3y = _to_float(row.get("shares_dilution_3y"))
    data_completeness_score = _to_float(row.get("data_completeness_score"))
    dollar_volume_90d = _to_float(row.get("dollar_volume_90d"))

    pe_ratio = _to_float(row.get("pe_ratio"))
    ev_ebitda = _to_float(row.get("ev_ebitda"))
    price_sales = _to_float(row.get("price_sales"))
    fcf_yield = _to_float(row.get("fcf_yield"))

    price_change_6m = _to_float(row.get("price_change_6m"))
    relative_strength_6m = _to_float(row.get("relative_strength_6m"))
    drawdown_from_52w_high = _to_float(row.get("drawdown_from_52w_high"))

    # Business quality: margins + FCF conversion proxy.
    quality_parts = [
        _scale_between(gross_margin, 0.20, 0.70),
        _scale_between(operating_margin, 0.00, 0.35),
        _scale_between(net_margin, 0.00, 0.30),
        _scale_between(fcf_margin, 0.00, 0.30),
    ]
    business_quality_score = sum(quality_parts) / len(quality_parts)

    # Financial health: leverage, interest coverage, liquidity, dilution.
    health_parts = [
        _inverse_scale_between(net_debt_to_ebitda, 0.0, 5.0),
        _scale_between(interest_coverage, 2.0, 25.0),
        _scale_between(current_ratio, 0.8, 2.0),
        _inverse_scale_between(shares_dilution_3y, -0.05, 0.30),
    ]
    financial_health_score = sum(health_parts) / len(health_parts)

    # Growth: revenue growth 1y/3y with cap to avoid rewarding extreme outliers too much.
    growth_parts = [
        _scale_between(revenue_growth_1y, -0.05, 0.25),
        _scale_between(revenue_growth_3y, 0.00, 0.25),
    ]
    growth_score = sum(growth_parts) / len(growth_parts)

    # Valuation: prefer FCF yield when available; otherwise use PE/EVEBITDA/P/S proxies.
    valuation_parts = []

    if fcf_yield is not None:
        valuation_parts.append(_scale_between(fcf_yield, 0.02, 0.10))

    if pe_ratio is not None and pe_ratio > 0:
        valuation_parts.append(_inverse_scale_between(pe_ratio, 10.0, 45.0))

    if ev_ebitda is not None and ev_ebitda > 0:
        valuation_parts.append(_inverse_scale_between(ev_ebitda, 6.0, 30.0))

    if price_sales is not None and price_sales > 0:
        valuation_parts.append(_inverse_scale_between(price_sales, 2.0, 20.0))

    if valuation_parts:
        valuation_score = sum(valuation_parts) / len(valuation_parts)
    else:
        # Neutral-low when valuation data is missing. Missing valuation should not kill a company,
        # but it should reduce confidence.
        valuation_score = 4.5

    # Risk: higher is worse. Penalize leverage, negative FCF, dilution, weak data, large drawdowns.
    risk_parts = [
        _scale_between(net_debt_to_ebitda, 0.0, 6.0),
        _inverse_scale_between(fcf_margin, -0.20, 0.20),
        _scale_between(shares_dilution_3y, -0.05, 0.40),
        _inverse_scale_between(data_completeness_score, 40.0, 100.0),
    ]

    if drawdown_from_52w_high is not None:
        # drawdown expected as negative value, e.g. -0.25.
        risk_parts.append(_scale_between(abs(drawdown_from_52w_high), 0.05, 0.60))

    risk_score = sum(risk_parts) / len(risk_parts)

    # Moat proxy: margins, FCF, stable/good growth.
    moat_parts = [
        _scale_between(gross_margin, 0.25, 0.75),
        _scale_between(operating_margin, 0.05, 0.35),
        _scale_between(fcf_margin, 0.00, 0.30),
        _scale_between(revenue_growth_3y, 0.02, 0.18),
    ]
    moat_proxy_score = sum(moat_parts) / len(moat_parts)

    # Momentum: optional. Neutral if missing.
    momentum_parts = []

    if price_change_6m is not None:
        momentum_parts.append(_scale_between(price_change_6m, -0.20, 0.40))

    if relative_strength_6m is not None:
        momentum_parts.append(_scale_between(relative_strength_6m, -0.20, 0.30))

    if drawdown_from_52w_high is not None:
        momentum_parts.append(_inverse_scale_between(abs(drawdown_from_52w_high), 0.05, 0.60))

    momentum_score = sum(momentum_parts) / len(momentum_parts) if momentum_parts else 5.0

    # Liquidity: dollar volume proxy.
    liquidity_score = _scale_between(dollar_volume_90d, 500_000, 50_000_000)

    # Data quality from completeness.
    data_quality_score = _scale_between(data_completeness_score, 50.0, 100.0)

    return {
        "business_quality_score": round(_clip_score(business_quality_score), 2),
        "financial_health_score": round(_clip_score(financial_health_score), 2),
        "growth_score": round(_clip_score(growth_score), 2),
        "valuation_score": round(_clip_score(valuation_score), 2),
        "risk_score": round(_clip_score(risk_score), 2),
        "moat_proxy_score": round(_clip_score(moat_proxy_score), 2),
        "momentum_score": round(_clip_score(momentum_score), 2),
        "liquidity_score": round(_clip_score(liquidity_score), 2),
        "data_quality_score": round(_clip_score(data_quality_score), 2),
    }


def calculate_final_stage3_score(scores: dict[str, float], config: dict[str, Any] | None = None) -> float:
    cfg = config or DEFAULT_STAGE3_CONFIG
    weights = cfg["weights"]

    weighted_score_0_10 = 0.0

    for score_name, weight in weights.items():
        weighted_score_0_10 += scores.get(score_name, 0.0) * weight

    final_score_0_100 = weighted_score_0_10 * 10.0
    final_score_0_100 -= scores.get("risk_score", 0.0) * cfg["risk_penalty_multiplier"]

    return round(max(0.0, min(100.0, final_score_0_100)), 2)


def classify_stage3_company(
    row: pd.Series,
    scores: dict[str, float],
    final_score: float,
    config: dict[str, Any] | None = None,
) -> tuple[str, str, list[dict[str, Any]]]:
    """
    Return status, category, reasons.
    """

    cfg = config or DEFAULT_STAGE3_CONFIG
    reasons: list[dict[str, Any]] = []

    risk_score = scores["risk_score"]
    data_quality_score = scores["data_quality_score"]
    valuation_score = scores["valuation_score"]
    business_quality_score = scores["business_quality_score"]
    moat_proxy_score = scores["moat_proxy_score"]

    if risk_score > cfg["max_risk_score_watchlist"]:
        _add_reason(
            reasons,
            reason_code="HIGH_RISK_SCORE",
            reason_text="Risk score is too high for Stage 3.",
            metric_name="risk_score",
            metric_value=risk_score,
            threshold=cfg["max_risk_score_watchlist"],
            severity="high",
            recoverable=True,
        )
        return "REJECTED", "🔴 Descartada por scoring", reasons

    if data_quality_score < cfg["min_data_quality_score_watchlist"]:
        _add_reason(
            reasons,
            reason_code="LOW_DATA_QUALITY",
            reason_text="Data quality score is too low for Stage 3.",
            metric_name="data_quality_score",
            metric_value=data_quality_score,
            threshold=cfg["min_data_quality_score_watchlist"],
            severity="high",
            recoverable=True,
        )
        return "REJECTED", "🔴 Descartada por scoring", reasons

    if final_score < cfg["min_final_score_watchlist"]:
        _add_reason(
            reasons,
            reason_code="LOW_FINAL_SCORE",
            reason_text="Final Stage 3 score below watchlist threshold.",
            metric_name="final_stage3_score",
            metric_value=final_score,
            threshold=cfg["min_final_score_watchlist"],
            severity="medium",
            recoverable=True,
        )
        return "REJECTED", "🔴 Descartada por scoring", reasons

    watchlist = False

    if risk_score > cfg["max_risk_score_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="RISK_SCORE_WATCHLIST_RANGE",
            reason_text="Risk score above clean pass threshold.",
            metric_name="risk_score",
            metric_value=risk_score,
            threshold=cfg["max_risk_score_pass"],
            severity="medium",
            recoverable=True,
        )

    if data_quality_score < cfg["min_data_quality_score_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="DATA_QUALITY_WATCHLIST_RANGE",
            reason_text="Data quality score below clean pass threshold.",
            metric_name="data_quality_score",
            metric_value=data_quality_score,
            threshold=cfg["min_data_quality_score_pass"],
            severity="medium",
            recoverable=True,
        )

    if final_score < cfg["min_final_score_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="FINAL_SCORE_WATCHLIST_RANGE",
            reason_text="Final score below clean pass threshold.",
            metric_name="final_stage3_score",
            metric_value=final_score,
            threshold=cfg["min_final_score_pass"],
            severity="medium",
            recoverable=True,
        )

    if watchlist:
        if data_quality_score < cfg["min_data_quality_score_pass"]:
            return "WATCHLIST", "⚫ Datos insuficientes pero potencial", reasons
        if risk_score > cfg["max_risk_score_pass"]:
            return "WATCHLIST", "🟠 Riesgo elevado / revisar con cuidado", reasons
        return "WATCHLIST", "🟡 Interesante con condiciones", reasons

    if business_quality_score >= 7.0 and moat_proxy_score >= 7.0 and valuation_score < 5.0:
        return "PASSED", "🔵 Alta calidad pero valoración exigente", reasons

    if final_score >= 70.0 and business_quality_score >= 6.5:
        return "PASSED", "🟢 Candidata fuerte para scouting", reasons

    return "PASSED", "🟡 Interesante con condiciones", reasons


def _build_rejection_log_row(
    row: pd.Series,
    status: str,
    reason: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ticker": _clean_text(row.get("ticker")).upper(),
        "name": _clean_text(row.get("name")),
        "stage": "stage3",
        "status": status,
        "reason_code": reason.get("reason_code"),
        "reason_text": reason.get("reason_text"),
        "metric_name": reason.get("metric_name"),
        "metric_value": reason.get("metric_value"),
        "threshold": reason.get("threshold"),
        "severity": reason.get("severity"),
        "recoverable": reason.get("recoverable"),
        "special_case": row.get("special_case", False),
        "sector": _clean_text(row.get("sector")),
        "industry": _clean_text(row.get("industry")),
        "country": _clean_text(row.get("country")),
        "market_cap": row.get("market_cap"),
        "data_date": row.get("financial_data_date"),
        "created_at": _utc_now_iso(),
    }


def run_stage3_scoring(
    input_path: Path = STAGE2_PASSED_PATH,
    passed_path: Path = STAGE3_PASSED_PATH,
    watchlist_path: Path = STAGE3_WATCHLIST_PATH,
    rejected_path: Path = STAGE3_REJECTED_PATH,
    rejection_log_path: Path = STAGE3_REJECTION_LOG_PATH,
    summary_path: Path = STAGE3_SUMMARY_PATH,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run Stage 3 scoring over Stage 2 PASSED universe.
    """

    ensure_funnel_directories()

    if not input_path.exists():
        raise FileNotFoundError(
            f"Stage 2 passed file not found: {input_path}. "
            "Run Phase 5D first: python -m src.run_stage2_filter"
        )

    cfg = config or DEFAULT_STAGE3_CONFIG

    df = pd.read_csv(input_path)
    df = ensure_stage3_columns(df)

    score_rows = []
    statuses = []
    categories = []
    primary_reasons = []
    all_reason_codes = []
    log_rows = []

    for _, row in df.iterrows():
        scores = calculate_stage3_scores(row)
        final_score = calculate_final_stage3_score(scores, config=cfg)
        status, category, reasons = classify_stage3_company(row, scores, final_score, config=cfg)

        score_rows.append({**scores, "final_stage3_score": final_score})
        statuses.append(status)
        categories.append(category)

        if reasons:
            primary_reasons.append(reasons[0]["reason_code"])
            all_reason_codes.append("|".join(reason["reason_code"] for reason in reasons))
        else:
            primary_reasons.append("")
            all_reason_codes.append("")

        for reason in reasons:
            log_rows.append(_build_rejection_log_row(row, status, reason))

    score_df = pd.DataFrame(score_rows)
    result_df = pd.concat([df.reset_index(drop=True), score_df.reset_index(drop=True)], axis=1)

    result_df["stage3_status"] = statuses
    result_df["stage3_category"] = categories
    result_df["stage3_primary_reason"] = primary_reasons
    result_df["stage3_all_reasons"] = all_reason_codes

    result_df = result_df.sort_values("final_stage3_score", ascending=False)

    passed_df = result_df[result_df["stage3_status"] == "PASSED"].copy()
    watchlist_df = result_df[result_df["stage3_status"] == "WATCHLIST"].copy()
    rejected_df = result_df[result_df["stage3_status"] == "REJECTED"].copy()

    passed_df.to_csv(passed_path, index=False, encoding="utf-8-sig")
    watchlist_df.to_csv(watchlist_path, index=False, encoding="utf-8-sig")
    rejected_df.to_csv(rejected_path, index=False, encoding="utf-8-sig")

    log_df = pd.DataFrame(log_rows, columns=REJECTION_COLUMNS)
    log_df.to_csv(rejection_log_path, index=False, encoding="utf-8-sig")

    # Final scouting outputs.
    top_candidates = pd.concat([passed_df, watchlist_df], ignore_index=True)
    top_candidates = top_candidates.sort_values("final_stage3_score", ascending=False)

    top_candidates.head(cfg["top_deep_research_count"]).to_csv(
        TOP_20_DEEP_RESEARCH_PATH,
        index=False,
        encoding="utf-8-sig",
    )
    top_candidates.head(cfg["top_watchlist_count"]).to_csv(
        TOP_50_WATCHLIST_PATH,
        index=False,
        encoding="utf-8-sig",
    )
    top_candidates.head(cfg["top_candidates_count"]).to_csv(
        TOP_100_CANDIDATES_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    recoverable_df = pd.concat([watchlist_df, rejected_df], ignore_index=True)
    if "stage3_primary_reason" in recoverable_df.columns:
        recoverable_df = recoverable_df[
            recoverable_df["stage3_primary_reason"].astype(str).str.len() > 0
        ]
    recoverable_df.sort_values("final_stage3_score", ascending=False).head(
        cfg["top_recoverable_count"]
    ).to_csv(
        TOP_RECOVERABLE_CANDIDATES_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    input_count = int(len(result_df))
    passed_count = int(len(passed_df))
    watchlist_count = int(len(watchlist_df))
    rejected_count = int(len(rejected_df))

    top_reasons = (
        log_df["reason_code"].value_counts().head(20).to_dict()
        if not log_df.empty
        else {}
    )

    category_distribution = (
        result_df["stage3_category"].value_counts().to_dict()
        if "stage3_category" in result_df.columns
        else {}
    )

    summary = {
        "phase": "5E",
        "stage": "stage3",
        "created_at": _utc_now_iso(),
        "input_companies": input_count,
        "passed_companies": passed_count,
        "watchlist_companies": watchlist_count,
        "rejected_companies": rejected_count,
        "pass_rate": passed_count / input_count if input_count else 0,
        "watchlist_rate": watchlist_count / input_count if input_count else 0,
        "rejection_rate": rejected_count / input_count if input_count else 0,
        "category_distribution": category_distribution,
        "top_rejection_or_watchlist_reasons": top_reasons,
        "top_company": (
            result_df.iloc[0][["ticker", "name", "final_stage3_score", "stage3_category"]].to_dict()
            if not result_df.empty
            else None
        ),
        "output_files": {
            "passed": str(passed_path),
            "watchlist": str(watchlist_path),
            "rejected": str(rejected_path),
            "rejection_log": str(rejection_log_path),
            "summary": str(summary_path),
            "top_20_deep_research": str(TOP_20_DEEP_RESEARCH_PATH),
            "top_50_watchlist": str(TOP_50_WATCHLIST_PATH),
            "top_100_candidates": str(TOP_100_CANDIDATES_PATH),
            "top_recoverable_candidates": str(TOP_RECOVERABLE_CANDIDATES_PATH),
        },
        "config": cfg,
    }

    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return summary


def print_stage3_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 5E Stage 3 opportunity scoring")
    print("=" * 64)
    print(f"Input companies: {summary.get('input_companies')}")
    print(f"PASSED: {summary.get('passed_companies')}")
    print(f"WATCHLIST: {summary.get('watchlist_companies')}")
    print(f"REJECTED: {summary.get('rejected_companies')}")
    print(f"Pass rate: {summary.get('pass_rate'):.2%}")
    print(f"Watchlist rate: {summary.get('watchlist_rate'):.2%}")
    print(f"Rejection rate: {summary.get('rejection_rate'):.2%}")

    top_company = summary.get("top_company")
    if top_company:
        print()
        print("Top company:")
        print(f"- {top_company.get('ticker')} | {top_company.get('name')} | "
              f"score={top_company.get('final_stage3_score')} | {top_company.get('stage3_category')}")

    print()
    print("Output files:")
    for label, path in summary.get("output_files", {}).items():
        print(f"- {label}: {path}")
