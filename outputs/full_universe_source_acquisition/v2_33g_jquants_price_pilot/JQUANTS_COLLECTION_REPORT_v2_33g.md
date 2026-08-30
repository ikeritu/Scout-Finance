# Scout Finance v2.33G — informe agregado del piloto real de precios J-Quants (JPX)

Activos esperados: **42** · Activos válidos: **42** · Errores de esquema: **0**.

- Observaciones numéricas válidas: 20228
- Sesiones por activo — mínimo: 368, máximo: 486, mediana: 486.0, media: 481.62, P10: 486, P25: 486, P75: 486, P90: 486.
- Ventana confirmada por el propio proveedor (plan gratuito): 2024-06-08 → 2026-06-08 (730 días naturales, ~490 sesiones estimadas).
- Fecha mínima observada global: 2024-06-10. Fecha máxima observada global: 2026-06-08.
- Cobertura de la mediana de sesiones frente a la ventana confirmada: **99.18%**.

## Activos con menos de 300 sesiones

Ninguno.

## Clasificación de la evidencia

### Hechos observados
- El propio J-Quants confirmó la ventana exacta del plan gratuito mediante un mensaje de error HTTP 400 al solicitar un rango mayor: '2024-06-08 ~ 2026-06-08'.
- 41/42 activos tienen el máximo de 486 sesiones cubriendo toda la ventana confirmada; 1 activo ('277A' / Globe-ing Inc., pilot P148) tiene solo 368 sesiones, empezando el 2024-11-29, más tarde que el resto.
- El límite de tasa documentado del plan gratuito (5 peticiones/minuto) produjo errores HTTP 429 reales en la práctica al ritmo documentado; un reintento con espera de 65 segundos resolvió todas las ocurrencias sin intervención manual ni pérdida de datos en la ejecución final.
- 2 activos registraron filas de calendario sin operación (OHLC nulo) (66 filas en total): el activo P182 (HOKURIKU GAS CO.,LTD., ticker 9537) tiene 64 días sin operación en toda la ventana, coherente con una acción regional poco líquida; P154 tiene 2.

### Limitaciones no confirmadas
- Por qué el activo P148 (Globe-ing Inc.) tiene una fecha de inicio posterior a los otros 41 activos no está confirmado aquí; una cotización reciente es la explicación más probable, pero no se ha verificado contra ninguna fuente externa de fecha de salida a bolsa.

## Seguridad

- No se detectaron credenciales ni URLs con clave en los archivos brutos.
- Scoring y ranking productivo: **no autorizados**.
- Este informe no reproduce precios fila a fila ni contenido licenciado.