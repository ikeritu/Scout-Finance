# v2.33C — diseño de fuentes financieras

Estado: **PASS · arquitectura híbrida validada · sin compras, claves ni llamadas de adquisición**.

## Decisión

- SEC/EDGAR: fundamentales oficiales estadounidenses.
- OpenFIGI: resolución de identificadores.
- EODHD: candidato preferente para un piloto mundial de pago, condicionado a licencia y cobertura real.
- Twelve Data: validación y contingencia, no duplicación completa inicial.
- Alpha Vantage: pruebas puntuales; descartado como fuente gratuita principal por su límite diario.

La configuración reproducible está en `config/data_sources_v2_33c.json`. Antes de contratar un proveedor se ejecutará un piloto estratificado de 240 activos y se solicitará una decisión explícita del usuario.
