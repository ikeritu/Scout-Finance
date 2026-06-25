# v1.3A — Visual UI Redesign

## Objetivo

Aceptar el nuevo diseño visual de Scout Finance como base de interfaz, manteniendo la alineación funcional introducida en v1.2A.

## Cambios incluidos

- Tema visual profesional basado en CSS global.
- Sidebar más limpio.
- Tarjetas, métricas, botones, tabs, tablas y expanders con estilo unificado.
- Configuración visual en `.streamlit/config.toml`.
- Mantiene helpers v1.2A de fallback al funnel revalidado.
- Corrige `Ranking` para que use `_get_latest_final_view_df()` y no vuelva a quedarse vacío cuando existe funnel revalidado.
- Mantiene aviso en `Comparar empresas` cuando los JSON son históricos/de ejemplo y no coinciden con el ranking actual.

## No toca

- Scoring
- Filtros financieros
- Pipeline
- OpenAI
- APIs externas
- yfinance
- Broker/trading
- Lógica financiera

## Validación

```powershell
.\.venv\Scripts\python.exe scripts/check_v1_3a_visual_ui_redesign.py
```

## Prueba manual recomendada

1. Arrancar interfaz.
2. Revisar Dashboard con tarjetas principales.
3. Abrir Ranking y confirmar que aparecen AUPH/BZ/ADBE o candidatas revalidadas.
4. Abrir Análisis empresa y confirmar que carga AUPH/BZ/ADBE.
5. Abrir Comparar empresas y confirmar que muestra aviso si aparecen AAPL/LLY/AMD.
6. Descargar CSV desde Dashboard/Ranking.
7. Confirmar que no aparece el funnel duplicado debajo de todas las pestañas.

## Nota

Este parche empaqueta el rediseño visual, pero también evita una regresión: el `Ranking` no debe volver a depender solo de la vista final vacía del último run.
