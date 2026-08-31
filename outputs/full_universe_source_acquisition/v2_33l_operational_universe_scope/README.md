# v2.33L — auditoría, inventario y alcance del universo operativo (Bloque A, fase 4)

Estado: **`COMPLETED_SCOPED_OPERATIONAL_UNIVERSE`** (para el bloque de alcance). El proyecto adopta un MVP multifuente de alcance limitado, no cobertura mundial gratuita.

## Resultado

- Auditoría inicial: repo limpio, `main` alineada con `origin/main`, commit base confirmado, sin secretos, sin archivos protegidos tocados.
- **Hallazgo clave:** Cboe Europe representa el **49,53 %** de los 21.165 candidatos elegibles del censo canónico — no una fracción menor. Ya bloqueado indefinidamente desde v2.33H.
- Clasificación completa de los 9 mercados con candidatos elegibles + 2 mercados retenidos por corrupción de esquema (Xetra, SGX).
- Techo teórico de cobertura si JPX/TWSE se amplían y EE. UU. se resuelve: ~44,45 % de los 21.165 candidatos actuales — un techo, no una cifra ya alcanzada.
- Sesgo geográfico documentado explícitamente: el universo operativo previsible se concentra en EE. UU., Japón y Taiwán.

## Archivos

- `scripts/build_market_universe_inventory_v2_33l.py`: genera el inventario reproducible desde el censo canónico completo (21.165 candidatos), no desde la muestra de 240.
- `tests/qa_market_universe_inventory_v2_33l.py`: QA de reproducibilidad del inventario.
- `market_universe_inventory_v2_33l.csv` / `market_universe_inventory_report_v2_33l.json`: inventario agregado.
- `OPERATIONAL_UNIVERSE_SCOPE_v2_33l.md`: auditoría, inventario, clasificación y decisión de alcance completas.
