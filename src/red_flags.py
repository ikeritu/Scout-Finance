from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional


ALLOWED_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
ALLOWED_CATEGORIES = {
    "debt",
    "margins",
    "fcf",
    "dilution",
    "data_quality",
    "risk",
    "valuation",
    "growth",
    "financial_deterioration",
    "source_quality",
}


@dataclass(frozen=True)
class RedFlag:
    category: str
    severity: str
    code: str
    title: str
    detail: str
    evidence: Dict[str, Any]
    source: str


def _num(value: Any) -> Optional[float]:
    if value in (None, "", "nan", "NaN"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def make_flag(
    *,
    category: str,
    severity: str,
    code: str,
    title: str,
    detail: str,
    evidence: Dict[str, Any],
    source: str,
) -> RedFlag:
    if category not in ALLOWED_CATEGORIES:
        category = "source_quality"
    if severity not in ALLOWED_SEVERITIES:
        severity = "MEDIUM"
    return RedFlag(
        category=category,
        severity=severity,
        code=code,
        title=title,
        detail=detail,
        evidence=evidence,
        source=source,
    )


def flags_to_dicts(flags: Iterable[RedFlag]) -> List[Dict[str, Any]]:
    return [asdict(flag) for flag in flags]


def severity_score(severity: str) -> int:
    return {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }.get(severity, 0)


def summarize_flags(flags: Iterable[RedFlag]) -> Dict[str, Any]:
    items = list(flags)
    by_severity: Dict[str, int] = {key: 0 for key in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}
    by_category: Dict[str, int] = {}
    for flag in items:
        by_severity[flag.severity] = by_severity.get(flag.severity, 0) + 1
        by_category[flag.category] = by_category.get(flag.category, 0) + 1

    max_severity = "LOW"
    if items:
        max_severity = max((flag.severity for flag in items), key=severity_score)

    return {
        "red_flag_count": len(items),
        "by_severity": by_severity,
        "by_category": by_category,
        "max_severity": max_severity,
        "has_high_or_critical": any(flag.severity in {"HIGH", "CRITICAL"} for flag in items),
    }


def detect_from_stage_status(row: Dict[str, Any]) -> List[RedFlag]:
    flags: List[RedFlag] = []

    for stage in ["stage1", "stage2", "stage3"]:
        status = _text(row.get(f"{stage}_status") or row.get(f"{stage}_decision")).upper()
        label = _text(row.get(f"{stage}_label") or "")
        reasons = _text(row.get(f"{stage}_reasons") or row.get("reasons") or "")

        if status == "REJECTED":
            flags.append(make_flag(
                category="risk",
                severity="HIGH",
                code=f"{stage.upper()}_REJECTED",
                title=f"{stage.upper()} rejected",
                detail=f"{stage.upper()} status is REJECTED.",
                evidence={"status": status, "label": label, "reasons": reasons},
                source="stage_status",
            ))
        elif status == "WATCHLIST":
            flags.append(make_flag(
                category="risk",
                severity="MEDIUM",
                code=f"{stage.upper()}_WATCHLIST",
                title=f"{stage.upper()} watchlist",
                detail=f"{stage.upper()} status is WATCHLIST.",
                evidence={"status": status, "label": label, "reasons": reasons},
                source="stage_status",
            ))

    return flags


def detect_from_metrics(row: Dict[str, Any]) -> List[RedFlag]:
    flags: List[RedFlag] = []

    net_debt_to_ebitda = _num(row.get("net_debt_to_ebitda"))
    if net_debt_to_ebitda is not None:
        if net_debt_to_ebitda > 5:
            flags.append(make_flag(
                category="debt",
                severity="HIGH",
                code="DEBT_NET_DEBT_EBITDA_GT_5",
                title="Elevated leverage",
                detail="Net debt to EBITDA is above 5.",
                evidence={"net_debt_to_ebitda": net_debt_to_ebitda, "threshold": 5},
                source="metric",
            ))
        elif net_debt_to_ebitda > 3:
            flags.append(make_flag(
                category="debt",
                severity="MEDIUM",
                code="DEBT_NET_DEBT_EBITDA_GT_3",
                title="Leverage needs review",
                detail="Net debt to EBITDA is above 3.",
                evidence={"net_debt_to_ebitda": net_debt_to_ebitda, "threshold": 3},
                source="metric",
            ))

    operating_margin = _num(row.get("operating_margin"))
    if operating_margin is not None:
        if operating_margin < -0.20:
            flags.append(make_flag(
                category="margins",
                severity="HIGH",
                code="OPERATING_MARGIN_LT_NEG_20",
                title="Very weak operating margin",
                detail="Operating margin is below -20%.",
                evidence={"operating_margin": operating_margin, "threshold": -0.20},
                source="metric",
            ))
        elif operating_margin < 0:
            flags.append(make_flag(
                category="margins",
                severity="MEDIUM",
                code="OPERATING_MARGIN_NEGATIVE",
                title="Negative operating margin",
                detail="Operating margin is negative.",
                evidence={"operating_margin": operating_margin, "threshold": 0},
                source="metric",
            ))

    fcf_margin = _num(row.get("fcf_margin"))
    if fcf_margin is not None:
        if fcf_margin < -0.10:
            flags.append(make_flag(
                category="fcf",
                severity="HIGH",
                code="FCF_MARGIN_LT_NEG_10",
                title="Very weak free cash flow margin",
                detail="FCF margin is below -10%.",
                evidence={"fcf_margin": fcf_margin, "threshold": -0.10},
                source="metric",
            ))
        elif fcf_margin < 0:
            flags.append(make_flag(
                category="fcf",
                severity="MEDIUM",
                code="FCF_MARGIN_NEGATIVE",
                title="Negative free cash flow margin",
                detail="FCF margin is negative.",
                evidence={"fcf_margin": fcf_margin, "threshold": 0},
                source="metric",
            ))

    dilution = _num(row.get("shares_dilution_3y") or row.get("dilution_3y"))
    if dilution is not None:
        if dilution > 0.30:
            flags.append(make_flag(
                category="dilution",
                severity="HIGH",
                code="DILUTION_3Y_GT_30",
                title="High shareholder dilution",
                detail="3-year share dilution is above 30%.",
                evidence={"shares_dilution_3y": dilution, "threshold": 0.30},
                source="metric",
            ))
        elif dilution > 0.15:
            flags.append(make_flag(
                category="dilution",
                severity="MEDIUM",
                code="DILUTION_3Y_GT_15",
                title="Material shareholder dilution",
                detail="3-year share dilution is above 15%.",
                evidence={"shares_dilution_3y": dilution, "threshold": 0.15},
                source="metric",
            ))

    data_quality = _num(row.get("data_quality_score") or row.get("data_completeness_score"))
    if data_quality is not None:
        if data_quality < 3.5:
            flags.append(make_flag(
                category="data_quality",
                severity="HIGH",
                code="DATA_QUALITY_LOW",
                title="Low data quality",
                detail="Data quality score is below 3.5.",
                evidence={"data_quality_score": data_quality, "threshold": 3.5},
                source="metric",
            ))
        elif data_quality < 5:
            flags.append(make_flag(
                category="data_quality",
                severity="MEDIUM",
                code="DATA_QUALITY_MEDIUM_LOW",
                title="Data quality needs review",
                detail="Data quality score is below 5.",
                evidence={"data_quality_score": data_quality, "threshold": 5},
                source="metric",
            ))

    risk_score = _num(row.get("risk_score"))
    if risk_score is not None:
        if risk_score > 8.5:
            flags.append(make_flag(
                category="risk",
                severity="HIGH",
                code="RISK_SCORE_GT_8_5",
                title="High risk score",
                detail="Risk score is above 8.5.",
                evidence={"risk_score": risk_score, "threshold": 8.5},
                source="metric",
            ))
        elif risk_score > 7:
            flags.append(make_flag(
                category="risk",
                severity="MEDIUM",
                code="RISK_SCORE_GT_7",
                title="Elevated risk score",
                detail="Risk score is above 7.",
                evidence={"risk_score": risk_score, "threshold": 7},
                source="metric",
            ))

    valuation_score = _num(row.get("valuation_score"))
    if valuation_score is not None and valuation_score < 3:
        flags.append(make_flag(
            category="valuation",
            severity="MEDIUM",
            code="VALUATION_SCORE_LOW",
            title="Valuation score is weak",
            detail="Valuation score is below 3.",
            evidence={"valuation_score": valuation_score, "threshold": 3},
            source="metric",
        ))

    growth_score = _num(row.get("growth_score"))
    if growth_score is not None and growth_score < 3:
        flags.append(make_flag(
            category="growth",
            severity="MEDIUM",
            code="GROWTH_SCORE_LOW",
            title="Growth score is weak",
            detail="Growth score is below 3.",
            evidence={"growth_score": growth_score, "threshold": 3},
            source="metric",
        ))

    return flags


def detect_from_reasons(row: Dict[str, Any]) -> List[RedFlag]:
    flags: List[RedFlag] = []
    combined = " ".join(_text(value) for value in row.values()).upper()

    reason_map = [
        ("DEBT", "debt", "HIGH", "DEBT_REASON_PRESENT", "Debt-related warning detected"),
        ("OPERATING_MARGIN", "margins", "HIGH", "OPERATING_MARGIN_REASON_PRESENT", "Operating margin warning detected"),
        ("FCF_MARGIN", "fcf", "HIGH", "FCF_REASON_PRESENT", "Free cash flow warning detected"),
        ("DILUTION", "dilution", "HIGH", "DILUTION_REASON_PRESENT", "Dilution warning detected"),
        ("DATA_QUALITY", "data_quality", "HIGH", "DATA_QUALITY_REASON_PRESENT", "Data quality warning detected"),
        ("DATA_COMPLETENESS", "data_quality", "MEDIUM", "DATA_COMPLETENESS_REASON_PRESENT", "Data completeness warning detected"),
        ("RISK_SCORE", "risk", "HIGH", "RISK_SCORE_REASON_PRESENT", "Risk score warning detected"),
        ("FINAL_SCORE", "risk", "MEDIUM", "FINAL_SCORE_REASON_PRESENT", "Final score warning detected"),
        ("MARKET_CAP", "source_quality", "MEDIUM", "MARKET_CAP_REASON_PRESENT", "Market cap warning detected"),
        ("DOLLAR_VOLUME", "source_quality", "MEDIUM", "DOLLAR_VOLUME_REASON_PRESENT", "Liquidity warning detected"),
    ]

    for token, category, severity, code, title in reason_map:
        if token in combined:
            flags.append(make_flag(
                category=category,
                severity=severity,
                code=code,
                title=title,
                detail=f"Reason token `{token}` found in source row.",
                evidence={"token": token},
                source="reason_text",
            ))

    return flags


def deduplicate_flags(flags: Iterable[RedFlag]) -> List[RedFlag]:
    seen = set()
    out: List[RedFlag] = []
    for flag in flags:
        key = (flag.category, flag.code, str(flag.evidence))
        if key not in seen:
            seen.add(key)
            out.append(flag)
    return sorted(out, key=lambda flag: (-severity_score(flag.severity), flag.category, flag.code))


def detect_red_flags(row: Dict[str, Any]) -> List[RedFlag]:
    flags: List[RedFlag] = []
    flags.extend(detect_from_stage_status(row))
    flags.extend(detect_from_metrics(row))
    flags.extend(detect_from_reasons(row))
    return deduplicate_flags(flags)
