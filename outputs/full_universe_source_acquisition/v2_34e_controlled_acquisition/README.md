# v2.34E — adquisición controlada real (Bloque E, fase 5)

Estado: **`COMPLETED`** — ambas puertas superadas con datos reales, cobertura 100% en activos.

## Resultado

- **JPX**: 42/42 activos, 0 fallos, 389 divulgaciones reales, ~2 años de historia con los 4 tipos de periodo. Cobertura núcleo (revenue/net_income/total_assets/eps/equity_ratio) del 87.9% (342/389) — el resto son revisiones de previsión (`EarnForecastRevision`/`DividendForecastRevision`), no estados financieros reales; recomendado excluirlas en el Bloque F.
- **TWSE**: 8/8 activos, 0 fallos, un único periodo por empresa (año ROC 115, Q2), cobertura 100% en las 11 métricas confirmadas en v2.34B.
- Reporte reproducible sin red: `fundamentals_acquisition_report_v2_34e.json` (`scripts/build_fundamentals_acquisition_report_v2_34e.py`).

Detalle completo en `CONTROLLED_ACQUISITION_v2_34e.md`.
