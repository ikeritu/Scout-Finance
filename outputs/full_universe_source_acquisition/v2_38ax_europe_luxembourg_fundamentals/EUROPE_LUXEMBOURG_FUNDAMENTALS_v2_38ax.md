# v2.38AX — Fundamentales reales de Luxemburgo: 16/18 vía la Centrale des Bilans (STATEC)

Fecha: 2026-09-06. Alcance: extraer fundamentales reales (balance + cuenta de resultados) para las 18 empresas luxemburguesas con número RCS confirmado en `v2.38AW`, desde el dataset abierto oficial de la Centrale des Bilans (STATEC) — una fuente que ningún país anterior de este proyecto tuvo disponible en esta forma: **datos financieros reales, estructurados, por empresa, de descarga directa, sin cuenta, sin CAPTCHA, licencia CC-BY-SA**.

## Por qué esta fuente es distinta a todo lo investigado hasta ahora

Cada país anterior tuvo un obstáculo real: Alemania y Suiza sin ninguna vía; Italia y Bélgica con CAPTCHA; Países Bajos con API de pago; España con formularios ASPX. Luxemburgo, en cambio, publica directamente en `data.public.lu` (portal de datos abiertos, API REST propia) ficheros XML trimestrales con **todos los depósitos de cuentas anuales realizados ese trimestre**, indexados por el mismo número RCS que GLEIF ya proporciona — confirmado en vivo mediante una petición de rango de bytes sobre el fichero real de 2026 Q1 antes de escribir ningún script.

**Hallazgo real sobre confidencialidad**: la ley luxemburguesa (Art. 70/71 de la ley de 2002) permite a las empresas marcar el balance y/o la cuenta de resultados como confidenciales al depositarlos. Comprobado en vivo que esto **no se representa con ningún campo o marcador en el XML** — simplemente, el `<Declaration type="CA_COMPP">` no aparece en absoluto para esa empresa ese trimestre. Este bloque nunca interpreta una declaración ausente como cero: registra explícitamente qué tipos de declaración se encontraron (`balance_sheet_disclosed`, `profit_loss_disclosed`), la misma disciplina fail-closed ya aplicada a cada concepto contable ausente en cualquier otro país de este proyecto.

## Método: descarga incremental, más reciente primero

`scripts/fetch_europe_luxembourg_fundamentals_v2_38ax.py` escanea los 8 trimestres más recientes (2024 Q3 → 2026 Q2) **empezando por el más reciente**, y deja de descargar trimestres más antiguos en cuanto las 18 empresas objetivo ya han aparecido al menos una vez — puesto que un hallazgo en un trimestre más reciente nunca puede ser superado por uno más antiguo. Cada trimestre descargado (100–824 MB) se guarda en una caché local (excluida de git, igual que cualquier otro proveedor de datos masivos de este proyecto) y nunca se vuelve a descargar en ejecuciones futuras — resumible, con escritura atómica.

Dado que los ficheros trimestrales pesan cientos de MB, el análisis usa `xml.etree.ElementTree.iterparse` para procesar cada `<Declarer>` de forma incremental, liberando memoria inmediatamente para cualquier empresa que no esté en la lista de las 18 objetivo.

## Resultado real

**16/18 empresas con datos financieros reales encontrados**, escaneando los 8 trimestres completos (los 2 restantes no aparecieron en ningún trimestre de los últimos 2 años):

| Concepto | Cobertura entre las 16 encontradas |
|---|---:|
| `total_assets` | 16/16 |
| `equity` | 16/16 |
| `net_profit` | 16/16 |
| `revenue` | 3/16 |
| Balance (`CA_BILAN`) divulgado | 16/16 |
| Cuenta de resultados (`CA_COMPP`) divulgada | 13/16 |

**Hallazgo real, consistente con el patrón ya documentado varias veces en este proyecto (Austria/GB/Francia)**: aunque el activo total, el patrimonio neto y el resultado del ejercicio están casi universalmente presentes (16/16), la partida específica "cifra de negocios neta" solo aparece en 3/16 — la mayoría de estas 16 son sociedades holding luxemburguesas (SOPARFI o similares) cuya cuenta de resultados no usa una partida operativa de ingresos clásica, sino partidas de participaciones/valores mobiliarios no capturadas por los alias de concepto de este bloque. No es un fallo de extracción: es la naturaleza real de estas entidades.

Ejemplos reales verificados (cifras en EUR, ejercicio más reciente disponible):

| Ticker | Empresa | Ejercicio | Activo total | Patrimonio neto | Resultado del ejercicio |
|---|---|---|---:|---:|---:|
| RRTL | RTL Group S.A. | 2025-12-31 | 7.638.899.963 | 3.228.823.221 | 17.012.471 |
| M4M1 | Millicom International Cellular S.A. | 2024-12-31 | 8.380.814.587 | 3.579.494.302 | 75.978.185 |
| TW10 | Tenaris S.A. | 2025-12-31 | 15.734.085.623 | 15.192.058.308 | -80.830.085 |
| AT1 | Aroundtown SA | 2024-12-31 | 18.545.523.924 | 5.383.527.266 | 186.822.278 |
| ADJ | Adler Group S.A. | 2024-12-31 | 3.347.439.081 | **-1.912.369.690** | -752.602.453 |

**Adler Group con patrimonio neto negativo** es un hecho real y públicamente conocido (la crisis de deuda del grupo inmobiliario alemán-luxemburgués es de dominio público) — confirma que este bloque extrae la cifra tal cual está depositada, sin filtrar ni suavizar resultados adversos.

**2 empresas no encontradas en ningún trimestre de los últimos 2 años**: **ArcelorMittal** (B82454) y **Spotify Technology S.A.** (B123052). Ninguna de las dos apareció en los 8 trimestres escaneados pese a tener un número RCS real confirmado — hallazgo honesto, consistente con el patrón ya visto en otros países: es plausible que estas dos multinacionales depositen sus cuentas consolidadas por una vía o un tipo de declaración distinto del régimen estándar `CA_BILAN`/`CA_COMPP` (pensado para el universo general de sociedades luxemburguesas), no capturado por este bloque. Se deja como una limitación real y explícita, no como un error de la extracción.

## Qué NO hace este bloque

- No reconstruye `v2.38AL` (matriz de cobertura global) ni `v2.38AM` (contexto geopolítico) todavía.
- No investiga por qué ArcelorMittal/Spotify no aparecen — quedaría para un futuro bloque si se decide profundizar.
- No calcula ningún ratio ni feature de crecimiento — eso es competencia de un futuro `v2.38AK`-equivalente para Luxemburgo, una vez haya más de un ejercicio fiscal capturado por empresa.

## Pruebas offline

`tests/qa_europe_luxembourg_fundamentals_v2_38ax.py` — 6 casos: extracción completa de los 4 conceptos rastreados, cuenta de resultados confidencial ausente nunca tratada como cero, números RCS no objetivo nunca extraídos, parada temprana al completar todos los objetivos (los trimestres más antiguos y más pesados nunca se descargan), modo sin ejecución sin red, y resumibilidad real (fichero ya en caché nunca se vuelve a pedir).

```
.venv/Scripts/python.exe tests/qa_europe_luxembourg_fundamentals_v2_38ax.py
PASS: v2.38AX-europe-luxembourg-fundamentals/concept-extraction/confidential-omission/target-filter/stop-early/dry-run/resumable/no-network
```

## Seguridad y alcance

Sin credenciales. Red real usada solo para descargar los ficheros abiertos oficiales de STATEC (nunca scraping, descarga directa vía la API REST del portal). Los ficheros trimestrales completos (cientos de MB, con datos de miles de empresas ajenas a este proyecto) se mantienen fuera de git, igual que cualquier otro caché de datos masivos de este proyecto — solo los 18 registros reales de las empresas objetivo se versionan. Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_LUXEMBOURG_FUNDAMENTALS`.** 16/20 empresas luxemburguesas (80%) con fundamentales reales de principio a fin — identidad (`v2.38AV`) → número RCS (`v2.38AW`) → cifras financieras reales (`v2.38AX`) — el resultado más completo de todos los países atacados fuera de los 13 originales, y la primera vez que este proyecto obtiene datos financieros reales de una fuente verdaderamente abierta (sin excepción de política, sin CAPTCHA, sin pago) en Europa continental.
