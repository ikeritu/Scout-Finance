"""License-safe local reports for phase 8."""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone

DISCLAIMER = "Scout Finance es una herramienta experimental de investigación. No constituye recomendación de comprar, vender o mantener ningún activo. Este informe no constituye asesoramiento financiero ni predicción de rentabilidad. El scoring no dispone actualmente de evidencia histórica suficiente para considerarse predictivo."


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def asset_markdown(asset: dict, as_of: str) -> str:
    pillars = "\n".join(f"- {key.title()}: {value:.2f}" for key, value in sorted((asset.get("pillar_scores") or {}).items())) or "- No disponibles en modo agregado"
    return f"""# Scout Finance — Ficha de investigación

**Generado:** {now()}

**Fecha de corte:** {as_of}

**Activo:** {asset['company_name']} ({asset['ticker']})

**Mercado:** {asset['market']}

**Estado:** {asset['eligibility_status']}

**Confianza:** {asset['confidence']}

**Score experimental:** {asset.get('total_score') if asset.get('total_score') is not None else 'No disponible'}
**Validación histórica:** INSUFFICIENT_EVIDENCE

## Pilares

{pillars}

## Limitaciones

- El resultado prioriza investigación; no predice rentabilidad.
- JPX no dispone de profundidad suficiente para validación OOS.
- TWSE tiene comparabilidad parcial, precios no ajustados y temporalidad fundamental incompleta.

_{DISCLAIMER}_
"""


def ranking_markdown(assets: list[dict], as_of: str) -> str:
    ranked = sorted((a for a in assets if a.get("rank")), key=lambda a: a["rank"])
    rows = "\n".join(f"| {a['rank']} | {a['ticker']} | {a['company_name']} | {a['total_score']:.2f} | {a['confidence']} |" for a in ranked) or "| — | — | No disponible | — | — |"
    return f"""# Scout Finance — Ranking experimental de investigación

**Generado:** {now()}

**Fecha de corte:** {as_of}

**Decisión de fase 7:** INSUFFICIENT_EVIDENCE

| Posición | Ticker | Empresa | Score | Confianza |
|---:|---|---|---:|---|
{rows}

TWSE, P020 y P178 no forman parte del ranking principal.

_{DISCLAIMER}_
"""


def watchlist_markdown(data: dict, as_of: str) -> str:
    rows = "\n".join(f"| {x['ticker']} | {x['company_name']} | {x['market']} | {x['research_status']} | {str(x.get('note','')).replace('|','/')} |" for x in data["items"]) or "| — | Watchlist vacía | — | — | — |"
    return f"""# Scout Finance — Watchlist privada

**Generado:** {now()}

**Fecha de corte:** {as_of}

**Lista:** {data['name']}

| Ticker | Empresa | Mercado | Estado de investigación | Nota |
|---|---|---|---|---|
{rows}

_{DISCLAIMER}_
"""


def to_html(markdown: str) -> bytes:
    body = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    document = '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><style>body{max-width:980px;margin:auto;padding:32px;font:15px system-ui;color:#17212b}h1{color:#0b6670}p,li{line-height:1.55}</style></head><body>' + "\n".join(body) + "</body></html>"
    return document.encode("utf-8")


def manifest(kind: str, as_of: str) -> bytes:
    return json.dumps({"schema_version": "1.0", "report_type": kind, "generated_at_utc": now(), "as_of_date": as_of, "phase7_decision": "INSUFFICIENT_EVIDENCE", "historically_validated_scoring": False, "investment_advice": False, "broker_action": False}, ensure_ascii=False, indent=2).encode("utf-8")
