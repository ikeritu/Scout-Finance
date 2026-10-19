"""The chart of a coin's daily closes and volume (v2.50G). A pure function over the daily series of the data layer.

CoinGecko's free plan has no daily OHLC (only 30-minute, 4-hour and 4-day candles), so there are NO candles here: a line of daily
closes with the daily volume in its own panel. Nothing is interpolated or filled in: a missing close is a gap in the line. The day in
progress is not in the series (v2.50C drops it), so the chart only shows completed UTC days.
"""
from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .signals import finite

REFERENCE_DAYS = 30  # the window of the breakout signal
LINE_COLOUR = "#0f766e"
REFERENCE_COLOUR = "#64748b"
VOLUME_COLOUR = "rgba(37, 99, 235, 0.45)"


def reference_high(series: list[dict], days: int = REFERENCE_DAYS) -> float | None:
    """The highest close of the last `days` completed days: what the breakout signal compares the current price with."""
    closes = [c for c in (finite(p.get("price_usd")) for p in series) if c is not None]
    return max(closes[-days:]) if len(closes) >= days else None


def chart_key_text(has_volume: bool, has_reference: bool) -> str:
    parts = ["Línea verde azulada: cierre diario (UTC, días completos; el día en curso no se dibuja)"]
    if has_reference:
        parts.append(f"línea gris punteada: máximo de cierre de los últimos {REFERENCE_DAYS} días, la referencia de la señal de ruptura")
    if has_volume:
        parts.append("barras azules: volumen diario")
    return " · ".join(parts) + "."


def daily_series_figure(series: list[dict]) -> go.Figure:
    dates = [p["date"] for p in series]
    closes = [finite(p.get("price_usd")) for p in series]
    volumes = [finite(p.get("volume_usd")) for p in series]
    has_volume = any(v is not None for v in volumes)
    fig = make_subplots(rows=2 if has_volume else 1, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.74, 0.26] if has_volume else [1.0])
    fig.add_trace(go.Scatter(x=dates, y=closes, mode="lines", name="Cierre", line={"color": LINE_COLOUR, "width": 2}, connectgaps=False), row=1, col=1)
    high = reference_high(series)
    if high is not None and dates:
        fig.add_trace(go.Scatter(x=[dates[0], dates[-1]], y=[high, high], mode="lines", name=f"Máximo de cierre de {REFERENCE_DAYS} días",
                                 line={"color": REFERENCE_COLOUR, "width": 1.5, "dash": "dot"}, hoverinfo="skip"), row=1, col=1)
    fig.update_yaxes(title_text="Precio (USD)", row=1, col=1)
    if has_volume:
        fig.add_trace(go.Bar(x=dates, y=volumes, name="Volumen", marker_color=VOLUME_COLOUR), row=2, col=1)
        fig.update_yaxes(title_text="Volumen (USD)", showgrid=False, tickformat="~s", row=2, col=1)
    fig.update_layout(height=470 if has_volume else 400, margin={"l": 8, "r": 8, "t": 36, "b": 8}, showlegend=False, xaxis_rangeslider_visible=False)
    return fig
