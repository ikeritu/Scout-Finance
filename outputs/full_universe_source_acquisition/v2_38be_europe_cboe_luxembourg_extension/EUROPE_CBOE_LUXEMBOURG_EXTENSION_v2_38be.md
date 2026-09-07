# v2.38BE — Ampliación de Luxemburgo: 10 empresas reales más, y un hallazgo real sobre fondos de inversión

Fecha: 2026-09-07. Alcance: primer paso de la decisión "decide qué hacer con las 3.766 empresas nuevas" — extender Luxemburgo (ya la mejor fuente de datos financieros abiertos encontrada en Europa continental, `v2.38AW`/`v2.38AX`) con las empresas nuevas que reveló la resolución completa de Cboe Europe (`v2.38BC`) bajo `country=LU`.

## Por qué Luxemburgo primero

De las 3.766 empresas nuevas repartidas en 54 países, Luxemburgo es el único con infraestructura 100% ya construida y probada de principio a fin (identidad RCS vía GLEIF + fundamentales reales vía la Centrale des Bilans) — cero decisiones de política nuevas, coste mínimo, resultado inmediato.

## Depuración real antes de atacar: 25 → 17 candidatas genuinamente nuevas

De las 25 filas que `v2.38BC` resolvió bajo Luxemburgo, **8 no eran realmente nuevas**:
- **5 duplicados reales** de empresas ya identificadas en `v2.38AW` bajo otro ticker/listado de Cboe: ArcelorMittal, CPI Property Group, H2APEX Group SCA, Marley Spoon Group SE, Logwin AG.
- **3 productos indexados** que el filtro de ETFs original no reconoció por no llevar ningún nombre de marca conocido: "YIS MSCI North America Selection", "YIS MSCI World Selection", "YIS MSCI World Universal".

Quedan **17 candidatas genuinamente nuevas**.

## Resolución de identidad: 17/17, con un hallazgo real inesperado

Las 17 resolvieron con GLEIF (mismo método de `v2.38AW`, sin cambios). Pero el número de registro devuelto reveló algo real: **6 de las 17 no son empresas operativas, son compartimentos de fondos de inversión luxemburgueses** — su identificador tiene el formato `O` + dígitos + guion bajo + número de subfondo (p. ej. `O00007020_00000026`), estructuralmente distinto del número RCS real de una empresa (`B` + dígitos). Los nombres genéricos que ya habían levantado sospecha ("Energy", "Renewable Energy", "Total", "DGA", "TEQ - General Artificial Intelligence", "Barclays Quantic Global E NR") eran exactamente la pista: los subfondos de inversión se nombran por su mandato temático, no por una razón social real. Excluidos correctamente de la extracción de fundamentales — pedir datos de la Centrale des Bilans para un fondo sería un error de categoría, no un hueco de datos.

**11 empresas reales confirmadas** (número RCS real): Allegro.eu (B214830), Aperam (B155908), Brederode (B174490), Eurofins Scientific SE (B167775), SES (B81267), Sword Group SE (B168244), Zabka Group (B263068), DNXCORP SE (B182439), Fotex Holding (B146938), Luxempart (B27846), CPI FIM SA (B44996).

## Fundamentales reales: 10/11 encontradas

Reutilizando la caché de ficheros trimestrales ya descargada (ningún fichero nuevo de cientos de MB, solo se reescaneó lo ya local):

| Empresa | Ejercicio | Activo total | Patrimonio neto | Resultado del ejercicio |
|---|---|---:|---:|---:|
| SES | 2024-12-31 | 12.022M€ | 3.069M€ | -210M€ |
| Eurofins Scientific S.E. | 2025-12-31 | 10.446M€ | 4.229M€ | 694M€ |
| Allegro.eu | 2024-12-31 | 8.748M€ | 8.578M€ | -136M€ |
| CPI FIM SA | 2024-12-31 | 5.408M€ | 981M€ | 27M€ |
| APERAM | 2024-12-31 | 5.441M€ | 4.447M€ | -692M€ |
| Zabka Group | 2024-12-31 | 1.911M€ | 1.824M€ | -21M€ |
| Luxempart | 2025-12-31 | 1.238M€ | 1.230M€ | 67M€ |
| Brederode S.A. | 2025-12-31 | 901M€ | 900M€ | 36M€ |
| Sword Group SE | 2025-12-31 | 293M€ | 200M€ | -1,2M€ |
| DNXCORP SE | 2025-12-31 | 14M€ | 5,6M€ | 4,7M€ |

**Fotex Holding no encontrada** en los 8 trimestres escaneados (2 años) — misma limitación honesta ya documentada para ArcelorMittal/Spotify en `v2.38AX`: probablemente deposita por una vía distinta al régimen estándar.

## Reutilización de infraestructura, sin lógica nueva

`scripts/build_europe_cboe_luxembourg_extension_v2_38be.py` no reimplementa nada — importa y llama directamente a `resolve_europe_luxembourg_rcs_gleif_v2_38aw.build()` y `fetch_europe_luxembourg_fundamentals_v2_38ax.build()`, exactamente igual que se probaron en las 20 empresas originales. La única lógica nueva es la selección de candidatas (deduplicar contra lo ya conocido, excluir productos indexados) y la separación real empresa/fondo por formato de identificador.

## Resultado combinado de Luxemburgo hasta hoy

**20 (original) + 10 (esta ampliación) = 30 empresas luxemburguesas con fundamentales reales**, de 20+17=37 identificadas con RCS real de empresa (excluyendo fondos), sobre un universo de 20+25=45 activos de Cboe/Xetra resueltos en Luxemburgo en total.

## Pruebas offline

`tests/qa_europe_cboe_luxembourg_extension_v2_38be.py` — 6 casos: exclusión de duplicados ya conocidos, exclusión de productos indexados, exclusión de filas ambiguas o de otros países, selección correcta de una empresa genuinamente nueva, separación real empresa/fondo por formato de identificador, y modo sin ejecución sin red.

```
.venv/Scripts/python.exe tests/qa_europe_cboe_luxembourg_extension_v2_38be.py
PASS: v2.38BE-europe-cboe-luxembourg-extension/dedup/index-fund-filter/scope-filter/new-selected/fund-compartment-split/dry-run/no-network
```

## Seguridad y alcance

Sin credenciales nuevas. Red real usada solo para 17 consultas a GLEIF; la extracción de fundamentales reutilizó la caché ya local, sin ninguna descarga nueva. Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_CBOE_LUXEMBOURG_EXTENSION`.** Primer paso ejecutado de la decisión de priorización sobre las 3.766 empresas nuevas — reutilización completa de infraestructura ya probada, cero decisiones de política nuevas, resultado real inmediato. Siguientes pasos de la misma decisión: Austria (40 candidatas) y Finlandia (133 candidatas), mismo patrón.
