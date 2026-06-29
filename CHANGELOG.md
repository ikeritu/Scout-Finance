# CHANGELOG

## Sin tag — Simplificación de la interfaz para pruebas

### Cambiado

- `app.py`: login y FAQ deshabilitados (no se llaman desde `main()`, código sin borrar).
- `app.py`: pestañas reducidas de 7 a 4 (Dashboard, Ranking, Análisis empresa, Comparar empresas). Candidatos Stage 3, Histórico/técnico y Ajustes quedan ocultas.
- `app.py`: panel de costes OpenAI en la sidebar movido a un expander colapsado.
- Nuevo `.streamlit/config.toml` con tema visual básico.
- README.md / VERSION.md actualizados: la documentación seguía en v0.4 pero el código y los freezes (`docs/v1/`) ya estaban en v1.1C.

## v1.0 → v1.1C — Freezes intermedios (ver `docs/v1/`)

Entre v0.4 y este punto se añadió, en commits y freezes separados no reflejados antes en este changelog:

- capa de revisión manual documentada (watchlist / reject / needs_more_data) y export pack final;
- freeze candidate v1.0.0 y freeze de documentación (`docs/USER_GUIDE.md`, `docs/SAFETY_LIMITS.md`, `docs/QUICKSTART.md`);
- parche de usabilidad v1.1B;
- freeze final v1.1C MVP.

Detalle completo en `docs/v1/*.md` y `releases/`.

## v0.4 — Versión estable Fase 4H

### Añadido

- Documentación principal actualizada.
- FAQ actualizado dentro de Streamlit.
- `VERSION.md`.
- `CHECKLIST_USO.md`.
- `FAQ_SCOUT_FINANCE.md`.
- Consolidación de versión estable.

### Consolidado

- Dashboard ejecutivo.
- Ranking resumido.
- Análisis empresa con outputs Fase 2.
- Comparativa visual por JSON.
- Avisos por baja confianza/datos insuficientes.
- Histórico por empresa.
- Riesgo interpretado correctamente.
- Gráfico de riesgo separado.
- Ajustes / panel técnico.
- Checker de estabilidad.

### No incluido

- Recomendaciones Buy/Hold/Sell.
- Broker integration.
- Portfolio construction.
- Automatización de inversión.
