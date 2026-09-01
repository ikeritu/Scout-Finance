# Scout Finance v2.37H — gate de fase 8

## Decisión final

`COMPLETED_LOCAL_PRODUCT`

La implementación, la QA offline y el recorrido funcional con datos reales locales en Windows 11 están completos. Scout Finance queda cerrado como producto local de investigación. No se autoriza despliegue público, broker ni trading.

## Evidencia automatizada

- Contrato de producto y lenguaje experimental: `PASS`.
- Repositorio fail-closed: `PASS`.
- Censo: 50 activos únicos; 41 JPX principales, 7 TWSE parciales, 2 revisión requerida.
- P020/P178 excluidos de posición automática: `PASS`.
- TWSE excluido del ranking principal: `PASS`.
- Modo agregado sin datos sintéticos: `PASS`.
- Modo local completo simulado por contrato: `PASS`.
- Watchlists atómicas, privadas y sin campos de trading: `PASS`.
- Informes con aviso y manifiesto: `PASS`.
- Suite completa de fase 7 heredada: `PASS`.
- Secretos, red y broker: `PASS`.

## Validación visual en el equipo canónico

- Arranque de Streamlit en Windows 11: `PASS`.
- Lectura del detalle local licenciado de precios, fundamentales y scoring: `PASS`.
- Inicio, universo, ranking, ficha, comparador, watchlist, informes y metodología/ayuda: `PASS`.
- Estados JPX, TWSE, P020 y P178 representados sin ocultar limitaciones: `PASS`.
- Comparador corregido a barras agrupadas y presentación localizada: `PASS`.
- Watchlist creada, persistida, editada y exportable: `PASS`.
- Informes con trazabilidad y aviso obligatorio: `PASS`.
- Las seis salidas locales protegidas permanecen fuera del alcance del cierre: `PASS`.

## Alcance del cierre

La fase 8 se cierra exclusivamente como producto local. La fase 7 permanece `INSUFFICIENT_EVIDENCE`; cerrar la interfaz no valida el scoring ni demuestra capacidad predictiva.

`public_deployment_authorized: false`
`broker_integration_authorized: false`
`automated_trading_authorized: false`
