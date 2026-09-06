# v2.38AF — Generalización: registro real vía GLEIF para 7 países de golpe

Fecha: 2026-09-06. Alcance: generalizar el método GLEIF (identidad por ISIN, sin ambigüedad de nombre, ya probado en Países Bajos: 36/44) a **los 7 países del universo europeo que aún no tenían ningún trabajo de registro**: Suiza (29), Italia (22), Dinamarca (21), Austria (20), Bélgica (6), Finlandia (5), Suecia (4) — **107 activos en una sola ejecución**, en vez de repetir un bloque por país.

## Por qué generaliza limpiamente donde el método por nombre no podía

Cada país anterior (GB, Irlanda, Francia) necesitó su propia lógica de emparejamiento por nombre contra el buscador de ese país en concreto, y cada uno topó con problemas reales y distintos (nombres abreviados de Xetra, empresas activas duplicadas). GLEIF evita todo eso: cada activo ya tiene un ISIN real y único desde v2.38AB, y GLEIF resuelve ISIN → registro LEI → autoridad de registro nacional + número directamente, sin ningún texto que comparar. El mismo script funciona igual de bien en cualquier país con emisores registrados en LEI (prácticamente todos los valores regulados europeos), porque el propio modelo de datos de GLEIF es agnóstico al país.

## Resultado real

`scripts/run_europe_gleif_registry_lookup_v2_38af.py` — mismo método de v2.38AE, generalizado con un parámetro `--countries` en vez de estar fijado a un solo país.

**Resultado real: 102/107 confirmados.**

| País | Resueltos | Autoridad de registro real confirmada |
|---|---:|---|
| Suiza (CH) | 29/29 | Dos autoridades reales distintas: `RA000549` (18 empresas, ej. Holcim AG → CHE-100.136.893) y `RA000548` (11 empresas, ej. Highlight Communications AG → CHE-100.774.645) — refleja que Suiza tiene varios registros cantonales/centrales reales, no uno solo |
| Italia (IT) | 22/22 | `RA000407` — Registro delle Imprese (ej. Assicurazioni Generali → 00079760328) |
| Dinamarca (DK) | 21/21 | `RA000170` — Erhvervsstyrelsen/CVR (ej. Carlsberg A/S → 61056416) |
| Austria (AT) | 20/20 | `RA000017` — Firmenbuch (ej. Strabag SE → 88983h) |
| Bélgica (BE) | 6/6 | `RA000025` — Banque-Carrefour des Entreprises (ej. KBC Groep → 0403.227.515) |
| Suecia (SE) | 4/4 | `RA000544` — Bolagsverket (ej. H&M → 5560427220) |
| **Finlandia (FI)** | **0/5** | — |

## Finlandia: un hallazgo real y confirmado, no un fallo del método

Las 5 empresas finlandesas (Nokia, UPM-Kymmene, Nordea Bank, SRV Yhtiöt, Sampo) dieron `no_lei_record_for_isin`. **Comprobado directamente en vivo, fuera del script**: una consulta manual a GLEIF con el ISIN real y correcto de Nokia (`FI0009000681`, confirmado independientemente como el ISIN real de Nokia) devuelve **0 resultados** — no es un error de nuestro ISIN ni de la codificación de la consulta, es una laguna real y confirmada en el propio mapeo ISIN↔LEI que GLEIF publica (depende de que cada emisor auto-declare sus ISIN a GLEIF; algunos mercados nórdicos tienen huecos conocidos en esa autodeclaración). Se documenta como limitación real de la fuente, no se fuerza ninguna coincidencia alternativa.

## Qué NO hace este bloque (alcance deliberadamente limitado)

- **No investiga ninguna fuente de fundamentales/cuentas anuales** para ninguno de estos 7 países. Confirmar si Suiza, Italia, Dinamarca, Austria, Bélgica, Suecia o Finlandia tienen un dataset abierto de cuentas reales (como el de Países Bajos) exige investigación real país por país, igual que se hizo para GB/Irlanda/Francia/Países Bajos — queda para bloques futuros.
- **No reintenta Finlandia con otro método.** Dado que el problema es una laguna real y confirmada del propio GLEIF, intentarlo por nombre (el método que ya causó problemas de ambigüedad en Francia) no es la solución correcta aquí — se documenta como pendiente, no se improvisa un rodeo.

## Pruebas offline

`tests/qa_europe_gleif_registry_lookup_v2_38af.py` — 3 casos: dry-run limitado a los países seleccionados sin red, **resolución real de tres países simultáneos en una sola ejecución** (Suiza/Italia/Dinamarca, sin filtro de jurisdicción ni lógica específica por país), sin registro LEI queda sin resolver.

```
.venv/Scripts/python.exe tests/qa_europe_gleif_registry_lookup_v2_38af.py
PASS: v2.38AF-gleif-registry-lookup/multi-country-single-run/isin-keyed/no-credential-needed
```

## Seguridad y alcance

- Red real usada: GLEIF (público, sin cuenta, CC0, sin límite documentado) — 107 llamadas.
- Ninguna cuenta creada, ninguna credencial usada ni necesaria.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C. `production_scoring_authorized: false`, `allow_ranking: false`.

## Resumen acumulado de registro por país (todo el proyecto hasta hoy)

| País | Activos | Registro confirmado | Método |
|---|---:|---:|---|
| GB | 40 | 29 | Nombre (Companies House) |
| Irlanda | 17 | 8 | Nombre (CRO) |
| España | 15 | — (sin vía) | — |
| Alemania | 413 | — (sin vía) | — |
| Francia | 53 | 18 | Nombre (registro FR) |
| Países Bajos | 44 | 36 | **ISIN (GLEIF)** |
| Suiza | 29 | 29 | **ISIN (GLEIF)** |
| Italia | 22 | 22 | **ISIN (GLEIF)** |
| Dinamarca | 21 | 21 | **ISIN (GLEIF)** |
| Austria | 20 | 20 | **ISIN (GLEIF)** |
| Bélgica | 6 | 6 | **ISIN (GLEIF)** |
| Suecia | 4 | 4 | **ISIN (GLEIF)** |
| Finlandia | 5 | 0 | **ISIN (GLEIF)** — laguna confirmada de la fuente |

**Estado del bloque: `COMPLETED_EUROPE_GLEIF_REGISTRY_LOOKUP_MULTI_COUNTRY`.** 102/107 confirmados en una sola ejecución, con 6 países al 100% (Suiza, Italia, Dinamarca, Austria, Bélgica, Suecia) y 1 laguna real y documentada (Finlandia). Con esto, **el registro oficial de identidad está confirmado para 10 de los 13 países del universo europeo** (todos salvo España, Alemania y Finlandia, cada uno por una razón real y distinta ya documentada).
