# v2.38AI — Austria: fundamentales reales vía firmenakte.at (real, con excepción de política aprobada por el usuario)

Fecha: 2026-09-06. Alcance: obtener fundamentales reales para las 20 empresas austriacas (identidad y registro ya resueltos al 100% vía GLEIF en v2.38AF).

## Contexto: por qué se usa una fuente comercial, con aprobación explícita

La investigación (documentada en la conversación) confirmó que **no existe ningún API oficial gratuito** para el Firmenbuch austriaco — el registro cobra por documentos/extractos, sin acceso programático gratuito. La única vía real con cifras financieras estructuradas es **firmenakte.at**, un agregador **comercial** (no oficial, no sin ánimo de lucro) de cuatro registros gubernamentales austriacos reales (Firmenbuch vía justizonline.gv.at, GISA, Ediktsdatei, BMF-Liste), con un nivel gratuito genuino y permanente (100 llamadas/mes, sin tarjeta de crédito). **El usuario aprobó explícitamente esta excepción** a la preferencia habitual de este proyecto por fuentes oficiales o sin ánimo de lucro, tras conocer la naturaleza comercial de la fuente.

## Ventaja real: sin ambigüedad de nombre en absoluto

A diferencia de GB/Irlanda/Francia, este bloque **no necesita ningún emparejamiento de nombre**: GLEIF ya dio el número real de Firmenbuch (`fnr`) de cada empresa en v2.38AF (ej. PORR AG → `34853f`), y el endpoint de firmenakte.at se consulta directamente por ese número (`GET /api/v1/businesses/{fnr}`) — cero ambigüedad posible.

## Bug real encontrado y corregido antes de aceptar el resultado

Las primeras 20 llamadas reales devolvieron **`HTTP 403` (Cloudflare, código de error 1010)** — no un reto anti-bot genuino (sin JavaScript, sin CAPTCHA), sino un **bloqueo específico de la cadena `User-Agent` por defecto de Python** (`Python-urllib/3.14`). Confirmado con una prueba en vivo: la misma llamada con `curl` (que la propia documentación de firmenakte.at recomienda como ejemplo) funciona sin problema. Corregido usando una cadena `User-Agent` honesta y descriptiva que identifica el script como investigación (`ScoutFinanceResearch/1.0`), nunca suplantando un navegador. Tras el cambio: **20/20 empresas obtenidas correctamente**.

## Resultado real

`scripts/run_europe_austria_fundamentals_v2_38ai.py` — extrae un conjunto cerrado de 11 conceptos (7 de balance: `bilanzSumme`, `anlageVermoegen`, `umlaufvermoegen`, `eigenkapital`, `verbindlichkeiten`, `rueckstellungen`, `liquidesVermoegen`; 4 de cuenta de resultados: `umsatzerloese`, `betriebsErfolg`, `ergebnisVorSteuern`, `jahresueberschuss`) para cada año fiscal disponible.

**Resultado real: 20/20 empresas obtenidas, 902 registros totales, 564 valores reales extraídos** (338 no etiquetados, nunca inventados) — entre **2 y 5 ejercicios fiscales por empresa** (2021–2025 según disponibilidad).

## Verificación de identidad contable — hallazgo real y honesto, no universal

Antes de aceptar el resultado, se verificó la identidad `Pasivo + Provisiones (Rückstellungen) + Patrimonio = Activo total` — la misma disciplina de verificación ya aplicada a Softcat/Kingfisher en GB.

- **Para PORR AG (FY2025), la identidad cuadra de forma exacta**: 1.150.919.959,54 + 35.129.999,93 + 589.899.666,58 = 1.775.949.626,05 ✓.
- **Pero no se cumple universalmente**: de 54 combinaciones empresa-año con los 4 conceptos presentes, **27 cuadran exactamente y 27 muestran un residuo real** (desde céntimos hasta decenas de millones, ej. UNIQA Insurance ~69M€, Österreichische Post ~35-65M€/año). Esto **no invalida los valores individuales** (siguen siendo cifras reales depositadas) — indica que algunas empresas (especialmente bancos como Raiffeisen/Erste/BAWAG bajo el esquema BWG, y aseguradoras como UNIQA bajo el esquema VAG) usan una estructura de balance estatutaria distinta a la de una empresa industrial bajo el UGB estándar, con un componente adicional (probablemente "Rechnungsabgrenzungsposten pasivos" u otra partida) no capturado en nuestra lista cerrada de conceptos. Se documenta con transparencia, no se oculta ni se fuerza un ajuste.

## Advertencia crítica: cifras de la entidad individual, no del grupo consolidado

**Confirmado con un ejemplo real**: OMV Aktiengesellschaft (la entidad matriz individual, no el "Grupo OMV" consolidado que se reporta a los inversores) muestra `umsatzerloese` (ingresos) de solo **289,5 millones de euros** en FY2024, pero `jahresueberschuss` (beneficio neto) de **1.623 millones de euros** — un patrón económicamente coherente para una sociedad holding pura (los ingresos por dividendos/participaciones de las filiales dominan la cuenta de resultados individual, no las ventas operativas, que están en las filiales). **Estas cifras son reales y correctas para la entidad jurídica individual depositada en el Firmenbuch, pero NO deben confundirse con las cifras consolidadas del grupo** que las empresas cotizadas reportan habitualmente a analistas e inversores. Esta advertencia se traslada íntegra a cualquier uso futuro de estos datos.

## Anomalía observada en la fuente (cosmética, no numérica)

El campo `legalForm` de firmenakte.at etiqueta la mayoría de las empresas como **"Anonim Şirket"** (turco, no alemán) en vez de "Aktiengesellschaft" — un error de traducción/etiquetado propio del proveedor (confirmado: PORR AG sí muestra correctamente "Aktiengesellschaft", STRABAG SE muestra correctamente "Europäische Gesellschaft (SE)", pero el resto de sociedades anónimas muestran la etiqueta turca). No afecta a ningún valor numérico, solo al campo de texto descriptivo — documentado como limitación observada de la fuente, no corregido silenciosamente.

## Pruebas offline

`tests/qa_europe_austria_fundamentals_v2_38ai.py` — 3 casos: dry-run sin red, bloqueo real sin credencial, **reproducción exacta de la forma de respuesta real de PORR AG** (2 ejercicios, campos ausentes en uno de ellos registrados como no etiquetados) incluyendo la **verificación de la identidad contable real**, y confirmación de que la clave nunca se filtra ni se registra.

```
.venv/Scripts/python.exe tests/qa_europe_austria_fundamentals_v2_38ai.py
PASS: v2.38AI-austria-fundamentals/dry-run-gate/blocked-without-credential/real-porr-shape/no-credential-leak
```

## Seguridad y alcance

- Red real usada: firmenakte.at (con la API key real del usuario, creada por él mismo, nunca vista ni registrada por este proyecto) — 20 llamadas reales, dentro del límite gratuito de 100/mes.
- Los valores financieros reales individuales (JSONL) quedan fuera de git (`.gitignore`), igual que en GB/Irlanda — solo se publica el perfil (identidad/estado, sin cifras) y el informe de cobertura agregado (recuentos, sin cifras).
- Escaneo de secretos confirmado: la clave nunca aparece en ningún fichero de salida.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C. `production_scoring_authorized: false`, `allow_ranking: false`.

## Resumen frente a las jurisdicciones ya tratadas

| | GB | Irlanda | Suiza | Italia | **Austria** |
|---|---:|---:|---:|---:|---:|
| Activos | 40 | 17 | 29 | 22 | **20** |
| Identidad/registro resuelto | 29/40 | 8/17 | 29/29 (GLEIF) | 22/22 (GLEIF) | **20/20 (GLEIF)** |
| Empresas con fundamentales reales | 2 | 0 | 0 (causa legal) | 0 (sin API) | **20/20, multi-año (2021-2025)** |
| Naturaleza de la fuente | Oficial (Companies House) | Oficial (CRO) | — | — | **Comercial, excepción aprobada por el usuario** |

**Estado del bloque: `COMPLETED_EUROPE_AUSTRIA_FUNDAMENTALS_REAL_MULTI_YEAR_COMMERCIAL_SOURCE`.** El resultado más rico en fundamentales reales de todo este proyecto hasta hoy (20 empresas, hasta 5 años cada una), obtenido mediante una excepción de política explícitamente aprobada por el usuario, con las limitaciones y advertencias (entidad individual vs. grupo consolidado, identidad contable no universal, anomalía cosmética de la fuente) documentadas con total transparencia.
