# Scout Finance — Fase 8A: diseño funcional del dashboard final

Fecha: `2026-06-10T20:03:42+00:00`

## Estado de partida

```text
v0.7 congelada: True
Funnel validado: 500 → 182 → 63 → 6
Release base: v0.7.0-candidate
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
| Inicio ejecutivo | usuario normal | parcial | simplificar portada y mostrar solo estado, funnel, top ideas y alertas | alta |
| Ranking final | usuario normal | parcial | convertir ranking en tabla de decisión con motivo corto y riesgo principal | alta |
| Ficha de empresa | usuario normal | pendiente | crear ficha profunda por ticker con tesis, riesgos, métricas y datos faltantes | muy alta |
| Comparador | usuario normal | pendiente | comparar candidatas por score, riesgo, crecimiento, valoración y calidad de datos | alta |
| Funnel y auditoría | técnico | avanzado | ordenar Stage 1/2/3, watchlist, rechazos y warnings en modo auditoría | media |
| Datos y cobertura | técnico | parcial | explicar cobertura, limitaciones yfinance y faltantes críticos como dilución | alta |
| Feedback | usuario normal | parcial | hacer que el feedback sea útil para revisar y aprender en futuros runs | media |
| Exportaciones | usuario normal | parcial | centralizar CSV, informe global y futuro HTML/PDF por empresa | media |
| Configuración | técnico | parcial | mover pesos, umbrales, proveedor y costes IA a panel avanzado | media |

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
