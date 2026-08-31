# Scout Finance v2.33N — licencia de J-Quants y alcance de ampliación (Bloque C)

Fecha: 2026-08-31. Alcance: **investigación documental (C1, C2) + bloqueo formal de la ampliación real (C3)**, sin descargar ningún precio nuevo, sin crear cuenta nueva (la cuenta ya existe desde v2.33G), sin gastar dinero.

Universo afectado: JPX, 3.701 candidatos elegibles (17,49 % del universo, v2.33L). Piloto ya validado: 42/42 símbolos (v2.33G).

## C1 — Licencia y uso, confirmado mediante documentación oficial

Fuente: página de ayuda oficial de J-Quants, "Purpose of use and use of data" (`jpx-jquants.com/en/help/usage`). Citas textuales:

- **Uso privado, permitido:** "Private use refers to utilizing this data for one's own investment analysis, portfolio management, etc." — coincide exactamente con el uso actual de Scout Finance (herramienta de investigación personal, según su propio `README.md`).
- **Publicar resultados de análisis, permitido:** "sharing analysis results (charts, graphs, reports, etc.) is permitted" — pero **compartir los datos brutos directamente está prohibido** ("distributing or sharing the data itself in a viewable form" es la prohibición ya citada en v2.33G).
- **Distribución recurrente a terceros, prohibida:** "Providing or distributing the results of investment analysis conducted using this data to third parties on a recurring basis does not qualify as private use." — **límite explícito**: si Scout Finance alguna vez pasara a compartir análisis de forma recurrente con terceros (otros usuarios, un servicio, etc.), dejaría de encajar en "uso privado".
- **Uso corporativo, prohibido:** "Even for internal-only, non-profit purposes, corporations cannot use J-Quants API." — no aplica a Scout Finance (proyecto personal, no una corporación).
- **Retención tras cancelación:** al terminar la suscripción, hay que "delete all data you acquired up to that point, together with any copies and any derivatives from which the original data can be reconstructed" — política de retención real y documentada, a respetar si en algún momento se cancela la cuenta.
- **Almacenamiento en la nube, permitido con condiciones:** solo si "the data can be viewed only by you" y existen controles de acceso adecuados — no aplica todavía (los datos de Scout Finance están en local, no en la nube).

**Conclusión de C1:** la licencia de J-Quants **sí es compatible** con el uso actual y previsto de Scout Finance (investigación privada, sin compartir datos brutos ni proveer análisis a terceros de forma recurrente), siempre que el proyecto se mantenga en ese uso privado. No se requiere ninguna acción adicional del usuario para confirmar esto por escrito de forma independiente: la documentación oficial pública ya responde la pregunta de forma directa y citable.

## C2 — Suficiencia analítica frente a la ventana real (2 años, retraso de 12 semanas)

Comparación directa, sin rebajar los requisitos de v2.33C en silencio:

| Indicador | Ventana necesaria típica | ¿Válido con 2 años (486 sesiones máx.)? |
|---|---|---|
| Retorno anualizado a 1 año | ~252 sesiones | **Sí**, sobra margen. |
| Medias móviles cortas (20/50 sesiones) | 20–50 sesiones | **Sí**. |
| Media móvil larga (200 sesiones) | 200 sesiones | **Sí**, cabe holgadamente. |
| Momentum clásico (12 meses, o 12-1 meses) | ~252 sesiones | **Sí**. |
| Volatilidad (ventanas de 30/90/252 sesiones) | hasta 252 sesiones | **Sí**. |
| Drawdown máximo dentro de la ventana disponible | variable | **Parcialmente válido**: mide el drawdown de los últimos ~2 años, pero **no** el drawdown histórico real de la empresa (una caída fuerte de hace 5–10 años quedaría invisible). |
| Estabilidad multi-año / multi-ciclo económico | varios años, idealmente varios ciclos | **No válido**: 2 años no garantizan cubrir ni siquiera un ciclo completo. |
| CAGR / retorno anualizado a 3–5 años | 3–5 años | **No válido**: profundidad insuficiente. |

Además, el **retraso de 12 semanas** es una limitación distinta de la profundidad: cualquier indicador de "momentum reciente" (últimas 4–8 semanas) **no puede calcularse con datos verdaderamente actuales** — el dato más reciente disponible siempre tiene como mínimo ~3 meses de antigüedad. Esto no se puede compensar con más profundidad; es una limitación de actualidad, no de historia.

**Conclusión de C2:** J-Quants (plan gratuito) es suficiente para indicadores de corto y medio plazo (hasta ~1 año) calculados sobre datos con 3 meses de retraso, pero **no** es suficiente para análisis de estabilidad multi-ciclo ni para CAGR a varios años. Cualquier futuro cálculo de estos últimos debe quedar explícitamente bloqueado o marcado como no disponible para activos JPX, no aproximado con menos datos de los necesarios.

## C3 — Ampliación controlada: bloqueada, requiere autorización explícita

El universo JPX elegible completo es de **3.701 candidatos** (censo v2.33L), muy por encima de los 42 ya validados y muy por encima del umbral de 500 activos que exige autorización explícita según la sección 7 del encargo.

**No se ha lanzado ninguna descarga masiva.** Estimación previa a cualquier ejecución, para que el usuario pueda decidir con datos:

- Con el mismo ritmo usado en v2.33G (resolución + descarga, ~15 s entre llamadas, con reintento automático ante 429): resolver y descargar 3.701 activos tomaría del orden de **3.701 × 2 llamadas × 15 s ≈ 30,8 horas** de ejecución acumulada (frente a los ~20 minutos que tomaron los 42 activos del piloto). Esto no es una única sesión de trabajo; requeriría ejecutarse en segundo plano a lo largo de varios días, con reanudación entre sesiones.
- No se ha estimado un límite de llamadas diario/mensual documentado por J-Quants para el plan gratuito más allá del límite de 5 solicitudes/minuto ya conocido; una ejecución de esta escala **debería confirmarse que no infringe ningún límite adicional no documentado** antes de lanzarse.
- El propio maestro `/v2/equities/master` permitiría detectar acciones retiradas, cambios de código y duplicados antes de descargar precios, igual que se hizo para los 42 símbolos del piloto — esto sí sería parte del trabajo, no un paso nuevo.

**Esto queda pendiente de autorización explícita del usuario antes de ejecutarse.**

## C4 — Decisión JPX

**Parcial: operativo con restricciones, no ampliado.**

- Licencia: **confirmada compatible** con el uso actual (C1).
- Indicadores: **válidos para corto/medio plazo, no válidos para estabilidad multi-ciclo ni CAGR a varios años** (C2), con retraso de 12 semanas siempre presente.
- Alcance: sigue acotado a los 42 símbolos ya validados en v2.33G (17,49 % del universo JPX elegible; 1,13 % del universo elegible total de 21.165). La ampliación a los 3.701 candidatos completos **requiere autorización explícita del usuario** por superar el umbral de 500 activos — no se ha solicitado consentimiento implícito, no se ha ejecutado nada.

No se autoriza ninguna descarga masiva, scoring, ranking, ni el inicio de la fase 5.

## Seguridad y alcance

- No se ha creado ninguna cuenta nueva (la de v2.33G ya existe).
- No se ha usado la clave de J-Quants en este bloque (C1/C2 son investigación documental; C3 no se ejecuta).
- No se ha descargado ningún precio nuevo.
- `production_scoring_authorized: false`, `allow_ranking: false`.

## Estado del roadmap

- No cambia el estado de v2.33G.
- Bloque C: licencia confirmada (C1), suficiencia analítica evaluada (C2), ampliación bloqueada pendiente de autorización (C3).
- Siguiente paso: si el usuario autoriza la ampliación, definir un piloto intermedio (por ejemplo, unos cientos de activos) antes de los 3.701 completos, para no comprometer ~31 horas de ejecución de una sola vez sin una validación intermedia.
