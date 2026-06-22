"""Validation for Scout Finance structured analysis JSON."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from src.analysis_schema import (
    ALLOWED_CONFIDENCE_LEVELS, ALLOWED_FINAL_CATEGORIES, MOAT_FIELDS,
    REQUIRED_FINAL_RESULT_FIELDS, REQUIRED_SCENARIO_FIELDS, REQUIRED_SCENARIO_KEYS,
    REQUIRED_SOURCE_FIELDS, REQUIRED_TOP_LEVEL_FIELDS, SCORE_FIELDS,
)

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

def _num_or_none(v: Any) -> bool:
    return v is None or (not isinstance(v, bool) and isinstance(v, (int, float)))

def _score(v: Any) -> bool:
    return v is None or (_num_or_none(v) and 0 <= float(v) <= 10)

def _prob(v: Any) -> bool:
    return v is None or (_num_or_none(v) and 0 <= float(v) <= 100)

def validate_analysis_json(data: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return ValidationResult(False, ["analysis_json_must_be_object"], [])

    for f in REQUIRED_TOP_LEVEL_FIELDS:
        if f not in data:
            errors.append(f"missing_top_level_field:{f}")
    if not data.get("ticker"):
        errors.append("ticker_is_required")
    if not data.get("company_name"):
        errors.append("company_name_is_required")
    if not data.get("analysis_date"):
        errors.append("analysis_date_is_required")
    if not isinstance(data.get("revenue_streams"), list):
        errors.append("revenue_streams_must_be_list")

    scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    if not isinstance(data.get("scores"), dict):
        errors.append("scores_must_be_object")
    for f in SCORE_FIELDS:
        if f not in scores:
            errors.append(f"missing_score:{f}")
        elif not _score(scores.get(f)):
            errors.append(f"invalid_score_0_10_or_null:{f}")

    evidence = scores.get("evidence_quality_score")
    freshness = scores.get("data_freshness_score")
    confidence = scores.get("confidence_score")
    if evidence is not None and confidence is not None and float(evidence) <= 4 and float(confidence) >= 7:
        errors.append("confidence_score_too_high_for_low_evidence_quality")
    if freshness is not None and confidence is not None and float(freshness) <= 4 and float(confidence) >= 7:
        errors.append("confidence_score_too_high_for_stale_data")

    moat = data.get("moat_breakdown") if isinstance(data.get("moat_breakdown"), dict) else {}
    if not isinstance(data.get("moat_breakdown"), dict):
        errors.append("moat_breakdown_must_be_object")
    for f in MOAT_FIELDS:
        if f not in moat:
            errors.append(f"missing_moat_field:{f}")
        elif not _score(moat.get(f)):
            errors.append(f"invalid_moat_score_0_10_or_null:{f}")

    valuation = data.get("valuation_summary")
    if not isinstance(valuation, dict):
        errors.append("valuation_summary_must_be_object")
    elif not _score(valuation.get("valuation_confidence")):
        errors.append("valuation_confidence_must_be_0_10_or_null")

    risk_analysis = data.get("risk_analysis") if isinstance(data.get("risk_analysis"), dict) else {}
    if not isinstance(data.get("risk_analysis"), dict):
        errors.append("risk_analysis_must_be_object")
    main_risks = risk_analysis.get("main_risks")
    if not isinstance(main_risks, list):
        errors.append("main_risks_must_be_list")
    else:
        for i, risk in enumerate(main_risks):
            if not isinstance(risk, dict):
                errors.append(f"main_risk_must_be_object:{i}")
                continue
            for rf in ["risk", "probability", "impact", "severity", "comment"]:
                if rf not in risk:
                    errors.append(f"missing_risk_field:{i}:{rf}")

    scenarios = data.get("scenarios") if isinstance(data.get("scenarios"), dict) else {}
    if not isinstance(data.get("scenarios"), dict):
        errors.append("scenarios_must_be_object")
    probs: list[float] = []
    for key in REQUIRED_SCENARIO_KEYS:
        sc = scenarios.get(key)
        if not isinstance(sc, dict):
            errors.append(f"missing_or_invalid_scenario:{key}")
            continue
        for sf in REQUIRED_SCENARIO_FIELDS:
            if sf not in sc:
                errors.append(f"missing_scenario_field:{key}:{sf}")
        if not isinstance(sc.get("key_assumptions"), list):
            errors.append(f"scenario_key_assumptions_must_be_list:{key}")
        p = sc.get("probability")
        if not _prob(p):
            errors.append(f"invalid_scenario_probability:{key}")
        elif p is not None:
            probs.append(float(p))
    if len(probs) == 3 and round(sum(probs), 2) != 100:
        errors.append(f"scenario_probabilities_must_sum_100:got_{round(sum(probs),2)}")
    elif len(probs) != 3:
        warnings.append("scenario_probabilities_incomplete_or_partially_missing")

    if not isinstance(data.get("dividend_analysis"), dict):
        errors.append("dividend_analysis_must_be_object")

    final = data.get("final_result") if isinstance(data.get("final_result"), dict) else {}
    if not isinstance(data.get("final_result"), dict):
        errors.append("final_result_must_be_object")
    for f in REQUIRED_FINAL_RESULT_FIELDS:
        if f not in final:
            errors.append(f"missing_final_result_field:{f}")
    if final.get("final_category") not in ALLOWED_FINAL_CATEGORIES:
        errors.append("invalid_final_category")
    if final.get("confidence_level") not in ALLOWED_CONFIDENCE_LEVELS:
        errors.append("invalid_confidence_level")

    sources = data.get("sources") if isinstance(data.get("sources"), dict) else {}
    if not isinstance(data.get("sources"), dict):
        errors.append("sources_must_be_object")
    for f in REQUIRED_SOURCE_FIELDS:
        if f not in sources:
            errors.append(f"missing_sources_field:{f}")
        elif not isinstance(sources.get(f), list):
            errors.append(f"sources_field_must_be_list:{f}")
    if isinstance(sources.get("source_warnings"), list) and sources.get("source_warnings"):
        warnings.append("source_warnings_present")
    if isinstance(sources.get("data_limitations"), list) and sources.get("data_limitations"):
        warnings.append("data_limitations_present")
    return ValidationResult(len(errors) == 0, errors, warnings)

def raise_if_invalid_analysis_json(data: dict[str, Any]) -> None:
    result = validate_analysis_json(data)
    if not result.is_valid:
        raise ValueError(f"Structured analysis JSON validation failed.\nErrors: {result.errors}\nWarnings: {result.warnings}")
