# Scout Finance v2.38A — auditoría canónica del universo global

Fecha de cierre: 2026-09-01. Alcance: censo, calidad, elegibilidad y rutas de datos; ejecución completamente offline. No incluye adquisición masiva, fundamentales nuevos, scoring, ranking ni recomendaciones.

## Dataset canónico resuelto

La fuente canónica de esta fase es `eligibility_census_v2_33b2.csv.xz`: contiene las 43.089 filas del universo operativo y la política de elegibilidad refinada vigente. Su SHA-256 es `dd7a5d2f98d2e750d08cb8633d772caecf044e6c41db7f27464b58bf10bb1876`.

La referencia v2.21H también contiene 43.089 identidades, pero no la elegibilidad refinada. La base v2.24F aporta MIC, sector, industria y capitalización cuando existen; se unió por posición únicamente después de verificar 43.089/43.089 coincidencias exactas en ticker, nombre y bolsa. Ninguna fuente fue modificada.

## Censo conservado

| Estado | Filas | Interpretación |
|---|---:|---|
| Elegible | 21.165 | Acción común o ADR que superó el preflight v2.33B2 |
| Excluida | 10.432 | Producto cotizado, placeholder, preferente u otra exclusión explícita |
| Revisión | 9.710 | Tipo no resuelto, fondo/trust, SPAC u otro caso no automático |
| Bloqueada | 1.782 | Xetra 1.424 + SGX 358 con problemas de esquema |
| **Total** | **43.089** | Conservación exacta, una fila auditada por fila canónica |

No se presentan las 21.165 elegibles como empresas listas para recomendar. Solo 4.397 filas elegibles pertenecen a JPX/TWSE, mercados con un piloto previo validado pero todavía no escalado. El resto exige fuente, licencia, identidad o política adicional.

## Calidad de metadatos

- Ticker y nombre: completos en el censo; 3.206 filas siguen con identidad parcial por las reglas del proveedor.
- MIC disponible en 19.922 filas; falta en 23.167.
- Moneda disponible en 11.311; falta en 31.778.
- ISIN disponible en 7.942; falta en 35.147.
- Sector disponible en 3.705; industria en 4.401; capitalización solo en 23.

Estas ausencias son inventariadas, no rellenadas por inferencia. Los flags fila a fila permiten distinguir ausencia real, revisión y corrupción de esquema.

## Rutas de proveedor

- JPX y TWSE: `PILOT_VALIDATED_NOT_SCALED`; no equivalen a cobertura global. JPX tiene licencia de uso personal confirmada y ventana de precios limitada; TWSE usa datos abiertos pero precios no ajustados y un solo periodo fundamental en fase 5.
- Estados Unidos: `USER_ACCOUNT_AND_PILOT_REQUIRED`; Twelve Data es solo candidata y sus condiciones de caché no están resueltas.
- Cboe Europe, ASX y BVC: excluidos por falta de ruta accionable, fuente gratuita o serie histórica suficiente.
- Xetra y SGX: bloqueados por metadatos; no se confunde reparación de identidad con fuente de precios.
- HKEX, NSE, CBOE y NYSE Arca: requieren investigación de fuente, aunque hoy no aportan filas elegibles bajo la política vigente.

La matriz completa se encuentra en `provider_route_matrix_v2_38a.csv`. Toda limitación y licencia se conserva explícitamente.

## Conclusión

El proyecto ya dispone de un censo global reproducible para planificar fuentes, pero no de cobertura suficiente para puntuar o recomendar las 43.089 filas. El siguiente paso correcto es la fase 9B de planificación y adquisición por lotes, que queda expresamente sin autorizar.
