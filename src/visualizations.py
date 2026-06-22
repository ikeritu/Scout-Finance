"""
Scout Finance — Visualizations from structured analysis JSON.

Phase 2C visual polish:
- Spanish labels for Bull/Base/Bear.
- Cleaner scorecard with explicit warning that risk is inverse.
- Better handling of missing scores.
- Executive HTML card with confidence/evidence warnings.
- Key limitations section.
- Clean, light and reusable visual style.

The visualizations are intentionally simple:
- no Streamlit dependency;
- matplotlib only for PNG charts;
- HTML generated with plain CSS;
- values come from validated JSON, not free text.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


SCORE_LABELS = {
    "business_quality_score": "Calidad negocio",
    "financial_health_score": "Salud financiera",
    "growth_score": "Crecimiento",
    "valuation_score": "Valoración",
    "moat_score": "Moat",
    "evidence_quality_score": "Calidad evidencia",
    "data_freshness_score": "Actualidad datos",
    "confidence_score": "Confianza",
}

RISK_SCORE_LABEL = "Riesgo"

SCENARIO_LABELS = {
    "bull_case": "Alcista",
    "base_case": "Base",
    "bear_case": "Bajista",
}


def _as_float_or_none(value: Any) -> float | None:
    """
    Convert value to float or None.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_label(value: Any, is_risk: bool = False) -> str:
    """
    Convert 0-10 score into Spanish label.
    """

    score = _as_float_or_none(value)

    if score is None:
        return "Sin datos"

    if is_risk:
        if score <= 3:
            return "Riesgo bajo"
        if score <= 6:
            return "Riesgo medio"
        return "Riesgo alto"

    if score >= 8:
        return "Muy fuerte"
    if score >= 6.5:
        return "Bueno"
    if score >= 5:
        return "Aceptable"
    if score >= 3:
        return "Débil"
    return "Muy débil"


def _score_color(value: Any, is_risk: bool = False) -> str:
    """
    Return color for HTML elements.
    """

    score = _as_float_or_none(value)

    if score is None:
        return "#94a3b8"

    if is_risk:
        if score <= 3:
            return "#16a34a"
        if score <= 6:
            return "#f97316"
        return "#dc2626"

    if score >= 8:
        return "#16a34a"
    if score >= 6.5:
        return "#2563eb"
    if score >= 5:
        return "#f97316"
    return "#dc2626"


def _format_score(value: Any) -> str:
    """
    Format 0-10 score.
    """

    score = _as_float_or_none(value)

    if score is None:
        return "Sin datos"

    return f"{score:.1f}/10"


def _available_positive_scores(data: dict[str, Any]) -> list[tuple[str, float, str]]:
    """
    Extract available positive-direction scores as label/value/color.

    Risk is excluded because its scale is inverted:
    0 = low risk, 10 = high risk.
    """

    scores = data.get("scores", {})

    if not isinstance(scores, dict):
        return []

    items: list[tuple[str, float, str]] = []

    for key, label in SCORE_LABELS.items():
        score = _as_float_or_none(scores.get(key))

        if score is None:
            continue

        items.append((label, score, _score_color(score)))

    return items


def _risk_score(data: dict[str, Any]) -> float | None:
    """
    Get risk score as float or None.
    """

    scores = data.get("scores", {})

    if not isinstance(scores, dict):
        return None

    return _as_float_or_none(scores.get("risk_score"))


def _wrap_title(title: str) -> str:
    """
    Small helper for chart titles.
    """

    return title.strip()


def save_scorecard_png(data: dict[str, Any], output_path: str | Path) -> Path:
    """
    Save a polished scorecard PNG.

    Design note:
    - Positive scores are shown together.
    - Risk is shown separately with a clear note that lower is better.
    """

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    items = _available_positive_scores(data)
    risk = _risk_score(data)

    if not items and risk is None:
        fig, ax = plt.subplots(figsize=(9, 3.8))
        ax.text(
            0.5,
            0.55,
            "Sin scores disponibles",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )
        ax.text(
            0.5,
            0.42,
            "El análisis no contiene puntuaciones estructuradas.",
            ha="center",
            va="center",
            fontsize=11,
        )
        ax.axis("off")
        fig.savefig(output, bbox_inches="tight", dpi=170)
        plt.close(fig)
        return output

    total_rows = len(items) + (1 if risk is not None else 0)
    fig_height = max(4.8, total_rows * 0.62 + 1.4)

    fig, ax = plt.subplots(figsize=(10.5, fig_height))

    labels = [item[0] for item in items]
    values = [item[1] for item in items]
    colors = [item[2] for item in items]

    y_positions = list(range(len(items)))

    if items:
        ax.barh(y_positions, values, color=colors, height=0.62)

        for index, value in enumerate(values):
            ax.text(
                value + 0.12,
                index,
                f"{value:.1f}",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="#0f172a",
            )

    # Add risk as a separate visual row.
    if risk is not None:
        risk_y = len(items) + 0.7
        risk_color = _score_color(risk, is_risk=True)
        ax.barh([risk_y], [risk], color=risk_color, height=0.62)
        ax.text(
            risk + 0.12,
            risk_y,
            f"{risk:.1f} · {_score_label(risk, is_risk=True)}",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#0f172a",
        )
        labels.append("Riesgo\n(más bajo es mejor)")
        y_positions.append(risk_y)

    ax.set_xlim(0, 10)
    ax.set_xlabel("Score 0-10", fontsize=10)
    ax.set_title(
        _wrap_title("Scout Finance — Scorecard de análisis"),
        fontsize=15,
        fontweight="bold",
        pad=14,
    )
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=10)
    ax.invert_yaxis()

    ax.grid(axis="x", linestyle="--", linewidth=0.6, alpha=0.35)
    ax.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    fig.text(
        0.01,
        0.01,
        "Nota: el score de riesgo usa escala inversa al resto: 0 = riesgo bajo, 10 = riesgo alto.",
        fontsize=8.5,
        color="#64748b",
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(output, bbox_inches="tight", dpi=170)
    plt.close(fig)

    return output


def save_scenarios_png(data: dict[str, Any], output_path: str | Path) -> Path:
    """
    Save Bull/Base/Bear probability chart as PNG.
    """

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    scenarios = data.get("scenarios", {})

    keys = ["bull_case", "base_case", "bear_case"]
    labels = [SCENARIO_LABELS[key] for key in keys]
    values: list[float | None] = []

    for key in keys:
        scenario = scenarios.get(key, {}) if isinstance(scenarios, dict) else {}
        probability = scenario.get("probability") if isinstance(scenario, dict) else None
        values.append(_as_float_or_none(probability))

    if all(value is None for value in values):
        fig, ax = plt.subplots(figsize=(8, 4.2))
        ax.text(
            0.5,
            0.58,
            "Probabilidades no estimadas",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )
        ax.text(
            0.5,
            0.44,
            "El análisis incluye escenarios, pero no asigna probabilidades por falta de datos suficientes.",
            ha="center",
            va="center",
            fontsize=10,
            color="#64748b",
        )
        ax.axis("off")
        fig.savefig(output, bbox_inches="tight", dpi=170)
        plt.close(fig)
        return output

    numeric_values = [0 if value is None else value for value in values]
    colors = ["#16a34a", "#2563eb", "#dc2626"]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(labels, numeric_values, color=colors, width=0.55)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Probabilidad estimada (%)", fontsize=10)
    ax.set_title("Escenarios alcista / base / bajista", fontsize=15, fontweight="bold", pad=12)

    for index, value in enumerate(values):
        if value is None:
            label = "Sin dato"
            y = 3
        else:
            label = f"{value:.0f}%"
            y = value + 2

        ax.text(index, y, label, ha="center", fontsize=10, fontweight="bold")

    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
    ax.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    fig.text(
        0.01,
        0.01,
        "Escenarios estimados para investigación. No representan recomendación de inversión.",
        fontsize=8.5,
        color="#64748b",
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(output, bbox_inches="tight", dpi=170)
    plt.close(fig)

    return output


def _html_list(values: Any, limit: int = 6) -> str:
    """
    Convert list values to HTML list.
    """

    if not isinstance(values, list) or not values:
        return "<p class='muted'>Sin datos disponibles.</p>"

    items = "".join(f"<li>{html.escape(str(value))}</li>" for value in values[:limit])
    return f"<ul>{items}</ul>"


def _category_style(category: str) -> tuple[str, str, str]:
    """
    Return background, text and border for category.
    """

    if "Alta calidad" in category:
        return "#ecfdf5", "#166534", "#bbf7d0"
    if "Interesante pero cara" in category:
        return "#eff6ff", "#1d4ed8", "#bfdbfe"
    if "margen de seguridad" in category:
        return "#fffbeb", "#92400e", "#fde68a"
    if "Riesgo elevado" in category:
        return "#fff7ed", "#9a3412", "#fed7aa"
    if "Descartar" in category:
        return "#fef2f2", "#991b1b", "#fecaca"
    if "Datos insuficientes" in category:
        return "#f8fafc", "#334155", "#cbd5e1"

    return "#f8fafc", "#334155", "#cbd5e1"


def _warning_box(scores: dict[str, Any], sources: dict[str, Any]) -> str:
    """
    Build warning box HTML for low confidence/evidence/data limitations.
    """

    warnings: list[str] = []

    confidence = _as_float_or_none(scores.get("confidence_score"))
    evidence = _as_float_or_none(scores.get("evidence_quality_score"))
    freshness = _as_float_or_none(scores.get("data_freshness_score"))

    if confidence is not None and confidence < 5:
        warnings.append("Confianza limitada: el análisis requiere más datos antes de usarlo como base de decisión.")

    if evidence is not None and evidence < 5:
        warnings.append("Calidad de evidencia baja o incompleta: varias conclusiones son preliminares.")

    if freshness is not None and freshness < 5:
        warnings.append("Actualidad de datos limitada: conviene verificar datos más recientes.")

    data_limitations = sources.get("data_limitations", []) if isinstance(sources, dict) else []
    if isinstance(data_limitations, list) and data_limitations:
        warnings.append("Existen limitaciones de datos relevantes indicadas por el análisis.")

    if not warnings:
        return ""

    items = "".join(f"<li>{html.escape(warning)}</li>" for warning in warnings)

    return f"""
    <div class="warning-box">
        <div class="warning-title">⚠️ Lectura prudente</div>
        <ul>{items}</ul>
    </div>
    """


def save_executive_card_html(data: dict[str, Any], output_path: str | Path) -> Path:
    """
    Save polished executive card as standalone HTML.
    """

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    scores = data.get("scores", {})
    final_result = data.get("final_result", {})
    scenarios = data.get("scenarios", {})
    risk_analysis = data.get("risk_analysis", {})
    sources = data.get("sources", {})

    if not isinstance(scores, dict):
        scores = {}
    if not isinstance(final_result, dict):
        final_result = {}
    if not isinstance(scenarios, dict):
        scenarios = {}
    if not isinstance(risk_analysis, dict):
        risk_analysis = {}
    if not isinstance(sources, dict):
        sources = {}

    ticker = html.escape(str(data.get("ticker", "")))
    company_name = html.escape(str(data.get("company_name", "")))
    analysis_date = html.escape(str(data.get("analysis_date", "")))
    final_category_raw = str(final_result.get("final_category", ""))
    final_category = html.escape(final_category_raw)
    confidence_level = html.escape(str(final_result.get("confidence_level", "")))
    final_reasoning = html.escape(str(final_result.get("final_reasoning", "")))

    confidence_score = scores.get("confidence_score")
    score_color = _score_color(confidence_score)
    badge_bg, badge_text, badge_border = _category_style(final_category_raw)

    score_cards = ""

    # Keep risk in this card, but its label makes the inverse scale clear.
    card_fields = {
        **SCORE_LABELS,
        "risk_score": "Riesgo",
    }

    for key, label in card_fields.items():
        value = scores.get(key)
        is_risk = key == "risk_score"
        color = _score_color(value, is_risk=is_risk)
        subtitle = _score_label(value, is_risk=is_risk)

        if is_risk:
            subtitle = f"{subtitle} · más bajo es mejor"

        score_cards += f"""
        <div class="score-card">
            <div class="score-title">{html.escape(label)}</div>
            <div class="score-value" style="color:{color};">{html.escape(_format_score(value))}</div>
            <div class="score-label" style="color:{color};">{html.escape(subtitle)}</div>
        </div>
        """

    main_risks = risk_analysis.get("main_risks", [])
    risk_names = []

    if isinstance(main_risks, list):
        for risk in main_risks[:3]:
            if isinstance(risk, dict):
                risk_names.append(risk.get("risk", ""))

    scenario_html = ""

    for scenario_key, title in [
        ("bull_case", "Escenario alcista"),
        ("base_case", "Escenario base"),
        ("bear_case", "Escenario bajista"),
    ]:
        scenario = scenarios.get(scenario_key, {}) if isinstance(scenarios, dict) else {}
        summary = html.escape(str(scenario.get("summary", ""))) if isinstance(scenario, dict) else ""
        probability = scenario.get("probability") if isinstance(scenario, dict) else None
        probability_text = "Sin dato" if probability is None else f"{probability}%"

        scenario_html += f"""
        <div class="scenario">
            <div class="scenario-title">{title}</div>
            <div class="scenario-prob">{html.escape(str(probability_text))}</div>
            <p>{summary}</p>
        </div>
        """

    limitations = sources.get("data_limitations", [])
    source_warnings = sources.get("source_warnings", [])

    html_content = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Scout Finance — {ticker}</title>
<style>
body {{
    font-family: Inter, Arial, sans-serif;
    background: #f8fafc;
    color: #0f172a;
    margin: 0;
    padding: 32px;
}}
.card {{
    max-width: 1120px;
    margin: 0 auto;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 24px;
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
    padding: 32px;
}}
.header {{
    display: flex;
    justify-content: space-between;
    gap: 24px;
    align-items: flex-start;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 22px;
}}
h1 {{
    margin: 0;
    font-size: 32px;
}}
h2 {{
    margin-top: 28px;
}}
.muted {{
    color: #64748b;
}}
.badge {{
    display: inline-block;
    border-radius: 999px;
    padding: 10px 14px;
    background: {badge_bg};
    color: {badge_text};
    border: 1px solid {badge_border};
    font-weight: 700;
}}
.main-score {{
    font-size: 56px;
    font-weight: 800;
    color: {score_color};
    line-height: 1;
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 22px;
}}
.score-card, .scenario, .section {{
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 18px;
    background: #ffffff;
}}
.score-title {{
    color: #334155;
    font-weight: 700;
    margin-bottom: 10px;
}}
.score-value {{
    font-size: 30px;
    font-weight: 800;
}}
.score-label {{
    font-weight: 700;
    margin-top: 8px;
}}
.scenario-title {{
    font-weight: 800;
    margin-bottom: 6px;
}}
.scenario-prob {{
    color: #2563eb;
    font-weight: 800;
    font-size: 24px;
}}
.warning-box {{
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 18px;
    padding: 18px;
    margin-top: 22px;
    color: #78350f;
}}
.warning-title {{
    font-weight: 800;
    margin-bottom: 8px;
}}
ul {{
    margin-top: 8px;
}}
.footer {{
    margin-top: 24px;
    font-size: 13px;
    color: #64748b;
}}
@media (max-width: 850px) {{
    .header {{
        flex-direction: column;
    }}
    .grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>
</head>
<body>
<div class="card">
    <div class="header">
        <div>
            <h1>{ticker} — {company_name}</h1>
            <p class="muted">{analysis_date}</p>
            <span class="badge">{final_category}</span>
            <p class="muted">Categoría interna de seguimiento. No es recomendación de inversión.</p>
        </div>
        <div>
            <div class="muted">Confianza del análisis</div>
            <div class="main-score">{html.escape(_format_score(confidence_score))}</div>
            <div class="muted">{confidence_level}</div>
        </div>
    </div>

    {_warning_box(scores, sources)}

    <h2>Scores principales</h2>
    <div class="grid">
        {score_cards}
    </div>

    <h2>Escenarios</h2>
    <div class="grid">
        {scenario_html}
    </div>

    <h2>Riesgos principales</h2>
    <div class="section">
        {_html_list(risk_names, limit=3)}
    </div>

    <h2>Limitaciones clave</h2>
    <div class="section">
        {_html_list(limitations, limit=6)}
    </div>

    <h2>Advertencias de fuentes</h2>
    <div class="section">
        {_html_list(source_warnings, limit=6)}
    </div>

    <h2>Conclusión prudente</h2>
    <div class="section">
        <p>{final_reasoning}</p>
    </div>

    <div class="footer">
        Scout Finance no emite recomendaciones de compra/venta. Esta ficha ayuda a priorizar investigación.
    </div>
</div>
</body>
</html>
"""

    output.write_text(html_content, encoding="utf-8")

    return output
