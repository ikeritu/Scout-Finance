from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path


class BacktestIntegrityError(ValueError):
    """Raised when an input could make a historical result misleading."""


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def information_date(record: dict) -> str:
    """Return a verifiable availability date; retrieval time is never PIT evidence."""
    value = record.get("publication_date") or record.get("filing_date")
    if not value:
        raise BacktestIntegrityError("missing_verified_publication_date")
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise BacktestIntegrityError("invalid_publication_date") from exc
    return value


def assert_point_in_time(record: dict, signal_date: str) -> None:
    available = information_date(record)
    if available > signal_date:
        raise BacktestIntegrityError("lookahead_fundamental_after_signal")
    period_end = record.get("period_end")
    if period_end and period_end > signal_date:
        raise BacktestIntegrityError("lookahead_period_end_after_signal")


def select_fundamentals(records: list[dict], signal_date: str) -> dict[str, dict[str, dict]]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    blocked = 0
    for record in records:
        asset = record.get("asset_id") or record.get("pilot_id")
        metric = record.get("metric")
        if not asset or not metric or record.get("value") is None:
            continue
        try:
            assert_point_in_time(record, signal_date)
        except BacktestIntegrityError as exc:
            if str(exc) == "missing_verified_publication_date":
                blocked += 1
                continue
            if str(exc).startswith("lookahead_"):
                continue
            raise
        grouped[(asset, metric)].append(record)
    selected: dict[str, dict[str, dict]] = defaultdict(dict)
    for (asset, metric), candidates in grouped.items():
        annual = [r for r in candidates if r.get("period_type") == "annual"]
        pool = annual or candidates
        pool.sort(key=lambda r: (information_date(r), r.get("period_end") or "", r.get("record_id") or ""))
        selected[asset][metric] = pool[-1]
    selected["__audit__"] = {"blocked_missing_publication_date": {"count": blocked}}
    return dict(selected)


def execution_index(dates: list[str], signal_date: str, lag_sessions: int) -> int:
    if lag_sessions < 1:
        raise BacktestIntegrityError("same_close_execution_forbidden")
    later = [i for i, value in enumerate(dates) if value > signal_date]
    if len(later) < lag_sessions:
        raise BacktestIntegrityError("missing_future_execution_session")
    return later[lag_sessions - 1]


def midrank_percentiles(values: dict[str, float], higher_is_better: bool = True) -> dict[str, float]:
    finite = {k: float(v) for k, v in values.items() if math.isfinite(float(v))}
    ordered = sorted((v, k) for k, v in finite.items())
    groups: dict[float, list[str]] = defaultdict(list)
    for value, asset in ordered:
        groups[value].append(asset)
    result: dict[str, float] = {}
    n, position = len(ordered), 0
    for value in sorted(groups):
        assets = sorted(groups[value])
        rank = position + (len(assets) - 1) / 2
        pct = 50.0 if n == 1 else 100.0 * rank / (n - 1)
        if not higher_is_better:
            pct = 100.0 - pct
        for asset in assets:
            result[asset] = round(pct, 8)
        position += len(assets)
    return result


def portfolio_return(weights: dict[str, float], returns: dict[str, float], turnover: float, cost_bps: float) -> float:
    if cost_bps < 0:
        raise BacktestIntegrityError("negative_transaction_cost")
    if not weights or abs(sum(weights.values()) - 1.0) > 1e-9 or any(v < 0 for v in weights.values()):
        raise BacktestIntegrityError("invalid_portfolio_weights")
    if any(asset not in returns or not math.isfinite(returns[asset]) for asset in weights):
        raise BacktestIntegrityError("missing_or_invalid_asset_return")
    gross = sum(weights[a] * returns[a] for a in weights)
    return gross - turnover * cost_bps / 10000.0


def max_drawdown(period_returns: list[float]) -> float:
    wealth = peak = 1.0
    worst = 0.0
    for value in period_returns:
        if not math.isfinite(value) or value <= -1:
            raise BacktestIntegrityError("invalid_period_return")
        wealth *= 1 + value
        peak = max(peak, wealth)
        worst = min(worst, wealth / peak - 1)
    return worst


def metrics(period_returns: list[float], benchmark_returns: list[float], periods_per_year: int = 12) -> dict:
    if len(period_returns) != len(benchmark_returns) or not period_returns:
        raise BacktestIntegrityError("metric_series_length_mismatch")
    excess = [a - b for a, b in zip(period_returns, benchmark_returns)]
    cumulative = math.prod(1 + r for r in period_returns) - 1
    benchmark_cumulative = math.prod(1 + r for r in benchmark_returns) - 1
    years = len(period_returns) / periods_per_year
    annualized = (1 + cumulative) ** (1 / years) - 1 if years > 0 and cumulative > -1 else None
    volatility = statistics.stdev(period_returns) * math.sqrt(periods_per_year) if len(period_returns) > 1 else None
    tracking_error = statistics.stdev(excess) * math.sqrt(periods_per_year) if len(excess) > 1 else None
    mean_ann = statistics.fmean(period_returns) * periods_per_year
    return {
        "observations": len(period_returns),
        "cumulative_return": cumulative,
        "benchmark_cumulative_return": benchmark_cumulative,
        "excess_cumulative_return": cumulative - benchmark_cumulative,
        "annualized_return": annualized,
        "annualized_volatility": volatility,
        "sharpe_zero_rate": None if not volatility else mean_ann / volatility,
        "maximum_drawdown": max_drawdown(period_returns),
        "tracking_error": tracking_error,
        "information_ratio": None if not tracking_error else statistics.fmean(excess) * periods_per_year / tracking_error,
        "hit_rate": sum(r > 0 for r in period_returns) / len(period_returns),
    }


def spearman(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 3:
        return None
    x = midrank_percentiles({str(i): p[0] for i, p in enumerate(pairs)})
    y = midrank_percentiles({str(i): p[1] for i, p in enumerate(pairs)})
    xs, ys = list(x.values()), list(y.values())
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    numerator = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    denominator = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return None if denominator == 0 else numerator / denominator


def evidence_decision(audit: dict, gate: dict) -> str:
    if audit.get("integrity_blocked"):
        return "BLOCKED"
    required = gate["hard_requirements"]
    if (
        audit.get("oos_windows", 0) < required["minimum_out_of_sample_windows"]
        or audit.get("oos_rebalances", 0) < required["minimum_out_of_sample_rebalances"]
        or not audit.get("point_in_time_metadata_complete", False)
    ):
        return "INSUFFICIENT_EVIDENCE"
    if audit.get("lookahead_violations", 0) or audit.get("data_leakage_violations", 0):
        return "BLOCKED"
    checks = audit.get("promotion_checks", {})
    return "COMPLETED_SCOPED" if checks and all(checks.values()) else "COMPLETED_NO_PROMOTION"
