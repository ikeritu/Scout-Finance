# Scout Finance v2.33M — evaluación de fuentes gratuitas para EE. UU. (Bloque B)

Fecha: 2026-08-31. Alcance: **investigación documental**. No se ha creado ninguna cuenta, no se ha usado ninguna clave, no se ha gastado dinero. Este bloque **queda bloqueado en el paso B2** (creación de cuenta), tal como exige la sección 2 de la skill de este proyecto y la regla 8 del encargo: nunca se crea una cuenta en nombre del usuario.

Universo afectado: NASDAQ (3.016), NYSE (1.761), NYSE American (233) y Cboe BZX (1) — **5.011 candidatos elegibles, el 23,67 % del universo de 21.165** (ver `v2.33L`).

## B1 — Evaluación de fuentes

### Twelve Data (plan gratuito) — única candidata viable identificada

Ya confirmado en v2.33E que el plan Basic de Twelve Data cubre "real-time US equities and ETFs" de forma gratuita — a diferencia del resto de mercados internacionales, que están bloqueados detrás de planes de pago. Esta pasada profundiza específicamente en el ángulo estadounidense:

- **Límites de tasa:** 8 créditos/minuto, 800/día (confirmado, v2.33E).
- **Ajuste por splits/dividendos:** el endpoint `time_series` documenta un parámetro `adjust` con modos `all`, `splits`, `dividendos`, `none`, con `splits` como valor por defecto — indicio favorable de que sí hay ajuste disponible, pero **no se ha confirmado en una llamada real** si este parámetro funciona igual en el plan gratuito o si el campo de salida coincide con el resto del contrato de este proyecto (`adjusted_close`).
- **Profundidad histórica para EE. UU. en el plan Basic:** **no documentada de forma explícita** en ninguna página oficial revisada. Ni la documentación de la API ni la página de precios especifican un límite de años para el plan gratuito.
- **Licencia:** prohíbe expresamente uso comercial (compatible con Scout Finance, que es personal). Prohíbe "almacenar o cachear datos más allá de los plazos permitidos especificados en la Documentación" — **no se ha localizado esa Documentación específica con el plazo exacto**, pese a buscarla directamente. Redistribución restringida salvo add-on de pago (irrelevante aquí, no se redistribuye).
- **Cuenta:** el plan gratuito requiere registro. **No se ha creado ninguna cuenta.**

### Stooq — descartada

Stooq ofrece descargas CSV gratuitas de precios históricos de EE. UU. sin registro aparente, pero:

- No se ha localizado ninguna página de términos de uso ni licencia (dos rutas probadas, `regulamin.html` y `rules.html`, devuelven HTTP 404).
- Fuentes de la comunidad describen sus endpoints de datos como "APIs no documentadas" ("undocumented API endpoints").
- Esto incumple directamente las reglas 7 y 11 del encargo (nada de endpoints no documentados como base productiva; licencia/retención deben estar documentadas). **Se descarta sin más pruebas técnicas**, independientemente de que el endpoint funcione (`stooq.com/q/d/l/?s=aapl.us&i=d` responde HTTP 200): funcionar no es lo mismo que estar autorizado.

### Alpha Vantage — no reevaluada

Ya descartada en v2.33C como fuente principal (25 solicitudes/día en el nivel gratuito, inviable a la escala de 5.011 candidatos). No ha surgido evidencia nueva que cambie esa conclusión; no se reabre la investigación.

### SEC EDGAR — fuera de alcance para precios

EDGAR (ya aprobado en v2.33C para fundamentales) no distribuye precios de mercado, solo información de presentaciones regulatorias. No aplica a este bloque.

## B2 — Gate previo a cuenta

**Bloqueado aquí.** Para continuar el Bloque B se necesita que el usuario:

1. Cree una cuenta gratuita en [twelvedata.com](https://twelvedata.com) (plan Basic, sin coste, sin tarjeta según la documentación revisada — a confirmar por el propio usuario al registrarse).
2. Guarde la clave API como variable de entorno de usuario en Windows, por ejemplo `SCOUT_FINANCE_TWELVEDATA_API_KEY`, sin compartirla nunca en el chat.
3. Confirme que ha leído y acepta los términos de uso del plan gratuito citados arriba (uso no comercial, límite de caché no localizado con exactitud).

**Condiciones y riesgos de continuar con Twelve Data:**
- No hay garantía de que la profundidad histórica real (una vez probada) sea suficiente para los indicadores previstos (momentum, volatilidad, drawdown) — esto solo se puede confirmar con una sonda mínima real, como se hizo con J-Quants y TWSE.
- El límite exacto de retención en caché no está confirmado; un piloto real debería tratarlo como pendiente de aclaración escrita, igual que la licencia de J-Quants (v2.33N).
- Alternativa si el usuario prefiere no crear esta cuenta: dejar el bloque EE. UU. como `BLOCKED_USER_ACTION_REQUIRED` de forma indefinida, sin otra fuente gratuita conocida y documentada para este subconjunto.

**No se ha asumido consentimiento.** Los bloques independientes (E, y el resto de A) continúan sin esperar esta decisión.

## Decisión

**`BLOCKED_USER_ACTION_REQUIRED`** — no `NO_FREE_SOURCE_FOUND`, porque sí existe una candidata plausible (Twelve Data), pero no se puede avanzar sin que el usuario cree la cuenta él mismo.

No se autoriza ninguna descarga, scoring, ranking, ni el inicio de la fase 5.

## Seguridad y alcance

- No se ha creado ninguna cuenta, no se ha usado ninguna clave, no se ha gastado dinero.
- No se ha descargado ningún precio.
- `production_scoring_authorized: false`, `allow_ranking: false`.

## Estado del roadmap

- No cambia el estado de ningún cierre anterior.
- Bloque EE. UU. (23,67 % del universo elegible) queda `BLOCKED_USER_ACTION_REQUIRED` hasta que el usuario decida crear la cuenta de Twelve Data o indique una alternativa.
- Los Bloques C, D, E, F continúan de forma independiente mientras tanto.
