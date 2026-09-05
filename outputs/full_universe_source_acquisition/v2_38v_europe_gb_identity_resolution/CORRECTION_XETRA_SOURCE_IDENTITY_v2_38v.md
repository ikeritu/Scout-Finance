# Corrección de identidad GB — de OpenFIGI/ticker a fuente Xetra/ISIN (v2.38V)

Fecha: 2026-09-05. Este documento describe un **error real encontrado en trabajo ya comiteado y subido** (v2.38V y v2.38W), su causa raíz, y la corrección aplicada. No se oculta ni se minimiza: se documenta con el mismo nivel de detalle que cualquier hallazgo positivo de este proyecto.

## El error

`resolve_europe_gb_identity_v2_38v.py` (el resolutor original) trataba el campo `ticker` de cada uno de los 40 activos GB como si fuera un ticker real de la Bolsa de Londres (LSE), y lo buscaba en OpenFIGI con `exchCode="LN"`. **Ese campo nunca fue un ticker de LSE**: es el *mnemonic* interno que Deutsche Börse Xetra asigna a su propio listado secundario de una acción extranjera — un código arbitrario, sin relación con el ticker real de la empresa en su mercado de origen.

Dos veces, esa búsqueda produjo una coincidencia **exacta, única y en apariencia perfectamente fail-closed** — pero con la empresa equivocada, porque el mnemonic de Xetra coincidía por pura casualidad con el ticker real (no relacionado) de otra empresa cotizada en LSE:

| Mnemonic Xetra (nuestro "ticker") | Empresa que Xetra pretendía (real, por ISIN) | Empresa que OpenFIGI devolvió (ticker real coincidente por casualidad) |
|---|---|---|
| `SCT` | **SSE PLC** (ISIN `GB0007908733`) | SOFTCAT PLC (ticker real de LSE también es "SCT") |
| `BMT` | **BRITISH AMERICAN TOBACCO** (ISIN `GB0002875804`) | BRAIME (TF&JH) (ticker real de LSE también es "BMT") |

Ambos casos fueron verificados de forma independiente: consultando OpenFIGI por separado se confirma que "SCT" y "BMT" SÍ son, de verdad, los tickers reales de Softcat y Braime respectivamente en LSE — el fallo no fue una alucinación de OpenFIGI, fue usar el identificador equivocado (un mnemonic de otro mercado) como si fuera ese ticker.

Los otros 2 de los 4 "resueltos" originales (`RIO1`→RIO TINTO PLC, `RTO1`→RENTOKIL INITIAL) **sí eran correctos** — confirmado ahora de forma independiente contra la fuente autoritativa (ver abajo). No fue una coincidencia sistemática: fue una colisión real que ocurrió en 2 de 4 casos.

## Cómo se encontró

Al investigar por qué el resto de tickers no resolvían en OpenFIGI (para "ampliar identidades GB", instrucción explícita del usuario), se localizó el fichero original de Deutsche Börse Xetra ya descargado en una fase muy anterior del proyecto (`outputs/full_universe_source_acquisition/raw/deutsche_boerse_xetra_v2_14c/`, ya versionado en git desde entonces). Ese fichero tiene columnas `Instrument` (nombre real) e `ISIN` (identificador único global) — y confirma que la columna `Product Assignment Group` (p. ej. `"UKI0"`, `"AST0"`, `"ESP0"`) es un **código de segmento de mercado**, no un nombre de empresa. Esa es literalmente la causa raíz del problema `"UKI0"` ya documentado en v2.38T/S/V: en algún punto muy anterior de este proyecto, el pipeline de ingesta mapeó la columna equivocada a `company_name`.

## La corrección

`scripts/resolve_europe_gb_identity_xetra_source_v2_38v.py` — resuelve identidad buscando el mnemonic (`ticker`) directamente contra el fichero fuente local (sin red, sin OpenFIGI, sin colisión posible: el ISIN es único globalmente). Fail-closed: solo resuelve si el mnemonic aparece exactamente una vez con un único ISIN; ambiguo o ausente queda sin resolver, nunca se adivina.

**Resultado real: 40/40 resueltos, 0 sin resolver** — frente al 4/40 (2 de ellos erróneos) del método anterior. Lista completa de las 40 empresas reales en `europe_gb_identity_resolution_xetra_source_matrix_v2_38v.csv` — incluye nombres muy conocidos (Diageo, BAE Systems, British American Tobacco, Imperial Brands, Rio Tinto, SSE, BP, Lloyds, Barclays, Vodafone, Tesco, GSK, Shell, Unilever, Aviva, entre otras 27 más).

## Qué queda invalidado en v2.38V/W/X, y qué no

**No se borra ni se reescribe ningún commit anterior** — el historial de git se conserva íntegro; esta corrección se añade como trabajo nuevo, documentado con transparencia.

- `europe_gb_identity_resolution_matrix_v2_38v.csv` (original, OpenFIGI): **superado**, se conserva como registro histórico del error, no como fuente de verdad. La nueva `europe_gb_identity_resolution_xetra_source_matrix_v2_38v.csv` es la autoritativa a partir de ahora.
- `europe_companies_house_lookup_matrix_v2_38v.csv`: los datos de Rio Tinto y Rentokil Initial siguen siendo correctos (identidad correcta desde el principio). **El perfil de "Softcat PLC" está mal atribuido**: es un perfil real de Companies House, pero pertenece a Softcat, no al activo `U37446` (que representa a SSE PLC). Braime quedó correctamente sin resolver por el resolutor de Companies House (nunca se llegó a confirmar), así que no hay dato erróneo ahí, solo la búsqueda de partida (Braime) era la empresa equivocada.
- `outputs/full_universe_source_acquisition/v2_38w_europe_ixbrl_fundamentals/`: **los 14 valores IFRS extraídos son reales y correctos para Softcat PLC** (verificados con 4 identidades contables exactas) — pero **no representan al activo `U37446` de nuestro censo**, que debería ser SSE PLC. Esta extracción queda marcada como mal atribuida, no como incorrecta en sí misma.
- `outputs/full_universe_source_acquisition/v2_38x_europe_candidate_feature_matrix/`: el único candidato de la matriz (basado en las features de "Softcat") queda igualmente mal atribuido a `U37446`.

## Próximo paso (pendiente de decisión del usuario)

Con 40 identidades reales confirmadas (frente a 4 antes, 2 de ellas erróneas), el paso natural sería repetir el piloto de Companies House + extracción iXBRL de v2.38V/W para las 40 empresas reales — una ampliación sustancialmente mayor que la piloteada hasta ahora. Esto se deja explícitamente para una decisión del usuario ("ampliar identidades primero, luego reevaluamos"), no se ejecuta automáticamente en esta corrección.

## Pruebas offline

`tests/qa_europe_gb_identity_xetra_source_v2_38v.py` — 5 casos, sin red, con fixture sintético del formato del fichero Xetra: resolución exacta con nombre limpio y crudo preservados; **prueba de regresión dedicada que reproduce exactamente la colisión SCT/Softcat-vs-SSE** confirmando que la nueva lógica nunca resuelve por el ticker real de una empresa no relacionada; mnemonic ausente → sin resolver; ISIN ambiguo → sin resolver; limpieza de nombre sin pérdida del valor crudo.

```
.venv/Scripts/python.exe tests/qa_europe_gb_identity_xetra_source_v2_38v.py
PASS: v2.38V-gb-identity-xetra-source/ticker-collision-regression/ambiguous-isin/no-network
```

## Seguridad y alcance

- Sin red: la resolución usa exclusivamente el fichero fuente ya local y ya versionado en git desde una fase anterior.
- Sin credenciales en este bloque de corrección.
- Sin scoring, ranking, recomendaciones, fase 9C.

**Estado: corrección completa de identidad (40/40, 0 ambiguos). Companies House + iXBRL para las 40 empresas reales queda pendiente de decisión explícita del usuario.**
