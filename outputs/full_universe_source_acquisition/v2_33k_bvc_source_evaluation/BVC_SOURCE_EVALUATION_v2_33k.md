# Scout Finance v2.33K — evaluación de fuentes BVC (Colombia, 1 símbolo)

Fecha: 2026-08-31. Alcance: **investigación técnica directa, sin descarga de datos, sin cuenta, sin gasto, sin intento de sortear ninguna medida antibot**. Afecta a un único símbolo del piloto (`P015`, "AO BANCO DE BOGOTA", código `COB01PAAO006`), así que el impacto de este cierre es marginal para el proyecto en su conjunto.

## Fuente 1: Superintendencia Financiera de Colombia (SFC) — accesible, oficial, pero insuficiente

Se localizó y confirmó en vivo la página oficial de cotización por emisor:

```
https://www.superfinanciera.gov.co/info/superfinancierav8/media/MercadoAccionario/Precios/Diarios/d_cob01paao006.htm
```

El patrón de URL (`d_` + código de la acción en minúsculas + `.htm`) se confirmó funcionando exactamente con nuestro identificador interno `COB01PAAO006`, devolviendo la página titulada "AO BANCO DE BOGOTA - cotización" con el código de acción correcto — confirmación directa de que el identificador ya es válido y no necesita mapeo adicional.

**Sin embargo**, la página no ofrece una serie diaria: para cada periodo (2, 6 o 12 meses, mediante los enlaces `d_cob01paao006.htm`, `_6.htm`, `_12.htm`) solo muestra **tres cifras resumen** — precio promedio ponderado más reciente, máximo del periodo (con su fecha) y mínimo del periodo (con su fecha) — más el patrimonial. No hay tabla fila por fila. Se comprobó explícitamente que la variante de 12 meses devuelve el mismo formato resumen, no una tabla diaria ampliada.

**Conclusión:** fuente oficial, gratuita, confirmada, pero **no apta** para reconstruir un histórico OHLCV real.

## Fuente 2: BVC (bvc.com.co) — probablemente mejor, pero no accesible de forma automatizada aquí

Varias fuentes independientes (La República, un hilo de Rankia, un tutorial en YouTube) coinciden en que el sitio de BVC sí ofrece una herramienta de descarga de histórico de precios "en rangos de hasta seis meses, con histórico de hasta cinco años", en apariencia sin necesidad de licencia.

Al intentar acceder de forma automatizada:

- Una petición HTTP simple devuelve la página (una aplicación Next.js) pero el contenido de mercado se carga vía JavaScript.
- Con un navegador real (sin trucos de evasión, sin simular comportamiento humano) la página se queda cargando indefinidamente en la sección de mercado de acciones, sin llegar a lanzar ninguna llamada de datos observable en la red, mientras otros recursos (CSS, JS, fuentes) sí cargan con normalidad.
- No se ha intentado ningún método para forzar la carga (no se ha imitado interacción humana con el fin de evadir una posible detección de automatización): sería exactamente el tipo de elusión de medidas de protección que este proyecto evita.

**Conclusión:** no se ha podido confirmar ni descartar en esta pasada si BVC realmente ofrece un histórico diario gratuito descargable, porque la herramienta no fue accesible de forma automatizada sin cruzar una línea que este proyecto no cruza. Dado el impacto de un solo símbolo, no se considera justificado insistir con más tiempo o con acceso manual guiado por el usuario.

## Decisión

**`INSUFFICIENT_FOR_DAILY_SERIES`** para la fuente SFC (confirmada pero inútil para históricos), **`UNVERIFIED_AUTOMATION_BLOCKED`** para BVC (probablemente mejor, no verificable aquí sin cruzar líneas de automatización que este proyecto evita). Dado que solo afecta a 1 símbolo del piloto completo, no se recomienda invertir más tiempo salvo que el usuario quiera comprobar manualmente la herramienta de BVC él mismo.

No se ha descargado ningún precio, no se ha creado ninguna cuenta, no se ha gastado dinero, no se ha intentado sortear ninguna protección.

## Estado del roadmap

- No cambia el estado de ningún cierre anterior (v2.33D1 a v2.33J).
- Progreso global: 3/8 fases cerradas, fase 4 en curso.
- Con esto se completa la revisión de los cuatro mercados originalmente bloqueados/limitados: **JPX resuelto (v2.33G)**, **TWSE resuelto (v2.33I)**, **Cboe Europe bloqueado indefinidamente (v2.33H)**, **ASX sin fuente (v2.33J)**, **BVC inconcluso por bajo impacto y bloqueo de automatización (este cierre)**.
- **Descartado explícitamente por el usuario (2026-08-31): no se sigue investigando BVC.** El usuario decidió no comprobar manualmente la herramienta de bvc.com.co ni continuar por ninguna otra vía. BVC (1 símbolo) queda cerrado sin fuente de precios, sin previsión de retomarlo salvo que el usuario lo reabra explícitamente.
