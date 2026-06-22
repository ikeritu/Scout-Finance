
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase8a_dashboard_final_design_summary.json"
REPORT_PATH = OUT_DIR / "phase8a_dashboard_final_design_report.md"
MATRIX_PATH = OUT_DIR / "phase8a_dashboard_final_design_matrix.csv"

APP_PATH = ROOT / "app.py"
FILTERS_PATH = ROOT / "src" / "filters.py"
RELEASE_LOCK_PATH = ROOT / "releases" / "v0.7" / "RELEASE_LOCK_v0.7.json"
PHASE7G_SUMMARY_PATH = OUT_DIR / "phase7g_freeze_final_v07_summary.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def file_signature(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "size": None, "mtime": None}
    stat = path.stat()
    return {"exists": True, "size": stat.st_size, "mtime": stat.st_mtime}


def write_matrix(rows: list[dict]) -> None:
    headers = ["area", "final_tab", "audience", "status", "action", "priority"]
    lines = [",".join(headers)]
    for row in rows:
        values = []
        for h in headers:
            value = str(row.get(h, "")).replace('"', '""')
            values.append(f'"{value}"')
        lines.append(",".join(values))
    MATRIX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(summary: dict, rows: list[dict]) -> str:
    tab_lines = "\n".join(
        f"| {r['final_tab']} | {r['audience']} | {r['status']} | {r['action']} | {r['priority']} |"
        for r in rows
    )
    return f"""# Scout Finance — Fase 8A: diseño funcional del dashboard final

Fecha: `{summary["created_at"]}`

## Estado de partida

```text
v0.7 congelada: {summary["phase7g_frozen"]}
Funnel validado: {summary["validated_funnel"]}
Release base: {summary["base_release"]}
```

## Objetivo de v0.8

Convertir Scout Finance de una herramienta técnicamente validada en una aplicación usable para tomar decisiones de investigación.

```text
De: motor + dashboard técnico validado
A: dashboard ejecutivo + fichas explicables + flujo de decisión claro
```

## Principio de diseño

La app debe tener dos niveles:

```text
Nivel 1 — Usuario normal: qué empresas son interesantes, por qué, qué riesgo tienen y qué revisar después.
Nivel 2 — Técnico/auditoría: de dónde sale cada empresa, qué filtro pasó/falló y qué datos faltan.
```

## Estructura propuesta del dashboard v0.8

| Pestaña final | Audiencia | Estado actual | Acción propuesta | Prioridad |
|---|---|---|---|---|
{tab_lines}

## Pestañas finales propuestas

### 1. Inicio ejecutivo

Debe mostrar:

```text
- Estado del último run
- Funnel 500 → 182 → 63 → 6
- Top 5 ideas
- Alertas principales de datos
- Guía: qué revisar primero
```

### 2. Ranking final

Debe mostrar:

```text
- Ranking Stage 3
- Score
- Etiqueta: fuerte / interesante / watchlist
- Motivo corto
- Riesgo principal
- Acción recomendada
```

### 3. Ficha de empresa

Debe ser el corazón de v0.8:

```text
- Resumen ejecutivo
- Por qué aparece
- Fortalezas
- Riesgos
- Datos faltantes
- Métricas clave
- Decisión manual
```

### 4. Comparador

Debe permitir comparar candidatas:

```text
AUPH vs BZ vs ADBE vs ADEA
```

### 5. Funnel y auditoría

Debe conservar lo técnico, pero ordenado.

### 6. Datos y cobertura

Debe explicar cobertura, limitaciones de yfinance y faltantes críticos como dilución.

### 7. Feedback

Debe permitir marcar empresas como interesante, revisar después, falso positivo, descartar o ya conocida.

### 8. Exportaciones

Debe centralizar CSV, informe global y futuro HTML/PDF por empresa.

### 9. Configuración

Debe esconder pesos, umbrales, proveedor de datos y costes IA en panel avanzado.

## Decisión de producto

La v0.8 no debe meter más complejidad visual hasta resolver la ficha de empresa.

Orden recomendado:

```text
8B — Ficha profunda por empresa
8C — Comparador de candidatas
8D — Limpieza visual del dashboard
8E — Export HTML/CSV final
```

## Controles

```text
OpenAI llamado: False
API externa llamada: False
yfinance llamado: False
app.py modificado: False
filters.py modificado: False
pipeline recalculado: False
release v0.7 modificada: False
```

## Resultado

```text
Fase 8A completada: diseño funcional del dashboard final documentado.
```
"""


def main() -> int:
    print("Scout Finance — Phase 8A dashboard final design")
    print("=" * 88)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    before_app = file_signature(APP_PATH)
    before_filters = file_signature(FILTERS_PATH)

    phase7g = read_json(PHASE7G_SUMMARY_PATH)
    release_lock = read_json(RELEASE_LOCK_PATH)

    rows = [
        {"area": "executive", "final_tab": "Inicio ejecutivo", "audience": "usuario normal", "status": "parcial", "action": "simplificar portada y mostrar solo estado, funnel, top ideas y alertas", "priority": "alta"},
        {"area": "ranking", "final_tab": "Ranking final", "audience": "usuario normal", "status": "parcial", "action": "convertir ranking en tabla de decisión con motivo corto y riesgo principal", "priority": "alta"},
        {"area": "company_detail", "final_tab": "Ficha de empresa", "audience": "usuario normal", "status": "pendiente", "action": "crear ficha profunda por ticker con tesis, riesgos, métricas y datos faltantes", "priority": "muy alta"},
        {"area": "comparison", "final_tab": "Comparador", "audience": "usuario normal", "status": "pendiente", "action": "comparar candidatas por score, riesgo, crecimiento, valoración y calidad de datos", "priority": "alta"},
        {"area": "audit", "final_tab": "Funnel y auditoría", "audience": "técnico", "status": "avanzado", "action": "ordenar Stage 1/2/3, watchlist, rechazos y warnings en modo auditoría", "priority": "media"},
        {"area": "data_quality", "final_tab": "Datos y cobertura", "audience": "técnico", "status": "parcial", "action": "explicar cobertura, limitaciones yfinance y faltantes críticos como dilución", "priority": "alta"},
        {"area": "feedback", "final_tab": "Feedback", "audience": "usuario normal", "status": "parcial", "action": "hacer que el feedback sea útil para revisar y aprender en futuros runs", "priority": "media"},
        {"area": "exports", "final_tab": "Exportaciones", "audience": "usuario normal", "status": "parcial", "action": "centralizar CSV, informe global y futuro HTML/PDF por empresa", "priority": "media"},
        {"area": "settings", "final_tab": "Configuración", "audience": "técnico", "status": "parcial", "action": "mover pesos, umbrales, proveedor y costes IA a panel avanzado", "priority": "media"},
    ]

    write_matrix(rows)

    summary = {
        "phase": "8A",
        "status": "OK",
        "created_at": utc_now(),
        "goal": "dashboard_final_functional_design",
        "base_release": release_lock.get("release", "v0.7.0-candidate"),
        "phase7g_frozen": release_lock.get("status") == "FROZEN" or phase7g.get("freeze_status") == "FROZEN",
        "validated_funnel": phase7g.get("validated_funnel", "500 → 182 → 63 → 6"),
        "final_tabs_count": len(rows),
        "recommended_next_phase": "8B — Ficha profunda por empresa",
        "outputs": {"summary": str(SUMMARY_PATH), "report": str(REPORT_PATH), "matrix": str(MATRIX_PATH)},
        "controls": {
            "openai_called": False,
            "api_called": False,
            "yfinance_called": False,
            "app_modified": False,
            "filters_modified": False,
            "pipeline_recalculated": False,
            "release_modified": False,
        },
        "signatures_before": {"app.py": before_app, "src/filters.py": before_filters},
        "signatures_after": {"app.py": file_signature(APP_PATH), "src/filters.py": file_signature(FILTERS_PATH)},
    }

    REPORT_PATH.write_text(build_report(summary, rows), encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("Design")
    print("-" * 88)
    print(f"Status: {summary['status']}")
    print(f"Base release: {summary['base_release']}")
    print(f"v0.7 frozen: {summary['phase7g_frozen']}")
    print(f"Validated funnel: {summary['validated_funnel']}")
    print(f"Final tabs proposed: {summary['final_tabs_count']}")
    print(f"Next: {summary['recommended_next_phase']}")
    print()
    print("Phase 8A dashboard final design is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
