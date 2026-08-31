# Scout Finance v2.33P — reparación de metadatos SGX y Xetra (Bloque E)

Fecha: 2026-08-31. Alcance: reparación determinista de identidad (ticker/nombre de empresa) sobre los 1.782 candidatos retenidos por corrupción de esquema. **No se ha tocado ningún precio ni ninguna fuente de precios en este bloque** — es exclusivamente reparación de metadatos, previa a cualquier decisión de fuente de precios (E3/E4). El censo canónico (`eligibility_census_v2_33b2.csv.xz`) **no se ha sobrescrito**: toda reparación se ha escrito como archivos delta separados en este mismo directorio.

## E1 — SGX (358 filas retenidas)

**Causa exacta reproducida y confirmada al 100 % de las filas, no sobre una muestra:** las columnas `ticker` y `company_name` están intercambiadas en el origen (`sgx_structured_endpoint`). Las 358 filas, sin excepción, tienen `ticker` con formato de precio decimal (p. ej. `"0.845"`) y `company_name` con formato de código de acción corto (p. ej. `"LVR"`, `"1Y1"`, `"533"`). Ninguna fila se desvía de este patrón (verificado con expresión regular contra las 358 filas completas).

**Reparación:** el código de acción real se traslada a `ticker`; el valor decimal (que era un precio desactualizado, no un dato de identidad) se descarta; `company_name` se marca como **genuinamente ausente** (`missing_company_name=True`), no se completa con ninguna inferencia. El nombre real de la empresa **no está presente en esta fuente** — no es recuperable sin consultar una fuente externa adicional, lo cual queda fuera de alcance de este bloque.

**Resultado:** 358/358 (100 %) reparadas en el sentido de "ticker recuperado correctamente". 0 sin resolver. Contraste posterior a un dry run, con evidencia antes/después conservada en `sgx_repair_delta_v2_33p.csv` (no sobrescribe el censo canónico).

## E2 — Xetra (1.424 filas retenidas)

**Causa exacta confirmada:** el campo `company_name` contiene un código de clasificación de segmento/índice de Deutsche Börse (`NAM0`, `GER0`, `DAX1`, `MDX1`, `SDX1`, `LUX0`, `UKI0`, `FRA0`, `SWI0`, `ITA0`, `AST0`, `ESP0`, etc. — 17 códigos distintos observados), no el nombre de la empresa. Todas las 1.424 filas tienen un ISIN válido, único y sin duplicados (verificado contra el conjunto completo) — el nombre real es recuperable de forma independiente por ISIN.

**Reparación:** consulta al endpoint público `/v3/mapping` de OpenFIGI (sin cuenta, sin clave, ya aprobado en v2.33C/H) con `idType=ID_ISIN`, en lotes de 10 ISIN por petición, a un ritmo de 3 s entre peticiones con reintento automático ante error 429. **Fail-closed real, no una formalidad**: un ISIN solo se acepta como reparado si OpenFIGI devuelve al menos un registro y **todos** los registros devueltos coinciden en el mismo `name` — nunca se elige entre nombres discrepantes.

**Resultado real (no una muestra):**

| Resultado | Filas | % |
|---|---:|---:|
| Reparadas (nombre recuperado, coincidencia exacta) | 1.256 | 88,2 % |
| Sin resolver: nombres discrepantes entre registros de OpenFIGI | 163 | 11,4 % |
| Sin resolver: sin registro en OpenFIGI para ese ISIN | 5 | 0,4 % |
| **Total retenido** | **1.424** | **100 %** |

Ejemplos reales recuperados (verificables en `xetra_repair_delta_v2_33p.csv`): `STRABAG SE-BR` (antes: `AST0`), `RAIFFEISEN BANK INTERNATIONAL` (antes: `AST0`), `OMV AG` (antes: `AST0`).

**Nota honesta sobre las 163 discrepancias:** una parte de estas probablemente se debe a que OpenFIGI devuelve varios registros para el mismo ISIN con sufijos de clase de acción ligeramente distintos (p. ej. `"-REG"`) que mi criterio de coincidencia exacta no normaliza en este script (a diferencia del normalizador de nombres usado en v2.33H para Cboe Europe). No se ha confirmado cuántas de las 163 se resolverían con esa misma normalización — queda como mejora futura documentada, no aplicada aquí para no introducir una regla nueva sin probarla contra el conjunto completo.

**168 filas siguen bloqueadas de forma fail-closed**, sin nombre inventado ni inferido.

## E3 — Fuente de precios: no investigada en este bloque

Este bloque repara identidad, no busca fuente de precios. Antes de investigar precios para SGX o Xetra:

- **SGX:** con la reparación de E1, los 358 activos ahora tienen un ticker real recuperado. v2.33F ya había investigado fuentes de precios generales para SGX sin resultado accionable gratuito completo (ver `v2_33f_official_exchange_sources_evaluation`) — no se reabre esa investigación sin un hallazgo nuevo evidente, según la instrucción explícita del encargo para Cboe Europe, extendida aquí por prudencia al mismo patrón.
- **Xetra:** con 1.256 nombres recuperados, en teoría podrían mapearse a un piloto de precios — pero **no se ha investigado ninguna fuente de precios oficial y gratuita para Xetra en este bloque**. v2.33H ya encontró que el único dataset gratuito conocido de Deutsche Börse (AWS Public Dataset) está descatalogado y sin mantenimiento. No hay evidencia nueva que cambie esa conclusión.

**No se clasifica SGX ni Xetra como `EXCLUDED_NO_FREE_SOURCE` todavía** — la reparación de identidad no implica automáticamente que no haya fuente; simplemente no se ha buscado en este bloque. Quedan en `BLOCKED_METADATA_CORRUPTION` parcialmente resuelto (identidad reparada), con la fuente de precios como pregunta abierta separada.

## E4 — Condición de cierre

Siguiendo la condición explícita del encargo ("SGX y Xetra pueden considerarse cerrados aunque no tengan precios, si la corrupción queda reparada o formalmente irresoluble, su impacto está medido, la ausencia de fuente queda documentada, y el estado operativo es explícito"):

- **SGX:** corrupción reparada al 100 % (358/358). Impacto medido. Sin fuente de precios investigada en este bloque (ver E3). Estado operativo: **identidad reparada, sin fuente de precios evaluada**.
- **Xetra:** corrupción reparada al 88,2 % (1.256/1.424); 168 filas formalmente irresolubles con la evidencia disponible (discrepancia real entre fuentes o ausencia de registro). Impacto medido. Sin fuente de precios investigada en este bloque. Estado operativo: **identidad mayoritariamente reparada, sin fuente de precios evaluada**.

Este bloque se cierra como **reparación de metadatos completada**, no como "mercado operativo": ningún activo de SGX o Xetra pasa a tener una fuente de precios validada por este cierre.

## Seguridad y alcance

- No se ha creado ninguna cuenta (OpenFIGI no la requiere).
- No se ha usado ninguna clave.
- No se ha gastado dinero.
- El censo canónico **no se ha modificado**; toda reparación vive en archivos delta separados en este directorio.
- No se ha descargado ningún precio.
- `production_scoring_authorized: false`, `allow_ranking: false`.

## Estado del roadmap

- No cambia el estado de v2.33H ni de v2.33F respecto a la fuente de precios de estos mercados.
- Progreso de identidad: SGX 100 % reparado, Xetra 88,2 % reparado — pendientes de decidir si se integran en el censo canónico oficial (requeriría una revisión aparte, ya que este bloque los deja como delta, no como sustitución).
- Siguiente paso, no ejecutado: decidir si se investiga una fuente de precios para SGX/Xetra ahora que la identidad está mayoritariamente reparada, o si se acepta que ambos mercados quedan fuera del universo operativo por ahora.
