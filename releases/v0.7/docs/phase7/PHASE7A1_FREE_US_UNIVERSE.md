# Scout Finance — Fase 7A.1: descarga gratuita del universo USA

## Objetivo

Conseguir automáticamente un listado amplio de símbolos USA sin pagar API.

## Fuente

Se usan ficheros públicos de Nasdaq Trader:

```text
https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt
https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt
```

## Qué genera

```text
data/raw/universe_source_real.csv
outputs/scouting/free_us_universe_download_summary.json
```

## Limitación importante

Este universo gratuito trae símbolos y nombres, pero no trae:

```text
Market Cap
Last Sale
Volume
Sector
Industry
```

Por eso Stage 1 podrá validar estructura, pero muchas empresas caerán hasta que añadamos enriquecimiento de market data.

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.download_free_us_universe
.\.venv\Scripts\python.exe scripts/check_phase7a1_free_us_universe.py
.\.venv\Scripts\python.exe -m src.run_real_universe_pilot --input data/raw/universe_source_real.csv --limit 500 --source nasdaqtrader_free
.\.venv\Scripts\python.exe scripts/check_phase7a_real_universe_pilot.py
```

## Siguiente fase

```text
Fase 7A.2 — Enriquecimiento gratuito de precio, volumen y market cap
```
