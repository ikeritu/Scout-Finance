from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FUNDAMENTALS = ROOT / "outputs" / "fundamentals" / "manual_fundamentals_valid_rows.csv"
OUT_CSV = ROOT / "outputs" / "scoring" / "fundamentals_granularity_audit_v1_6e4.csv"
OUT_MD = ROOT / "outputs" / "scoring" / "fundamentals_granularity_audit_v1_6e4.md"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def f(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0)
    except ValueError:
        return 0.0


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def revenue_scale_score(revenue: float) -> float:
    # Conservative revenue scale score.
    # 100B+ gets full scale, but values below remain differentiated.
    if revenue >= 100_000_000_000:
        return 100.0
    if revenue >= 50_000_000_000:
        return 90.0
    if revenue >= 25_000_000_000:
        return 80.0
    if revenue >= 10_000_000_000:
        return 70.0
    if revenue >= 5_000_000_000:
        return 60.0
    return 45.0


def growth_score(growth: float) -> float:
    # 15%+ excellent, 10% strong, positive modest still rewarded.
    return clamp(50 + growth * 4)


def margin_score(margin: float, excellent: float) -> float:
    # Scale relative to a high-quality threshold.
    if excellent <= 0:
        return 0.0
    return clamp((margin / excellent) * 100)


def fcf_scale_score(fcf: float) -> float:
    if fcf >= 50_000_000_000:
        return 100.0
    if fcf >= 20_000_000_000:
        return 90.0
    if fcf >= 10_000_000_000:
        return 80.0
    if fcf >= 5_000_000_000:
        return 70.0
    if fcf > 0:
        return 55.0
    return 30.0


def balance_sheet_score(cash: float, debt: float) -> float:
    if debt <= 0:
        return 100.0
    cash_to_debt = cash / debt
    if cash_to_debt >= 1.5:
        return 100.0
    if cash_to_debt >= 1.0:
        return 90.0
    if cash_to_debt >= 0.75:
        return 80.0
    if cash_to_debt >= 0.5:
        return 70.0
    return 55.0


def granular_score(row: dict[str, str]) -> dict[str, float]:
    revenue = f(row, "revenue")
    growth = f(row, "revenue_growth_yoy")
    gross = f(row, "gross_margin")
    operating = f(row, "operating_margin")
    net = f(row, "net_margin")
    fcf = f(row, "free_cash_flow")
    cash = f(row, "total_cash")
    debt = f(row, "total_debt")

    components = {
        "revenue_scale_detail": revenue_scale_score(revenue),
        "growth_detail": growth_score(growth),
        "gross_margin_detail": margin_score(gross, 65.0),
        "operating_margin_detail": margin_score(operating, 40.0),
        "net_margin_detail": margin_score(net, 35.0),
        "fcf_scale_detail": fcf_scale_score(fcf),
        "balance_sheet_detail": balance_sheet_score(cash, debt),
    }

    # Granular score: intentionally not the production score.
    weighted = (
        components["revenue_scale_detail"] * 0.15
        + components["growth_detail"] * 0.20
        + components["gross_margin_detail"] * 0.15
        + components["operating_margin_detail"] * 0.15
        + components["net_margin_detail"] * 0.10
        + components["fcf_scale_detail"] * 0.15
        + components["balance_sheet_detail"] * 0.10
    )

    components["fundamentals_granular_score_v1_6e4"] = round(clamp(weighted), 2)
    return components


def main() -> int:
    rows = load_csv(FUNDAMENTALS)
    if not rows:
        raise SystemExit(f"No rows found: {FUNDAMENTALS}")

    out_rows = []
    for row in rows:
        components = granular_score(row)
        out = {
            "ticker": row.get("ticker", ""),
            "revenue": row.get("revenue", ""),
            "revenue_growth_yoy": row.get("revenue_growth_yoy", ""),
            "gross_margin": row.get("gross_margin", ""),
            "operating_margin": row.get("operating_margin", ""),
            "net_margin": row.get("net_margin", ""),
            "free_cash_flow": row.get("free_cash_flow", ""),
            "total_cash": row.get("total_cash", ""),
            "total_debt": row.get("total_debt", ""),
            **components,
        }
        out_rows.append(out)

    ranked = sorted(
        out_rows,
        key=lambda x: float(x["fundamentals_granular_score_v1_6e4"]),
        reverse=True,
    )

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(ranked[0].keys()))
        writer.writeheader()
        writer.writerows(ranked)

    report = []
    report.append("# Scout Finance ? v1.6E4 Fundamentals Granularity Audit")
    report.append("")
    report.append("## Purpose")
    report.append("")
    report.append("This audit calculates a non-production granular fundamentals score.")
    report.append("It is intended to diagnose ties caused by capped fundamentals components.")
    report.append("")
    report.append("## Ranking by granular fundamentals")
    report.append("")

    for idx, row in enumerate(ranked, start=1):
        report.append(
            f"{idx}. **{row['ticker']}** ? granular fundamentals "
            f"{float(row['fundamentals_granular_score_v1_6e4']):.2f}"
        )
        report.append(
            f"   - Revenue scale: {float(row['revenue_scale_detail']):.2f}, "
            f"Growth: {float(row['growth_detail']):.2f}, "
            f"Gross: {float(row['gross_margin_detail']):.2f}, "
            f"Operating: {float(row['operating_margin_detail']):.2f}, "
            f"Net: {float(row['net_margin_detail']):.2f}, "
            f"FCF: {float(row['fcf_scale_detail']):.2f}, "
            f"Balance sheet: {float(row['balance_sheet_detail']):.2f}"
        )

    report.append("")
    report.append("## Interpretation")
    report.append("")
    report.append("If companies tied at fundamentals_score_component = 100 separate here,")
    report.append("the production component is too coarse or capped too early.")

    OUT_MD.write_text("\n".join(report), encoding="utf-8")

    print("Scout Finance ? v1.6E4 Fundamentals Granularity Audit")
    print("=" * 92)
    print(f"OK   Rows analyzed: {len(rows)}")
    print(f"OK   CSV written: {OUT_CSV}")
    print(f"OK   Report written: {OUT_MD}")
    print("")
    print("Granular fundamentals ranking:")
    for idx, row in enumerate(ranked, start=1):
        print(f"{idx}. {row['ticker']} ? {float(row['fundamentals_granular_score_v1_6e4']):.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
