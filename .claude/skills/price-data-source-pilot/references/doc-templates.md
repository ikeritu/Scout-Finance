# Closure document templates

Two files per pilot, inside `outputs/full_universe_source_acquisition/v2_XX_<short_name>/`: a short `README.md` index and a longer `PRICE_PILOT_STATUS_v2_XX.md` (or `<TOPIC>_EVALUATION_v2_XX.md` for a desk-research-only pilot with nothing to download).

## README.md — index, keep it under ~20 lines

```markdown
# v2.XX — <one-line description of the pilot>

Estado: **<decision status>**.

## Resultado

- <bulleted, numeric findings — the headline facts a reader needs before opening the full doc>
- <license/limitation caveat if relevant>

## Archivos

- `scripts/...`: <what it does>
- `tests/qa_....py`: <what it covers>
- `<REPORT>.json` / `<REPORT>.md`: informe agregado (sin precios fila a fila).
- `PRICE_PILOT_STATUS_v2_XX.md`: decisión del gate, evidencia e incidentes técnicos.
```

## PRICE_PILOT_STATUS_v2_XX.md — the full closure doc

Section order that's worked well across every pilot this project has run:

1. **Title + status line** — the decision status up front, in bold, so a reader never has to hunt for it.
2. **Por qué se hizo** — one paragraph: what earlier finding motivated checking this source.
3. **Trabajo realizado** — numbered list of concrete steps actually taken (probe, resolve, download, validate, QA) with real counts, not descriptions of intent.
4. **Cifras confirmadas** — the numbers, reproduced locally, with a note if any earlier-cited figure needs correcting (say so plainly rather than quietly using the corrected number).
5. **Evaluación frente al contrato existente** — a table against this project's live gate criteria (check the current source-design doc for the actual thresholds before citing ≥90%/≥90%/0/documented-license, since those are project-specific and may have moved).
6. **Clasificación de la evidencia** — three subsections, always in this order and never merged:
   - **Hechos observados** — only things directly observed: a quoted error message, a measured count, a response field you actually saw. Cite how you know it.
   - **Inferencias** — reasoned conclusions built from those facts, explicitly labeled as inference, not fact.
   - **Limitaciones no confirmadas** — things you don't know, didn't check, or checked and got an ambiguous answer on. This section existing and being non-empty is a sign of a careful pilot, not an incomplete one.
7. **Decisión del gate** — restate the status, and say explicitly what it does *not* authorize (production promotion, scoring, ranking, a new phase) even if that feels repetitive — it's the line that keeps a technically-clean pilot from being read as more than it is.
8. **Seguridad y alcance** — confirm no credential/URL leaked, raw data stays local and gitignored, `production_scoring_authorized: false` / `allow_ranking: false` in every generated report.
9. **Estado del roadmap** — what this does and doesn't change about the broader project state, and the next open step (if any) — phrased as a question for the user to decide, not a plan already in motion.

## Worked example: the "corrected figure" pattern

From the EODHD pilot, this is the shape to reuse whenever a validator surfaces that an earlier-stated number was subtly wrong (e.g. a provider's non-data row got counted as data):

```markdown
> Corrección respecto a validaciones previas: la cifra de "18.791 observaciones
> totales" corresponde a filas en bruto e incluye una fila de aviso del
> proveedor por activo (77 filas), no datos de precio. El total de
> observaciones numéricas reales es 18.714. Ambas cifras están documentadas
> y son reproducibles ejecutando el validador sobre la carpeta local.
```

State both numbers, say which one is real, and make it reproducible — don't just quietly swap the figure.

## Worked example: an evidence-classification block that caught a real mistake

From the Cboe Europe / OpenFIGI pilot — an inference that looked plausible from two examples turned out wrong once checked against more:

```markdown
### Inferencias
- (draft, before checking more examples) El código de mercado compuesto
  "GR" parece indicar Alemania, y "US" Estados Unidos, en los casos vistos.

### Hechos observados (tras comprobar 13 casos)
- El mismo código "GR" aparece en una empresa italiana y dos suecas; "US"
  aparece en una empresa británica. Esto descarta que el código identifique
  el país real de la empresa.
```

The lesson isn't "never infer" — it's that an inference drawn from a handful of convenient examples needs to be checked against a wider sample before it gets promoted into the "hechos observados" section, and the doc should show that correction happened rather than silently presenting only the final, corrected conclusion.
