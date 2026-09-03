#!/usr/bin/env python3
"""Build deterministic v2.38L US explained research shortlist."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38L-us-explained-shortlist"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38l_us_explained_shortlist"
SCORES = ROOT / "outputs/full_universe_source_acquisition/v2_38k_us_experimental_scoring/us_experimental_scores_v2_38k.csv"
SCORE_REPORT = ROOT / "outputs/full_universe_source_acquisition/v2_38k_us_experimental_scoring/us_experimental_score_aggregate_report_v2_38k.json"
MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38j_us_candidate_feature_matrix/us_candidate_feature_matrix_v2_38j.csv"

SHORTLIST_FIELDS = [
    "shortlist_rank", "research_rank", "asset_id", "ticker", "company_name",
    "exchange", "cik", "experimental_score", "score_bucket_38k",
    "shortlist_bucket", "candidate_matrix_status", "evidence_level",
    "inclusion_reason", "positive_drivers", "risk_drivers", "evidence_summary",
    "research_explanation", "next_research_steps", "recommendation_generated",
    "financial_advice", "broker_actions_allowed", "phase9c_authorized", "phase",
]

NOTE_FIELDS = ["asset_id", "ticker", "note_type", "note", "source_phase", "phase"]
QUALITY_FIELDS = [
    "asset_id", "ticker", "shortlist_rank", "research_rank", "experimental_score",
    "shortlist_bucket", "candidate_matrix_status", "quality_status",
    "quality_notes", "phase",
]
REJECTION_FIELDS = ["asset_id", "ticker", "company_name", "exchange", "reason", "phase"]

FORBIDDEN_TERMS = [
    "buy",
    "sell",
    "hold",
    "investment recommendation",
    "price target",
    "expected return",
    "guaranteed",
    "will rise",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"BLOCKED: required input not found: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fields})


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def as_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def as_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def shortlist_bucket(score: float) -> str:
    if score >= 75:
        return "SHORTLIST_HIGH_PRIORITY"
    if score >= 60:
        return "SHORTLIST_MEDIUM_PRIORITY"
    return "SHORTLIST_WATCHLIST"


def split_notes(value: str, fallback: str) -> list[str]:
    parts = [part.strip() for part in str(value or "").split(";") if part.strip()]
    return parts or [fallback]


def has_forbidden_language(value: str) -> bool:
    text = f" {value.lower()} "
    return any(f" {term} " in text for term in FORBIDDEN_TERMS)


def inclusion_reason(row: dict[str, str], bucket: str) -> str:
    score = row.get("experimental_score", "")
    rank = row.get("research_rank", "")
    if bucket == "SHORTLIST_HIGH_PRIORITY":
        return f"High-priority research candidate from v2.38K technical rank {rank} with experimental score {score}."
    if bucket == "SHORTLIST_MEDIUM_PRIORITY":
        return f"Medium-priority research candidate from v2.38K technical rank {rank} with experimental score {score}."
    return f"Watchlist research candidate from v2.38K technical rank {rank} with experimental score {score}."


def evidence_summary(row: dict[str, str]) -> str:
    return (
        f"Evidence level {row.get('evidence_level', 'unknown')}; "
        f"candidate status {row.get('candidate_matrix_status', 'unknown')}; "
        "derived only from local v2.38J/v2.38K artifacts."
    )


def explanation(row: dict[str, str], bucket: str) -> str:
    positive = row.get("top_positive_drivers") or "tracked positive drivers are limited"
    risks = row.get("top_risk_drivers") or "tracked risk drivers require review"
    return (
        f"This is a {bucket.lower()} research shortlist item because its complete local evidence row "
        f"received v2.38K technical rank {row.get('research_rank')} and experimental score "
        f"{row.get('experimental_score')}. Positive tracked drivers: {positive}. "
        f"Risk checks: {risks}. This output is only a research prioritization aid and needs "
        "human review of business model, valuation, filings, sector context and upcoming macro/geopolitical phase data."
    )


def next_steps(row: dict[str, str]) -> str:
    return (
        "Review latest SEC filings; inspect revenue quality and cash conversion; compare valuation manually; "
        "check sector news and macro/geopolitical exposure in the next phase."
    )


def is_eligible(row: dict[str, str], min_score: float | None) -> tuple[bool, str]:
    if row.get("candidate_matrix_status") != "CANDIDATE_MATRIX_READY":
        return False, "candidate_matrix_not_ready"
    if str(row.get("recommendation_generated", "")).lower() != "false":
        return False, "upstream_recommendation_flag_not_false"
    if as_int(row.get("research_rank")) is None:
        return False, "missing_research_rank"
    score = as_float(row.get("experimental_score"))
    if score is None:
        return False, "missing_experimental_score"
    if min_score is not None and score < min_score:
        return False, "below_min_score"
    return True, ""


def sort_key(row: dict[str, str]) -> tuple[int, float, str, str]:
    return (
        as_int(row.get("research_rank")) or 10**9,
        -(as_float(row.get("experimental_score")) or -1),
        row.get("ticker", ""),
        row.get("asset_id", ""),
    )


def build(scores_path: Path, score_report_path: Path, matrix_path: Path, output_dir: Path, limit: int, min_score: float | None) -> dict[str, Any]:
    if limit < 1 or limit > 100:
        raise SystemExit("BLOCKED: --limit must be between 1 and 100")
    output_dir.mkdir(parents=True, exist_ok=True)
    score_rows = read_csv(scores_path)
    _ = json.loads(score_report_path.read_text(encoding="utf-8")) if score_report_path.exists() else {}
    _matrix_rows = read_csv(matrix_path)

    candidates: list[dict[str, str]] = []
    rejections: list[dict[str, Any]] = []
    for row in score_rows:
        ok, reason = is_eligible(row, min_score)
        if ok:
            candidates.append(row)
        else:
            rejections.append({
                "asset_id": row.get("asset_id", ""),
                "ticker": row.get("ticker", ""),
                "company_name": row.get("company_name", ""),
                "exchange": row.get("exchange", ""),
                "reason": reason,
                "phase": PHASE,
            })

    candidates.sort(key=sort_key)
    selected = candidates[:limit]
    shortlist: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    quality: list[dict[str, Any]] = []

    for index, row in enumerate(selected, 1):
        score = as_float(row.get("experimental_score")) or 0.0
        bucket = shortlist_bucket(score)
        out = {
            "shortlist_rank": index,
            "research_rank": row.get("research_rank", ""),
            "asset_id": row.get("asset_id", ""),
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "exchange": row.get("exchange", ""),
            "cik": row.get("cik", ""),
            "experimental_score": row.get("experimental_score", ""),
            "score_bucket_38k": row.get("score_bucket", ""),
            "shortlist_bucket": bucket,
            "candidate_matrix_status": row.get("candidate_matrix_status", ""),
            "evidence_level": row.get("evidence_level", ""),
            "inclusion_reason": inclusion_reason(row, bucket),
            "positive_drivers": row.get("top_positive_drivers", ""),
            "risk_drivers": row.get("top_risk_drivers", ""),
            "evidence_summary": evidence_summary(row),
            "research_explanation": explanation(row, bucket),
            "next_research_steps": next_steps(row),
            "recommendation_generated": False,
            "financial_advice": False,
            "broker_actions_allowed": False,
            "phase9c_authorized": False,
            "phase": PHASE,
        }
        text_to_check = " ".join(str(out.get(field, "")) for field in ["inclusion_reason", "research_explanation", "next_research_steps"])
        if has_forbidden_language(text_to_check):
            rejections.append({
                "asset_id": row.get("asset_id", ""),
                "ticker": row.get("ticker", ""),
                "company_name": row.get("company_name", ""),
                "exchange": row.get("exchange", ""),
                "reason": "forbidden_language_detected",
                "phase": PHASE,
            })
            continue
        shortlist.append(out)
        for note in split_notes(row.get("top_positive_drivers", ""), "positive driver detail limited"):
            notes.append(note_row(row, "POSITIVE_DRIVER", note, "v2.38K"))
        for note in split_notes(row.get("top_risk_drivers", ""), "risk driver detail limited"):
            notes.append(note_row(row, "RISK_DRIVER", note, "v2.38K"))
        notes.append(note_row(row, "EVIDENCE_LIMITATION", "Shortlist uses local 38J/38K evidence only; no external news or macro/geopolitical data is added in 38L.", "v2.38L"))
        notes.append(note_row(row, "NEXT_RESEARCH_STEP", next_steps(row), "v2.38L"))
        notes.append(note_row(row, "LANGUAGE_GUARDRAIL", "Research prioritization only; not a final investment action signal.", "v2.38L"))
        quality.append({
            "asset_id": row.get("asset_id", ""),
            "ticker": row.get("ticker", ""),
            "shortlist_rank": index,
            "research_rank": row.get("research_rank", ""),
            "experimental_score": row.get("experimental_score", ""),
            "shortlist_bucket": bucket,
            "candidate_matrix_status": row.get("candidate_matrix_status", ""),
            "quality_status": "SHORTLIST_ROW_READY",
            "quality_notes": "complete_scored_row_with_explanation",
            "phase": PHASE,
        })

    write_csv(output_dir / "us_explained_shortlist_v2_38l.csv", SHORTLIST_FIELDS, shortlist)
    write_csv(output_dir / "us_explained_shortlist_research_notes_v2_38l.csv", NOTE_FIELDS, notes)
    write_csv(output_dir / "us_explained_shortlist_quality_v2_38l.csv", QUALITY_FIELDS, quality)
    write_csv(output_dir / "us_explained_shortlist_rejections_v2_38l.csv", REJECTION_FIELDS, rejections)

    counts = Counter(row["shortlist_bucket"] for row in shortlist)
    report = {
        "phase": PHASE,
        "status": "COMPLETED_US_EXPLAINED_SHORTLIST_NOT_RECOMMENDATIONS",
        "input_scored_companies": len([r for r in score_rows if as_float(r.get("experimental_score")) is not None]),
        "eligible_candidates": len(candidates),
        "shortlist_size": len(shortlist),
        "high_priority": counts.get("SHORTLIST_HIGH_PRIORITY", 0),
        "medium_priority": counts.get("SHORTLIST_MEDIUM_PRIORITY", 0),
        "watchlist": counts.get("SHORTLIST_WATCHLIST", 0),
        "rejected_rows": len(rejections),
        "limit": limit,
        "min_score": min_score,
        "guardrails": {
            "network_calls": 0,
            "phase9c_authorized": False,
            "recommendation_generated": False,
            "recommendations_generated": False,
            "financial_advice": False,
            "broker_actions_allowed": False,
        },
    }
    (output_dir / "us_explained_shortlist_aggregate_report_v2_38l.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    (output_dir / "README.md").write_text("# v2.38L US explained research shortlist\n\nBuilds a deterministic explained research shortlist from v2.38K scores. It prioritizes companies for manual investigation only and does not create final investment guidance, broker actions, external news claims or phase 9C promotion.\n", encoding="utf-8", newline="\n")
    (output_dir / "US_EXPLAINED_SHORTLIST_CONTRACT_v2_38l.md").write_text("# US Explained Shortlist Contract v2.38L\n\nThis phase converts v2.38K technical scores into a traceable research shortlist. It uses only local v2.38J/v2.38K artifacts, preserves language guardrails and keeps final recommendation generation closed.\n", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9L US Explained Shortlist Gate v2.38L

Status: {report['status']}

- Input scored companies: {report['input_scored_companies']}
- Eligible candidates: {report['eligible_candidates']}
- Shortlist size: {report['shortlist_size']}
- High priority: {report['high_priority']}
- Medium priority: {report['medium_priority']}
- Watchlist: {report['watchlist']}
- Rejected rows: {report['rejected_rows']}

Guardrails: no network calls, no external claims, no final recommendation generation, no broker actions and no phase 9C authorization.
"""
    (output_dir / "PHASE9L_US_EXPLAINED_SHORTLIST_GATE_v2_38l.md").write_text(gate, encoding="utf-8", newline="\n")

    public = [
        "README.md",
        "US_EXPLAINED_SHORTLIST_CONTRACT_v2_38l.md",
        "PHASE9L_US_EXPLAINED_SHORTLIST_GATE_v2_38l.md",
        "us_explained_shortlist_v2_38l.csv",
        "us_explained_shortlist_research_notes_v2_38l.csv",
        "us_explained_shortlist_quality_v2_38l.csv",
        "us_explained_shortlist_rejections_v2_38l.csv",
        "us_explained_shortlist_aggregate_report_v2_38l.json",
    ]
    manifest = {
        "phase": PHASE,
        "outputs": {name: {"bytes": (output_dir / name).stat().st_size, "sha256": sha256(output_dir / name)} for name in public},
        "guardrails": report["guardrails"],
    }
    (output_dir / "us_explained_shortlist_manifest_v2_38l.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": report["status"],
        "input_scored_companies": report["input_scored_companies"],
        "shortlist_size": report["shortlist_size"],
        "high_priority": report["high_priority"],
        "medium_priority": report["medium_priority"],
        "watchlist": report["watchlist"],
        "recommendations_generated": False,
    }, sort_keys=True))
    return report


def note_row(row: dict[str, str], note_type: str, note: str, source_phase: str) -> dict[str, str]:
    return {
        "asset_id": row.get("asset_id", ""),
        "ticker": row.get("ticker", ""),
        "note_type": note_type,
        "note": note,
        "source_phase": source_phase,
        "phase": PHASE,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores-path", type=Path, default=SCORES)
    parser.add_argument("--score-report-path", type=Path, default=SCORE_REPORT)
    parser.add_argument("--matrix-path", type=Path, default=MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--min-score", type=float, default=None)
    args = parser.parse_args()
    build(args.scores_path, args.score_report_path, args.matrix_path, args.output_dir, args.limit, args.min_score)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
