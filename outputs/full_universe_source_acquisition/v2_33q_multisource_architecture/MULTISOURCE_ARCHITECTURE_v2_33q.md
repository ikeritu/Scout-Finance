# Scout Finance v2.33Q — arquitectura multifuente mínima (Bloque F)

Fecha: 2026-08-31. Alcance: construcción de un esquema canónico y adaptadores de normalización sobre las colecciones ya validadas (J-Quants v2.33G, TWSE v2.33I). No se ha descargado ningún precio nuevo, no se ha creado ninguna cuenta, no se ha gastado dinero.

## Por qué una arquitectura mínima y no una colección de scripts sueltos

Hasta v2.33Q, cada piloto (EODHD, J-Quants, TWSE) tenía su propio esquema de fila JSON, sus propios nombres de campo (`O`/`H`/`L`/`C` en J-Quants, `Open`/`High`/`Low`/`Close` en TWSE) y su propia forma de marcar "sin operación ese día". Cualquier validador o informe futuro tenía que conocer los tres formatos. Esto no escala a un cuarto o quinto proveedor. v2.33Q introduce una capa de normalización fina, sin reescribir el trabajo ya probado de los pilotos.

## F1 — Contrato común

`scripts/price_adapters/schema.py` define `PriceRecord`, con los 20 campos exigidos por el encargo (`asset_id`, `provider`, `provider_symbol`, `exchange`, `mic`, `country`, `currency`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume`, `is_adjusted`, `adjustment_source`, `retrieved_at`, `source_window_start`, `source_window_end`, `license_status`, `quality_status`).

Distingue explícitamente los cuatro tipos de "sin valor" que exige el encargo mediante `quality_status`:

| `quality_status` | Significado |
|---|---|
| `ok` | Observación real y validada. |
| `no_trade_this_session` | El proveedor registró el día de calendario pero no hubo operación (visto tanto en J-Quants como en TWSE). |
| `not_applicable` | El campo no aplica a esta fuente (p. ej. `adjusted_close` en una fuente que nunca ajusta). |
| `not_available_by_license` | El proveedor tiene el dato pero nuestro plan/licencia no lo permite. |

`validate_record_shape()` comprueba la forma del registro y una regla de coherencia mínima: si `is_adjusted=True`, `adjustment_source` debe nombrar una fuente real, nunca quedar vacío ni marcado como "no disponible".

## F2 — Adaptadores

Este proyecto ya tenía, por cada fuente aprobada, un script de resolución y un script de descarga fail-closed, reanudable y con escritura atómica (J-Quants: `resolve_jquants_price_pilot_v2_33g.py` + `download_jquants_price_pilot_v2_33g.py`; TWSE: `download_twse_opendata_price_pilot_v2_33i.py`). **No se han reescrito** — reescribir código ya probado en producción real solo para encajarlo en una interfaz nueva habría añadido riesgo sin beneficio real.

Lo que añade v2.33Q es la pieza que faltaba: un **normalizador** por proveedor (`scripts/price_adapters/jquants_adapter.py`, `scripts/price_adapters/twse_adapter.py`) que traduce el JSON crudo ya descargado (local, con licencia) al `PriceRecord` común, sin tocar la red ni las credenciales. Verificado contra las colecciones reales:

- J-Quants: 20.294 registros normalizados desde los 42 archivos reales de v2.33G.
- TWSE: 29.484 registros normalizados desde los 8 archivos reales de v2.33I.

Un futuro proveedor (por ejemplo, la fuente de EE. UU. del Bloque B, una vez resuelta) solo necesita su propio `<provider>_adapter.py` — el resto del pipeline (validadores, manifiesto, informes) ya sabe hablar `PriceRecord`.

## F3 — Manifiesto de cobertura

`scripts/build_coverage_manifest_v2_33q.py` genera `coverage_manifest_v2_33q.json`: por cada uno de los 50 activos con colección real local (42 JPX + 8 TWSE), fuente asignada, símbolo, rango de fechas, sesiones disponibles, ajustado/no ajustado, estado de licencia, confianza y última actualización. Reproducible: vuelve a leer los archivos locales cada vez, sin cachear cifras.

## F4 — Seguridad y licencias

Ya cumplido por el diseño existente de cada piloto, formalizado aquí como política del proyecto:

- Ningún adaptador ni descargador imprime tokens ni claves (verificado en el checklist de seguridad de cada cierre v2.33D1–v2.33I).
- J-Quants usa cabecera `x-api-key`, no query string, cuando la API lo permite.
- Los mensajes de error solo registran campos estructurados (`pilot_id`, `error_type`, `http_status`), nunca la URL completa ni la clave.
- Los datos brutos por activo permanecen fuera de Git (`.gitignore`) para cada proveedor con licencia restrictiva (J-Quants, EODHD) y, por consistencia, también para TWSE aunque su licencia sea abierta.
- Solo se versionan esquemas (`price_adapters/`), informes agregados y manifiestos — nunca precios fila a fila.
- Retención documentada por proveedor: J-Quants pendiente de confirmación escrita (v2.33N); TWSE, Open Government Data License v1.0, sin restricción conocida.

## F5 — Actualización y rollback

Política declarada para este bloque (no se ha ejecutado ninguna actualización real todavía, ya que ningún proveedor tiene aún una frecuencia operativa definida más allá del piloto puntual):

- Frecuencia por fuente: por definir cuando un proveedor pase de `CONDITIONAL` a un estado operativo continuo (fuera de alcance de este cierre).
- Todo escritor de archivo en este proyecto ya usa el patrón `<archivo>.tmp` + `Path.replace()` (verificado en los descargadores de J-Quants, TWSE, y en ambos scripts de reparación de este mismo cierre) — no se sobrescribe nunca un archivo final directamente.
- El manifiesto de cobertura de v2.33Q incluye `last_updated` por activo; una actualización futura debería comparar contra el manifiesto anterior antes de sustituirlo (no implementado en este cierre: no hay todavía una segunda ejecución real que comparar).
- Detección de deltas anómalos (activos añadidos, retirados, fallidos) queda como trabajo futuro explícito, no simulado aquí.

## QA

`tests/qa_price_adapters_schema_v2_33q.py`: valida la forma del esquema común, la regla de coherencia ajustado/fuente, y ambos adaptadores (J-Quants, TWSE) con fixtures sintéticas — sin red, sin credenciales. Verificado además contra las colecciones reales locales (50 activos, 0 problemas de forma).

## Seguridad y alcance

- No se ha descargado ningún precio nuevo en este bloque.
- No se ha creado ninguna cuenta, no se ha gastado dinero.
- `production_scoring_authorized: false`, `allow_ranking: false` en el manifiesto generado.

## Estado del roadmap

- No cambia el estado de ningún cierre anterior.
- Arquitectura mínima construida y verificada contra datos reales. Queda pendiente añadir un adaptador para EE. UU. (bloqueado en v2.33M) y para JPX/TWSE ampliados (bloqueados en v2.33N/O por el límite de 500 activos).
