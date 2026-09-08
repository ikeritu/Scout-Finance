# v2.38BQ — las 530 ambiguas: 200 resueltas de verdad, 174 candidatas sin confirmar, 156 siguen ambiguas

Fecha: 2026-09-08. Alcance: el usuario pidió continuar con las 530 empresas que `v2.38BC` había dejado marcadas como "ambiguas" — múltiples entidades reales y distintas de GLEIF coincidiendo exactamente con el mismo nombre normalizado, donde la disciplina fail-closed correctamente se negó a adivinar entre ellas.

## Lo que la investigación real encontró antes de escribir ningún código de producción

Un piloto real contra una muestra amplia de las 530 mostró que la mayoría de esta "ambigüedad" no es confusión real entre empresas distintas — es que una gran multinacional tiene muchas filiales nacionales reales, cada una con su propio LEI, que comparten el mismo nombre tras quitar la forma jurídica (Volkswagen AG tenía un duplicado real en Alemania y un fondo francés retirado junto a su única filial alemana realmente activa; AbbVie Inc tenía 12 filiales nacionales reales, y solo la de EE. UU. compartía la forma jurídica "Inc" del nombre de origen).

## Dos señales reales de GLEIF, nunca una suposición

**Nivel 1 (resuelto, mismo nivel de confianza que cualquier otra coincidencia por nombre ya aceptada en este proyecto)**: de las coincidencias exactas de nombre, si exactamente una tiene `registration.status == "ISSUED"` (la propia GLEIF marcando qué registro está actualmente activo y mantenido, frente a LAPSED, RETIRED, ANNULLED o DUPLICATE — estados reales, nunca inferidos), se resuelve a esa.

**Nivel 2 (candidata sin confirmar, deliberadamente NO "resuelta")**: si quedan varias con `ISSUED`, se comprueba si exactamente una comparte la misma forma jurídica final (p. ej. "AG", "Inc", "ASA") que el propio nombre de origen de Cboe. Si es así, se guarda como candidata real y plausible — pero **nunca como identidad resuelta**.

## El hallazgo real que obligó a bajar el Nivel 2 de categoría

Validando este nivel contra datos reales de GLEIF en vivo se encontraron **dos casos reales, no hipotéticos**:

- **ACEA SpA** (ticker Cboe `ACEm`, el sufijo "m" marcando que es un espejo de su cotización real en la Borsa Italiana) resolvió correctamente a `ACEA S.P.A.` (Italia, LEI real `549300Q3448N041CTH56`) — pero solo tras encontrar y corregir un bug real: GLEIF registra la forma jurídica italiana como "S.P.A." (letras separadas por puntos), y la normalización de `v2.38BB` convierte los puntos en espacios ANTES de comprobar la forma jurídica final, así que "S.P.A." se convertía en tres palabras sueltas ("S", "P", "A") y nunca coincidía con la forma reconocida "SPA". Sin el arreglo, "ACEA SpA" ni siquiera aparecía como candidata real de Italia — solo dos empresas francesas homónimas sin relación aparecían, y el nivel 2 casi elige la equivocada.
- **Danone SA**, en cambio, sí eligió la entidad equivocada: el nivel 2 la redujo a una filial española real y activa (`DANONE SA`, España) cuyo propio nombre coincide con el sufijo "SA" del nombre de origen — pero la empresa matriz francesa real está registrada en GLEIF simplemente como `DANONE`, sin ningún sufijo, así que nunca entró en la comparación y quedó descartada en silencio.

**Esta es la razón real por la que el Nivel 2 nunca se etiqueta "resuelto"**: el propio mecanismo no puede distinguir el caso de ACEA (correcto) del caso de Danone (incorrecto) en el momento de decidir — ambos producen exactamente un candidato tras el filtro, con la misma apariencia de certeza. Se guarda como candidata real y útil para revisión humana, nunca como identidad silenciosa.

## Resultado real

| Resultado | Empresas | Empresas de ejemplo reales |
|---|---:|---|
| **Resuelto (Nivel 1)** | **200** | Volkswagen AG→DE, Broadcom Inc→US, HP Inc→US, AcadeMedia AB→SE, Aker BP ASA→NO, Amgen Inc→US |
| **Candidata sin confirmar (Nivel 2)** | **174** | AbbVie Inc→US (probablemente correcto), Danone SA→ES (confirmado incorrecto) |
| **Sigue ambigua** | **156** | Accenture PLC (11 candidatas reales en 11 países), RTX Corp (3 países, los 3 con registro activo), American Express Co (2 entidades activas en EE. UU.) |
| **Total** | **530** | |

Solo las 200 del Nivel 1 se conectan a la matriz de cobertura (`v2.38AL`, decimosexta reconstrucción) como identidad real resuelta — el mismo nivel de confianza que cualquier otra coincidencia por nombre ya aceptada en este proyecto. Las 174 del Nivel 2 quedan documentadas en el propio fichero de este bloque como candidatas reales pero no verificadas, disponibles para revisión manual, nunca mezcladas con identidad confirmada.

## Impacto real en la matriz de las 43.089 (decimosexta reconstrucción de `v2.38AL`)

`NO_DATA_YET` baja de 38.055 a **37.855** (-200, exacto). De las 200 nuevas: 195 quedan en `IDENTITY_ONLY_NO_FUNDAMENTALS_YET` (fundamentales todavía no investigados para esta población) y 5 caen automáticamente en `IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED` (`v2.38BM`) porque su país real resuelto resultó ser una de las 6 jurisdicciones offshore ya cerradas por hecho legal — el mismo chequeo posterior ya existente se aplicó correctamente sin cambio alguno.

## Qué NO hace este bloque

No calcula fundamentales ni crecimiento para las 200 empresas nuevas — solo identidad. No promueve ninguna de las 174 candidatas del Nivel 2 a identidad resuelta. No corrige el bug real de normalización de puntos ("S.P.A.") dentro del propio `v2.38BB` compartido — se corrige solo localmente en este script, para no alterar retroactivamente el comportamiento de fases ya completadas y documentadas que importan esa función sin cambios (`v2.38BC`, la resolución completa de 7.590 candidatas; `v2.38BF`, Austria y Finlandia). Si el usuario decide que vale la pena, corregir `v2.38BB` y volver a ejecutar la resolución completa de 7.590 candidatas queda como una decisión real y explícita, pendiente, no tomada aquí — podría rescatar algunas empresas italianas más entre las 3.294 ya marcadas "sin resolver".

## Pruebas offline

9 casos en `tests/qa_europe_cboe_ambiguous_disambiguation_v2_38bq.py`: Nivel 1 resuelve con un único registro activo, Nivel 2 nunca se etiqueta "resuelto" aunque acierte (caso AbbVie), el bug real de "S.P.A." se corrige y verifica con el caso real de ACEA, **el caso real de Danone demuestra explícitamente que el Nivel 2 puede elegir la entidad equivocada**, ninguna coincidencia sin forma jurídica compartida se resuelve nunca, sin coincidencia exacta tras el arreglo se queda sin resolver, resumibilidad real (sin llamada de red para una clave ya procesada), dry-run sin ninguna llamada de red, y bloqueo real si falta el fichero de entrada. Más 2 pruebas nuevas en `qa_global_coverage_matrix_v2_38al.py` (23 en total): las resueltas del Nivel 1 obtienen identidad real, las candidatas sin confirmar del Nivel 2 nunca se convierten en identidad.

## Seguridad y alcance

Red real usada solo contra la API pública de GLEIF (mismo endpoint y ritmo ya aprobados y usados en `v2.38BB`/`BC`/`BF`), en 3 bloques resumibles de 200. Sin credenciales. Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_CBOE_AMBIGUOUS_DISAMBIGUATION`.** 530/530 procesadas, 200 con identidad real nueva y verificable, 174 con una candidata real pero honestamente sin confirmar, 156 correctamente siguen sin resolver — ningún dato inventado, ningún silencio sobre lo que no se sabe.
