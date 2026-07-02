from __future__ import annotations

from pathlib import Path


SRC = Path("src/combined_scoring_v1.py")

HELPER_MARKER = "# >>> v1.6E5 FUNDAMENTALS GRANULAR TIE-BREAKER HELPERS"

HELPERS = r'''
# >>> v1.6E5 FUNDAMENTALS GRANULAR TIE-BREAKER HELPERS
def revenue_scale_detail_score(revenue: float) -> float:
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


def growth_detail_score(growth: float) -> float:
    return clamp(50 + growth * 4, 0, 100)


def margin_detail_score(margin: float, excellent: float) -> float:
    if excellent <= 0:
        return 0.0
    return clamp((margin / excellent) * 100, 0, 100)


def fcf_scale_detail_score(fcf: float) -> float:
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


def balance_sheet_detail_score(cash: float, debt: float) -> float:
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


def fundamentals_granular_score_v1_6e(fundamentals: dict[str, object] | None) -> float:
    """Non-production granular fundamentals score used only for exact tie-breaking."""
    if not fundamentals:
        return 0.0

    revenue = as_float(fundamentals.get("revenue"), 0) or 0.0
    growth = as_float(fundamentals.get("revenue_growth_yoy"), 0) or 0.0
    gross = as_float(fundamentals.get("gross_margin"), 0) or 0.0
    operating = as_float(fundamentals.get("operating_margin"), 0) or 0.0
    net = as_float(fundamentals.get("net_margin"), 0) or 0.0
    fcf = as_float(fundamentals.get("free_cash_flow"), 0) or 0.0
    cash = as_float(fundamentals.get("total_cash"), 0) or 0.0
    debt = as_float(fundamentals.get("total_debt"), 0) or 0.0

    score = (
        revenue_scale_detail_score(revenue) * 0.15
        + growth_detail_score(growth) * 0.20
        + margin_detail_score(gross, 65.0) * 0.15
        + margin_detail_score(operating, 40.0) * 0.15
        + margin_detail_score(net, 35.0) * 0.10
        + fcf_scale_detail_score(fcf) * 0.15
        + balance_sheet_detail_score(cash, debt) * 0.10
    )

    return round(clamp(score, 0, 100), 2)


def exact_component_tie_key(row: dict[str, object]) -> tuple[float, float, float, float]:
    return (
        round(as_float(row.get("combined_score_v1"), 0) or 0.0, 4),
        round(as_float(row.get("metadata_score_component"), 0) or 0.0, 4),
        round(as_float(row.get("market_data_score_component"), 0) or 0.0, 4),
        round(as_float(row.get("fundamentals_score_component"), 0) or 0.0, 4),
    )


def annotate_exact_component_ties(rows: list[dict[str, object]]) -> None:
    counts: dict[tuple[float, float, float, float], int] = {}

    for row in rows:
        key = exact_component_tie_key(row)
        counts[key] = counts.get(key, 0) + 1

    for row in rows:
        key = exact_component_tie_key(row)
        is_tie = counts.get(key, 0) > 1
        row["tie_status"] = "EXACT_COMPONENT_TIE" if is_tie else "NO_TIE"
        row["calibration_warning"] = (
            "Empate exacto de componentes; orden secundario por granularidad fundamental."
            if is_tie
            else ""
        )
# <<< v1.6E5 FUNDAMENTALS GRANULAR TIE-BREAKER HELPERS
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Block not found: {label}")
    return text.replace(old, new, 1)


def main() -> int:
    text = SRC.read_text(encoding="utf-8")

    if "# v1.6E5 fundamentals granular tie-breaker packaged" not in text:
        text = "# v1.6E5 fundamentals granular tie-breaker packaged\n" + text

    if HELPER_MARKER not in text:
        anchor = "def category(score: float) -> str:"
        idx = text.find(anchor)
        if idx == -1:
            raise RuntimeError("Could not find helper anchor: def category(score: float) -> str:")
        text = text[:idx] + HELPERS.strip() + "\n\n\n" + text[idx:]

    if "fundamentals_granular = fundamentals_granular_score_v1_6e(f)" not in text:
        text = replace_once(
            text,
            '''        f_score, f_pos, f_neg = fundamentals_score(f)

        combined = round(clamp((m_score * 0.20) + (md_score * 0.35) + (f_score * 0.45)), 2)
''',
            '''        f_score, f_pos, f_neg = fundamentals_score(f)
        fundamentals_granular = fundamentals_granular_score_v1_6e(f)

        combined = round(clamp((m_score * 0.20) + (md_score * 0.35) + (f_score * 0.45)), 2)
''',
            "add fundamentals_granular calculation",
        )

    if 'out["fundamentals_granular_score_v1_6e"] = fundamentals_granular' not in text:
        text = replace_once(
            text,
            '''        out["fundamentals_score_component"] = f_score
''',
            '''        out["fundamentals_score_component"] = f_score
        out["fundamentals_granular_score_v1_6e"] = fundamentals_granular
''',
            "add granular score to output row",
        )

    if '"fundamentals_granular_score_v1_6e": fundamentals_granular' not in text:
        text = replace_once(
            text,
            '''            "fundamentals_score_component": f_score,
            "combined_score_v1": combined,
''',
            '''            "fundamentals_score_component": f_score,
            "fundamentals_granular_score_v1_6e": fundamentals_granular,
            "combined_score_v1": combined,
''',
            "add granular score to breakdown row",
        )

    if "annotate_exact_component_ties(output_rows)" not in text:
        text = replace_once(
            text,
            '''    output_rows.sort(key=lambda r: as_float(r.get("combined_score_v1"), 0) or 0, reverse=True)
    breakdown_rows.sort(key=lambda r: as_float(r.get("combined_score_v1"), 0) or 0, reverse=True)
''',
            '''    annotate_exact_component_ties(output_rows)
    annotate_exact_component_ties(breakdown_rows)

    output_rows.sort(
        key=lambda r: (
            as_float(r.get("combined_score_v1"), 0) or 0,
            as_float(r.get("fundamentals_granular_score_v1_6e"), 0) or 0,
            str(r.get("ticker", "")),
        ),
        reverse=True,
    )
    breakdown_rows.sort(
        key=lambda r: (
            as_float(r.get("combined_score_v1"), 0) or 0,
            as_float(r.get("fundamentals_granular_score_v1_6e"), 0) or 0,
            str(r.get("ticker", "")),
        ),
        reverse=True,
    )
''',
            "replace sort block",
        )

    # v1.6E5: report enrichment skipped because report layout varies between versions.
    # Core calibration fields are added to CSV outputs and active ranking.

    SRC.write_text(text, encoding="utf-8")

    print("Scout Finance ? v1.6E5 Fundamentals Granular Tie-breaker")
    print("=" * 92)
    print("OK   src/combined_scoring_v1.py updated")
    print("OK   combined_score_v1 unchanged")
    print("OK   Added fundamentals_granular_score_v1_6e")
    print("OK   Added tie_status/calibration_warning")
    print("OK   Exact ties sorted by granular fundamentals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
