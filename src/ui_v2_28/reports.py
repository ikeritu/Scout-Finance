"""In-memory, provenance-aware reports for Streamlit downloads."""
from __future__ import annotations
import hashlib,html,json
from datetime import datetime,timezone

def now():return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def digest_bytes(data:bytes):return hashlib.sha256(data).hexdigest()
def esc(value):return str(value or "").replace("|","\\|").replace("\n"," ")

def universe_markdown(universe,scoring):
 return f"""# Scout Finance — Informe del universo

**Generado:** {now()}  
**Estado consumidor:** CATALOG_AVAILABLE  
**Scoring:** {"AUTHORIZED PRODUCTION" if scoring.allow_ranking else "SCORING UNAVAILABLE · FAIL-CLOSED"}

## Universo operativo

- Filas: **{universe.rows:,}**
- Dataset: `{esc(universe.dataset)}`
- SHA-256: `{esc(universe.dataset_sha256)}`

No hay score, ranking, recomendación ni señal productiva disponible.

_Informe descriptivo. Sin recomendación de inversión ni acción de broker._
"""

def watchlist_markdown(data,scoring):
 rows="\n".join(f'| {esc(x.get("ticker"))} | {esc(x.get("exchange"))} | {esc(x.get("name"))} | {esc(", ".join(x.get("tags",[])))} | {esc(x.get("note"))} |' for x in data.get("items",[])) or "| — | — | Watchlist vacía | — | — |"
 return f"""# Scout Finance — Informe de watchlist

**Generado:** {now()}  
**Watchlist:** {esc(data.get("name"))}  
**Activos:** {len(data.get("items",[]))}  
**Scoring:** {"AUTHORIZED PRODUCTION" if scoring.allow_ranking else "UNAVAILABLE · NOT USED"}

| Ticker | Exchange | Nombre | Etiquetas | Nota |
|---|---|---|---|---|
{rows}

Scores, rankings, recomendaciones y señales quedan excluidos.

_Informe descriptivo. Sin recomendación de inversión ni acción de broker._
"""

def diagnostic_markdown(summary):
 components="\n".join(f'- {key.replace("_"," ").title()}: **{("N/A" if value is None else f"{value:.2f}")}**' for key,value in summary["component_means"].items())
 buckets="\n".join(f'- {key}: {value:,} ({100*value/summary["rows"]:.1f}%)' for key,value in summary["buckets"].items())
 return f"""# Scout Finance — Diagnóstico de preparación de datos

**Generado:** {now()}  
**Rol:** DATA_READINESS_ONLY  
**Filas:** {summary["rows"]:,} / 43.089  
**Scoring productivo autorizado:** No

## Medias de componentes

{components}

## Distribución diagnóstica

{buckets}

No se ordenan ni seleccionan activos. No es análisis de inversión.
"""

def markdown_to_html(markdown):
 body=[]
 for line in markdown.splitlines():
  if line.startswith("# "):body.append(f"<h1>{html.escape(line[2:])}</h1>")
  elif line.startswith("## "):body.append(f"<h2>{html.escape(line[3:])}</h2>")
  elif line.startswith("- "):body.append(f"<li>{html.escape(line[2:])}</li>")
  elif line.strip():body.append(f"<p>{html.escape(line)}</p>")
 return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><style>body{max-width:980px;margin:auto;padding:32px;font:15px system-ui;color:#18222e}h1{color:#0e7c86}p,li{line-height:1.55}</style></head><body>'+"\n".join(body)+"</body></html>"

def package_report(markdown,kind,fmt="md",sources=None):
 rendered=markdown if fmt=="md" else markdown_to_html(markdown);payload=rendered.encode("utf-8")
 manifest={"schema_version":"1.0","report_type":kind,"generated_at_utc":now(),"format":fmt,"report_sha256":digest_bytes(payload),"sources":sources or [],"investment_recommendation":False,"broker_action":False}
 return payload,json.dumps(manifest,ensure_ascii=False,indent=2).encode("utf-8")
