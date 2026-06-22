"""
Export module.

This module exports persisted MVP results from SQLite to local files.

Current scope:
- Export top signals to CSV.
- Export all signals for a run to CSV.
- Export market snapshots for a run to CSV.
- Export data errors to CSV.
- Export a compact multi-sheet Excel report when openpyxl is available.

Not included in this phase:
- Streamlit download buttons.
- OpenAI analysis export.
- Validation export.
- Scheduled reports.
- Advanced formatting.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from config import get_paths
from src.results import (
    get_latest_run_id,
    get_run_summary,
    get_top_signals,
    load_data_errors,
    load_final_research_view,
    load_market_snapshots,
    load_signals,
    summarize_signals,
)


DEFAULT_TOP_N = 20


def _timestamp_for_filename() -> str:
    """
    Return a UTC timestamp safe for filenames.
    """

    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _get_exports_dir(mode: str = "demo") -> Path:
    """
    Resolve and create the exports directory.
    """

    if mode not in {"demo", "real"}:
        raise ValueError("Invalid mode. Expected 'demo' or 'real'.")

    paths = get_paths(mode)

    if "exports_dir" in paths:
        exports_dir = Path(paths["exports_dir"])
    else:
        exports_dir = Path("outputs") / "exports"

    exports_dir.mkdir(parents=True, exist_ok=True)

    return exports_dir


def _resolve_run_id(run_id: str | None = None, mode: str = "demo") -> str:
    """
    Resolve the run_id to export.

    If run_id is None, the latest run for the selected mode is used.
    """

    if run_id is not None:
        return run_id

    latest_run_id = get_latest_run_id(mode=mode)

    if latest_run_id is None:
        raise ValueError("No runs found. Execute python -m src.pipeline first.")

    return latest_run_id


def _safe_run_id_for_filename(run_id: str) -> str:
    """
    Shorten run_id for readable filenames.
    """

    return run_id[:8]


CATEGORY_LABELS = {
    "high_priority_research": "Alta prioridad",
    "medium_priority_research": "Media prioridad",
    "watchlist": "Watchlist",
    "low_priority": "Baja prioridad",
    "low_confidence": "Baja confianza",
    "high_risk_review": "Revisar riesgo",
    "excluded": "Excluida",
}


FEEDBACK_LABELS = {
    "interesting": "🟢 Interesante",
    "discard": "🔴 Descartar",
    "review_later": "🔵 Revisar después",
    "false_positive": "⚠️ Falso positivo",
    "needs_more_research": "🟡 Investigar más",
    "already_known": "✅ Ya conocida",
}


QUANT_REASON_LABELS = {
    "strong_relative_volume": "Volumen relativo elevado",
    "positive_momentum": "Momentum positivo",
    "negative_momentum": "Momentum negativo",
    "good_liquidity": "Buena liquidez",
    "low_liquidity": "Baja liquidez",
    "constructive_price_context": "Contexto técnico favorable",
    "weak_price_context": "Contexto técnico débil",
    "elevated_risk": "Riesgo elevado",
    "high_data_confidence": "Alta confianza en datos",
    "medium_data_confidence": "Confianza media en datos",
    "low_data_confidence": "Baja confianza en datos",
    "high_relative_volume": "Volumen relativo elevado",
    "low_relative_volume": "Volumen relativo bajo",
    "large_cap": "Gran capitalización",
    "mid_cap": "Mediana capitalización",
    "small_cap": "Pequeña capitalización",
    "no_strong_quant_signal": "Sin señal cuantitativa fuerte",
}


def _is_missing(value: Any) -> bool:
    """
    Return True if a value should be treated as missing for clean exports.
    """

    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except TypeError:
        pass

    if isinstance(value, str) and value.strip() == "":
        return True

    return False


def _format_number(value: Any, decimals: int = 2) -> str:
    """
    Format a numeric value for human-readable exports.
    """

    if _is_missing(value):
        return ""

    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _format_compact_usd(value: Any) -> str:
    """
    Format large USD values compactly for human-readable exports.
    """

    if _is_missing(value):
        return ""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    abs_number = abs(number)

    if abs_number >= 1_000_000_000_000:
        return f"${number / 1_000_000_000_000:.2f}T"

    if abs_number >= 1_000_000_000:
        return f"${number / 1_000_000_000:.2f}B"

    if abs_number >= 1_000_000:
        return f"${number / 1_000_000:.2f}M"

    return f"${number:,.2f}"


def _format_percent_ratio(value: Any) -> str:
    """
    Format a ratio as a percentage for clean exports.
    """

    if _is_missing(value):
        return ""

    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _category_label(value: Any) -> str:
    """
    Convert internal category into a user-facing export label.
    """

    if _is_missing(value):
        return ""

    value_str = str(value)
    return CATEGORY_LABELS.get(value_str, value_str)


def _feedback_label(value: Any) -> str:
    """
    Convert internal feedback labels into user-facing export labels.
    """

    if _is_missing(value):
        return ""

    value_str = str(value)
    return FEEDBACK_LABELS.get(value_str, value_str)


def _reviewed_by_label(value: Any) -> str:
    """
    Convert internal reviewer identifiers into cleaner export labels.
    """

    if _is_missing(value):
        return ""

    value_str = str(value).strip()
    reviewer_labels = {
        "system_demo": "Sistema demo",
        "system": "Sistema",
        "demo": "Sistema demo",
    }

    return reviewer_labels.get(value_str, value_str)


def _short_openai_reason(value: Any) -> str:
    """
    Shorten technical OpenAI placeholder messages for clean exports.
    """

    if _is_missing(value):
        return ""

    value_str = str(value)

    if "ENABLE_OPENAI=false" in value_str:
        return "IA desactivada"

    if len(value_str) > 120:
        return value_str[:117] + "..."

    return value_str


def _humanize_quant_reason(value: Any) -> str:
    """
    Convert internal quantitative reason codes into readable Spanish labels.
    """

    if _is_missing(value):
        return ""

    value_str = str(value).strip()
    normalized = value_str.replace(" · ", ";").replace("·", ";")
    parts = [part.strip() for part in normalized.split(";") if part.strip()]

    return " · ".join(
        QUANT_REASON_LABELS.get(part, part.replace("_", " ").capitalize())
        for part in parts
    )


def build_clean_final_research_view(final_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a human-readable final research dataframe for CSV/Excel exports.

    This function does not change the persisted database rows. It only creates
    a clean report-oriented view with labels matching the Streamlit interface.
    """

    if final_df.empty:
        return pd.DataFrame()

    ranked_df = final_df.copy().reset_index(drop=True)
    ranked_df.insert(0, "rank", ranked_df.index + 1)

    mappings = {
        "rank": "Rank",
        "ticker": "Ticker",
        "company_name": "Empresa",
        "sector": "Sector",
        "industry": "Industria",
        "score_priority": "Score",
        "category_final": "Categoría",
        "price_at_signal": "Precio",
        "market_cap": "Market Cap",
        "relative_volume": "Volumen rel.",
        "change_5d": "Cambio 5D",
        "change_20d": "Cambio 20D",
        "openai_reason_to_pass": "Análisis IA",
        "feedback_label": "Feedback",
        "feedback_notes": "Notas feedback",
        "reviewed_by": "Revisado por",
        "reason_to_pass_quant": "Razón cuantitativa",
        "summary_thesis": "Tesis IA",
        "why_it_could_work": "Por qué podría funcionar",
        "why_it_could_fail": "Por qué podría fallar",
    }

    clean_df = pd.DataFrame()

    for original, renamed in mappings.items():
        if original in ranked_df.columns:
            clean_df[renamed] = ranked_df[original]

    if "Score" in clean_df.columns:
        clean_df["Score"] = clean_df["Score"].apply(lambda value: _format_number(value, 2))

    if "Precio" in clean_df.columns:
        clean_df["Precio"] = clean_df["Precio"].apply(lambda value: _format_number(value, 2))

    if "Market Cap" in clean_df.columns:
        clean_df["Market Cap"] = clean_df["Market Cap"].apply(_format_compact_usd)

    if "Volumen rel." in clean_df.columns:
        clean_df["Volumen rel."] = clean_df["Volumen rel."].apply(lambda value: _format_number(value, 2))

    if "Cambio 5D" in clean_df.columns:
        clean_df["Cambio 5D"] = clean_df["Cambio 5D"].apply(_format_percent_ratio)

    if "Cambio 20D" in clean_df.columns:
        clean_df["Cambio 20D"] = clean_df["Cambio 20D"].apply(_format_percent_ratio)

    if "Categoría" in clean_df.columns:
        clean_df["Categoría"] = clean_df["Categoría"].apply(_category_label)

    if "Análisis IA" in clean_df.columns:
        clean_df["Análisis IA"] = clean_df["Análisis IA"].apply(_short_openai_reason)

    if "Feedback" in clean_df.columns:
        clean_df["Feedback"] = clean_df["Feedback"].apply(_feedback_label)

    if "Revisado por" in clean_df.columns:
        clean_df["Revisado por"] = clean_df["Revisado por"].apply(_reviewed_by_label)

    if "Razón cuantitativa" in clean_df.columns:
        clean_df["Razón cuantitativa"] = clean_df["Razón cuantitativa"].apply(_humanize_quant_reason)

    return clean_df.fillna("")


def export_top_signals_csv(
    run_id: str | None = None,
    mode: str = "demo",
    top_n: int = DEFAULT_TOP_N,
    min_score: float | None = None,
) -> Path:
    """
    Export top signals to CSV.

    Parameters
    ----------
    run_id:
        Optional run identifier. If None, latest run is used.
    mode:
        Either "demo" or "real".
    top_n:
        Number of top signals to export.
    min_score:
        Optional minimum priority score.

    Returns
    -------
    pathlib.Path
        Created CSV path.
    """

    resolved_run_id = _resolve_run_id(run_id=run_id, mode=mode)
    exports_dir = _get_exports_dir(mode=mode)

    top_df = get_top_signals(
        run_id=resolved_run_id,
        mode=mode,
        top_n=top_n,
        min_score=min_score,
    )

    file_path = exports_dir / (
        f"top_signals_{mode}_{_safe_run_id_for_filename(resolved_run_id)}_"
        f"{_timestamp_for_filename()}.csv"
    )

    top_df.to_csv(file_path, index=False, encoding="utf-8-sig")

    return file_path


def export_all_signals_csv(
    run_id: str | None = None,
    mode: str = "demo",
) -> Path:
    """
    Export all signals for one run to CSV.
    """

    resolved_run_id = _resolve_run_id(run_id=run_id, mode=mode)
    exports_dir = _get_exports_dir(mode=mode)

    signals_df = load_signals(run_id=resolved_run_id, mode=mode)

    file_path = exports_dir / (
        f"all_signals_{mode}_{_safe_run_id_for_filename(resolved_run_id)}_"
        f"{_timestamp_for_filename()}.csv"
    )

    signals_df.to_csv(file_path, index=False, encoding="utf-8-sig")

    return file_path


def export_market_snapshots_csv(
    run_id: str | None = None,
    mode: str = "demo",
) -> Path:
    """
    Export market snapshots for one run to CSV.
    """

    resolved_run_id = _resolve_run_id(run_id=run_id, mode=mode)
    exports_dir = _get_exports_dir(mode=mode)

    snapshots_df = load_market_snapshots(run_id=resolved_run_id, mode=mode)

    file_path = exports_dir / (
        f"market_snapshots_{mode}_{_safe_run_id_for_filename(resolved_run_id)}_"
        f"{_timestamp_for_filename()}.csv"
    )

    snapshots_df.to_csv(file_path, index=False, encoding="utf-8-sig")

    return file_path


def export_data_errors_csv(
    run_id: str | None = None,
    mode: str = "demo",
) -> Path:
    """
    Export data errors for one run to CSV.
    """

    resolved_run_id = _resolve_run_id(run_id=run_id, mode=mode)
    exports_dir = _get_exports_dir(mode=mode)

    errors_df = load_data_errors(run_id=resolved_run_id, mode=mode)

    file_path = exports_dir / (
        f"data_errors_{mode}_{_safe_run_id_for_filename(resolved_run_id)}_"
        f"{_timestamp_for_filename()}.csv"
    )

    errors_df.to_csv(file_path, index=False, encoding="utf-8-sig")

    return file_path



def export_final_research_view_csv(
    run_id: str | None = None,
    mode: str = "demo",
    top_n: int | None = None,
) -> Path:
    """
    Export a clean final research view to CSV.

    The exported file is intended for human review and includes quantitative
    ranking, OpenAI status, manual feedback and key thesis fields in one table.
    """

    resolved_run_id = _resolve_run_id(run_id=run_id, mode=mode)
    exports_dir = _get_exports_dir(mode=mode)

    final_df = load_final_research_view(run_id=resolved_run_id, mode=mode)

    if top_n is not None:
        final_df = final_df.head(top_n)

    clean_df = build_clean_final_research_view(final_df)

    file_path = exports_dir / (
        f"final_research_view_clean_{mode}_{_safe_run_id_for_filename(resolved_run_id)}_"
        f"{_timestamp_for_filename()}.csv"
    )

    clean_df.to_csv(file_path, index=False, encoding="utf-8-sig")

    return file_path


def export_run_report_excel(
    run_id: str | None = None,
    mode: str = "demo",
    top_n: int = DEFAULT_TOP_N,
) -> Path:
    """
    Export a compact Excel report for one run.

    Sheets:
    - run_summary
    - top_signals
    - all_signals
    - market_snapshots
    - data_errors

    Notes
    -----
    This function requires an Excel writer engine such as openpyxl.
    If openpyxl is not installed, install it or use the CSV export functions.
    """

    resolved_run_id = _resolve_run_id(run_id=run_id, mode=mode)
    exports_dir = _get_exports_dir(mode=mode)

    run_summary = get_run_summary(run_id=resolved_run_id, mode=mode)
    signals_df = load_signals(run_id=resolved_run_id, mode=mode)
    top_df = get_top_signals(run_id=resolved_run_id, mode=mode, top_n=top_n)
    snapshots_df = load_market_snapshots(run_id=resolved_run_id, mode=mode)
    errors_df = load_data_errors(run_id=resolved_run_id, mode=mode)
    final_view_df = load_final_research_view(run_id=resolved_run_id, mode=mode)
    clean_final_view_df = build_clean_final_research_view(final_view_df.head(top_n))
    signal_summary = summarize_signals(signals_df)

    run_summary_df = pd.DataFrame(
        [{"metric": key, "value": value} for key, value in run_summary.items()]
    )

    signal_summary_df = pd.DataFrame(
        [{"metric": key, "value": str(value)} for key, value in signal_summary.items()]
    )

    file_path = exports_dir / (
        f"run_report_{mode}_{_safe_run_id_for_filename(resolved_run_id)}_"
        f"{_timestamp_for_filename()}.xlsx"
    )

    try:
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            run_summary_df.to_excel(writer, sheet_name="run_summary", index=False)
            signal_summary_df.to_excel(writer, sheet_name="signal_summary", index=False)
            clean_final_view_df.to_excel(writer, sheet_name="final_research_view", index=False)
            top_df.to_excel(writer, sheet_name="top_signals", index=False)
            signals_df.to_excel(writer, sheet_name="all_signals", index=False)
            snapshots_df.to_excel(writer, sheet_name="market_snapshots", index=False)
            errors_df.to_excel(writer, sheet_name="data_errors", index=False)
    except ImportError as exc:
        raise ImportError(
            "Excel export requires openpyxl. Install it with: pip install openpyxl"
        ) from exc

    return file_path


def export_default_bundle(
    run_id: str | None = None,
    mode: str = "demo",
    top_n: int = DEFAULT_TOP_N,
    include_excel: bool = True,
) -> dict[str, str]:
    """
    Export a default bundle of files for one run.

    Created files:
    - top_signals CSV
    - all_signals CSV
    - final_research_view_clean CSV
    - market_snapshots CSV
    - data_errors CSV
    - optional Excel report

    Returns
    -------
    dict[str, str]
        Export names and file paths.
    """

    resolved_run_id = _resolve_run_id(run_id=run_id, mode=mode)

    exported_files: dict[str, str] = {}

    exported_files["top_signals_csv"] = str(
        export_top_signals_csv(
            run_id=resolved_run_id,
            mode=mode,
            top_n=top_n,
        )
    )
    exported_files["final_research_view_clean_csv"] = str(
        export_final_research_view_csv(
            run_id=resolved_run_id,
            mode=mode,
            top_n=top_n,
        )
    )
    exported_files["all_signals_csv"] = str(
        export_all_signals_csv(run_id=resolved_run_id, mode=mode)
    )
    exported_files["market_snapshots_csv"] = str(
        export_market_snapshots_csv(run_id=resolved_run_id, mode=mode)
    )
    exported_files["data_errors_csv"] = str(
        export_data_errors_csv(run_id=resolved_run_id, mode=mode)
    )

    if include_excel:
        exported_files["excel_report"] = str(
            export_run_report_excel(
                run_id=resolved_run_id,
                mode=mode,
                top_n=top_n,
            )
        )

    return exported_files


if __name__ == "__main__":
    mode = "demo"
    run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        raise SystemExit("No runs found. Execute python -m src.pipeline first.")

    print(f"Exporting latest run: {run_id}")

    try:
        exported = export_default_bundle(
            run_id=run_id,
            mode=mode,
            top_n=20,
            include_excel=True,
        )
    except ImportError as exc:
        print(exc)
        print("Retrying CSV-only export...")
        exported = export_default_bundle(
            run_id=run_id,
            mode=mode,
            top_n=20,
            include_excel=False,
        )

    print("\nExported files:")
    for name, path in exported.items():
        print(f"- {name}: {path}")
