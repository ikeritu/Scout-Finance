# Scout Finance v2.37H — gate de fase 8

## Decisión provisional

`IMPLEMENTED_AWAITING_WINDOWS_UI_VALIDATION`

La implementación y la QA offline están completas, pero la fase 8 no se declara cerrada hasta ejecutar el producto en Windows con los datos reales locales y completar el checklist visual. No se autoriza despliegue público, broker ni trading.

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

## Validación pendiente en el equipo canónico

- Arranque de Streamlit en Windows 11.
- Lectura del detalle local licenciado de precios, fundamentales y scoring.
- Recorrido visual de las ocho pantallas.
- Accesibilidad básica por teclado y ancho móvil.
- Confirmación de que ninguna de las seis salidas locales protegidas ha sido tocada.

## Regla de cierre

Solo tras esos controles podrá cambiarse la decisión a `COMPLETED_LOCAL_PRODUCT` y crearse el tag final. La fase 7 permanece `INSUFFICIENT_EVIDENCE`; cerrar la interfaz no valida el scoring.

`public_deployment_authorized: false`
`broker_integration_authorized: false`
`automated_trading_authorized: false`
