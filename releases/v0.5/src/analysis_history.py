
"""
Scout Finance — Analysis history utilities.

Phase 3B: read structured JSON outputs from outputs/analyses/ and build
comparison tables without calling OpenAI.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

OUTPUT_STEM_PATTERN = re.compile(r"^(?P<ticker>[A-Z0-9.\-]+)_(?P<date>\d{8})_(?P<time>\d{6})$")

@dataclass(frozen=True)
class AnalysisFileRecord:
    ticker: str
    output_id: str
    json_path: Path
    analysis_timestamp: datetime | None
    modified_timestamp: datetime


def _parse_output_timestamp(stem: str) -> datetime | None:
    match = OUTPUT_STEM_PATTERN.match(stem)
    if not match:
        return None
    try:
        return datetime.strptime(f"{match.group('date')}{match.group('time')}", "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _ticker_from_stem(stem: str) -> str:
    match = OUTPUT_STEM_PATTERN.match(stem)
    if match:
        return match.group('ticker')
    return stem.split('_', 1)[0].upper()


def list_analysis_json_files(output_dir: str | Path) -> list[AnalysisFileRecord]:
    folder = Path(output_dir)
    if not folder.exists():
        return []
    records: list[AnalysisFileRecord] = []
    for json_path in folder.glob('*.json'):
        stem = json_path.stem
        try:
            modified = datetime.fromtimestamp(json_path.stat().st_mtime)
        except OSError:
            modified = datetime.min
        records.append(AnalysisFileRecord(
            ticker=_ticker_from_stem(stem),
            output_id=stem,
            json_path=json_path,
            analysis_timestamp=_parse_output_timestamp(stem),
            modified_timestamp=modified,
        ))
    return sorted(records, key=lambda r: r.analysis_timestamp or r.modified_timestamp, reverse=True)


def load_analysis_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f'Analysis JSON is not an object: {path}')
    return data


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _record_to_row(record: AnalysisFileRecord, data: dict[str, Any]) -> dict[str, Any]:
    scores = data.get('scores') if isinstance(data.get('scores'), dict) else {}
    final = data.get('final_result') if isinstance(data.get('final_result'), dict) else {}
    sources = data.get('sources') if isinstance(data.get('sources'), dict) else {}
    valuation = data.get('valuation_summary') if isinstance(data.get('valuation_summary'), dict) else {}
    risk = data.get('risk_analysis') if isinstance(data.get('risk_analysis'), dict) else {}
    return {
        'ticker': data.get('ticker') or record.ticker,
        'company_name': data.get('company_name'),
        'sector': data.get('sector'),
        'industry': data.get('industry'),
        'analysis_date': data.get('analysis_date'),
        'output_id': record.output_id,
        'json_path': str(record.json_path),
        'parsed_output_datetime': (record.analysis_timestamp.isoformat() if record.analysis_timestamp else None),
        'final_category': final.get('final_category'),
        'confidence_level': final.get('confidence_level'),
        'confidence_score': scores.get('confidence_score'),
        'business_quality_score': scores.get('business_quality_score'),
        'financial_health_score': scores.get('financial_health_score'),
        'growth_score': scores.get('growth_score'),
        'valuation_score': scores.get('valuation_score'),
        'risk_score': scores.get('risk_score'),
        'moat_score': scores.get('moat_score'),
        'evidence_quality_score': scores.get('evidence_quality_score'),
        'data_freshness_score': scores.get('data_freshness_score'),
        'risk_level': risk.get('risk_level'),
        'valuation_status': valuation.get('valuation_status'),
        'source_warnings_count': len(_as_list(sources.get('source_warnings'))),
        'data_limitations_count': len(_as_list(sources.get('data_limitations'))),
        'main_sources_count': len(_as_list(sources.get('main_sources'))),
    }


def build_analysis_comparison_df(output_dir: str | Path, latest_only: bool = True) -> pd.DataFrame:
    records = list_analysis_json_files(output_dir)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        key = record.ticker.upper()
        if latest_only and key in seen:
            continue
        try:
            data = load_analysis_json(record.json_path)
            rows.append(_record_to_row(record, data))
        except Exception as exc:
            rows.append({'ticker': record.ticker, 'output_id': record.output_id, 'json_path': str(record.json_path), 'load_error': f'{exc.__class__.__name__}: {exc}'})
        seen.add(key)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    score_columns = ['confidence_score','business_quality_score','financial_health_score','growth_score','valuation_score','risk_score','moat_score','evidence_quality_score','data_freshness_score']
    for col in score_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    sort_cols = [c for c in ['confidence_score','business_quality_score','moat_score'] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=[False] * len(sort_cols))
    return df.reset_index(drop=True)


def build_display_comparison_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    cols = ['ticker','company_name','final_category','confidence_level','confidence_score','business_quality_score','moat_score','evidence_quality_score','data_freshness_score','risk_score','valuation_score','source_warnings_count','data_limitations_count','output_id']
    available = [c for c in cols if c in df.columns]
    display = df[available].copy()
    return display.rename(columns={
        'ticker':'Ticker','company_name':'Empresa','final_category':'Categoría','confidence_level':'Confianza','confidence_score':'Score confianza','business_quality_score':'Calidad negocio','moat_score':'Moat','evidence_quality_score':'Evidencia','data_freshness_score':'Actualidad datos','risk_score':'Riesgo','valuation_score':'Valoración','source_warnings_count':'Avisos fuentes','data_limitations_count':'Limitaciones','output_id':'Output'
    })


def summarize_analysis_history(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {'companies':0, 'avg_confidence':None, 'avg_risk':None, 'high_quality_count':0, 'insufficient_data_count':0}
    cats = df['final_category'].fillna('').astype(str) if 'final_category' in df.columns else pd.Series([], dtype=str)
    return {
        'companies': int(len(df)),
        'avg_confidence': float(df['confidence_score'].mean()) if 'confidence_score' in df.columns else None,
        'avg_risk': float(df['risk_score'].mean()) if 'risk_score' in df.columns else None,
        'high_quality_count': int(cats.str.contains('Alta calidad', regex=False).sum()) if not cats.empty else 0,
        'insufficient_data_count': int(cats.str.contains('Datos insuficientes', regex=False).sum()) if not cats.empty else 0,
    }


def export_comparison_csv_bytes(df: pd.DataFrame) -> bytes:
    if df is None:
        df = pd.DataFrame()
    return df.to_csv(index=False).encode('utf-8-sig')
