# v2.38AV — Los 25 activos que v2.38N nunca llegó a clasificar: 5 países nuevos, incluido Luxemburgo

Fecha: 2026-09-06. Alcance: resolver la identidad real de los **25 activos** que la fase de resolución de casa de cotización (`v2.38N`) marcó como `COUNTRY_EXCHANGE_MISMATCH_REVIEW` — una bandera de país (BG/KY/LI/LU/MT) en conflicto con el mapeo de bolsa (XETR/DE) — y que por eso nunca llegaron a formar parte de los 689 activos "en alcance" que `v2.38Q` enrutó y que todo el trabajo posterior (identidad, registro, fundamentales, crecimiento, sector) ha ido atacando país por país.

## Por qué este bloque

El usuario pidió atacar "el hueco de fundamentales para los 9.900 restantes". Antes de construir nada, se comprobó qué hay realmente detrás de esa cifra — no corresponde a ningún bloque real de este proyecto. Los tres huecos reales que sí existen en `v2.38N` son:

| Categoría real (`v2.38N`) | Filas | Naturaleza |
|---|---:|---|
| `CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED` | 21.066 | Cboe Europe es solo cotización secundaria; ya investigado en `v2.33H` y confirmado que el código de cambio compuesto de OpenFIGI no es fiable a esta escala |
| `ADR_GDR_REVIEW_REQUIRED` | 88 | Certificados de depósito de empresas **no europeas** (Japón, India, Taiwán, Egipto, Omán, Qatar, Baréin, Kazajistán) |
| `COUNTRY_EXCHANGE_MISMATCH_REVIEW` | 25 | Nunca identificadas — objeto de este bloque |

Presentados los tres al usuario con su evidencia real, **eligió atacar los 25** — el único de los tres alcanzable con el método ya probado, sin abrir ningún proyecto nuevo de escala distinta.

## Método: el mismo ya probado 4 veces, sin cambios

`scripts/resolve_europe_mismatch_identity_xetra_source_v2_38av.py` reutiliza exactamente el mismo mecanismo de `v2.38V/Z/AA/AB`: resolución directa contra el fichero fuente local de Deutsche Börse Xetra (Mnemonic → ISIN/Instrument, sin red, fail-closed). La única adición real: el país verdadero de cada empresa se lee ahora del **prefijo ISO 6166 del ISIN** (los dos primeros caracteres del ISIN), no de la bandera de país del censo ni del campo de bolsa mapeada — que es exactamente el conflicto que `v2.38N` había dejado sin resolver.

## Resultado real

**25/25 resueltos, 0 ambiguos, 0 sin resolver.** El prefijo ISIN confirma que la bandera de país del censo **era correcta desde el principio** — el conflicto real siempre estuvo en el campo de bolsa/país "home" (XETR/DE), no en la clasificación de país del censo:

| País real (por ISIN) | Empresas | Ejemplos reales verificados |
|---|---:|---|
| Luxemburgo | 20 | RTL Group, ArcelorMittal, Spotify Technology S.A., Aroundtown, Grand City Properties, Tenaris S.A., Millicom International Cellular, CPI Property Group, Adler Group, Befesa, Global Fashion Group, Corestate Capital |
| Bulgaria | 2 | Shelly Group PLC, Sirma Group Holding |
| Liechtenstein | 1 | Cerdios SE |
| Cayman Islands | 1 | Joby Aviation |
| Malta | 1 | Samara Asset Group |

**Hallazgo real, verificable de forma independiente**: Spotify Technology S.A. y ArcelorMittal S.A. son dos de las empresas más conocidas del mundo, y ambas están legalmente incorporadas en Luxemburgo — un patrón real y muy común (holdings/inmobiliarias/tecnológicas incorporadas en Luxemburgo por motivos legales/fiscales, cotizando en otro mercado). Ninguna de las 25 había tenido su identidad resuelta antes de este bloque; todas seguían con el placeholder de segmento de Xetra (`LUX0`, `SDX1`, `NEWX`, `MDX1`, `SWI0`, `NAM0`, `ITA0`) como nombre de empresa.

## Qué NO hace este bloque (alcance deliberadamente limitado)

- **No investiga ningún registro mercantil todavía.** Luxemburgo (RCS — Registre de Commerce et des Sociétés), Malta (MBR), Bulgaria (Registro Mercantil búlgaro), Liechtenstein y el registro de Islas Caimán son 5 jurisdicciones completamente nuevas para este proyecto — ninguna se ha investigado para fundamentales, siguiendo la misma disciplina de "identidad primero, registro después" ya aplicada a los 13 países anteriores.
- **No toca los otros dos huecos reales** (`CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED`, 21.066 filas; `ADR_GDR_REVIEW_REQUIRED`, 88 filas) — quedan explícitamente fuera, a la espera de que el usuario decida si se atacan y con qué prioridad.
- **No reconstruye `v2.38AL`** (matriz de cobertura global) ni `v2.38AM` (contexto geopolítico) todavía — se hará en el próximo bloque si se decide seguir con el registro de Luxemburgo.

## Pruebas offline

`tests/qa_europe_mismatch_identity_xetra_source_v2_38av.py` — 5 casos: selección exclusiva de filas `COUNTRY_EXCHANGE_MISMATCH_REVIEW` (ignora cualquier otro estado del fichero de 22.578 filas), resolución real de RTL Group con el prefijo ISIN (LU) resolviendo el conflicto frente al campo de bolsa (DE), mnemonic no encontrado, ISIN ambiguo, y prefijo de país nunca visto (fail-visible, nunca inventado).

```
.venv/Scripts/python.exe tests/qa_europe_mismatch_identity_xetra_source_v2_38av.py
PASS: v2.38AV-europe-mismatch-identity-xetra-source/status-filter/isin-country-override/ambiguous/unmapped-prefix/no-network
```

## Seguridad y alcance

Sin red (fichero fuente ya local desde v2.14c), sin credenciales, sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_MISMATCH_IDENTITY_RESOLUTION`.** 25/25 activos con identidad real, revelando 5 países nuevos para el proyecto — Luxemburgo, con diferencia el más grande (20/25) y con varias empresas de renombre mundial. El siguiente paso natural es decidir si se investiga el registro mercantil de Luxemburgo (RCS) para fundamentales, siguiendo la misma disciplina de investigación previa ya aplicada a los 13 países anteriores.
