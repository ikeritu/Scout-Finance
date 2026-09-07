# v2.38BL — Reino Unido: investigación de fuente de fundamentales, dos vías reales investigadas, ninguna automatizable con seguridad (real, sin script)

Fecha: 2026-09-08. Alcance: continuar el frente Reino Unido/EE. UU. tras cerrar EE. UU. (`v2.38BI`/`BJ`/`BK`, 538 empresas con fundamentales reales). Las 791 candidatas GB de `v2.38BC` ya tienen identidad real resuelta (GLEIF, más los 40 originales de `v2.38AB` con SIC codes reales de `v2.38AN`) — el hueco aquí, a diferencia de EE. UU., nunca fue de identidad. Es de fuente: ¿existe un equivalente gratuito al `companyfacts.json` de la SEC para estados financieros estructurados de empresas cotizadas del Reino Unido?

## Vía 1: Companies House (API + producto de datos masivos de cuentas) — confirmado real, pero PDF, no iXBRL, para las grandes cotizadas

Companies House sí publica un "Free Accounts Data Product" real y gratuito (ficheros ZIP mensuales, sin cuenta ni clave, desde 2008) que contiene iXBRL/XBRL de las cuentas presentadas electrónicamente — pero su propia documentación oficial confirma que esto cubre **solo el 60-75% de las presentaciones anuales**, el resto en PDF/papel.

**Prueba real en vivo, antes de descartar la vía**: usando la credencial ya provista `SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY` (ya aprobada y en uso desde `v2.38AN`/`v2.38V`/`v2.38Y`), se consultó el histórico de presentaciones (`filing-history?category=accounts`) y los metadatos del documento más reciente de 4 empresas reales, grandes y ya conocidas de este proyecto (identidad ya resuelta desde `v2.38AB`):

| Empresa | N.º de empresa | Fecha de la última presentación | Formato real disponible |
|---|---|---|---|
| Diageo plc | 00023307 | 2025-11-15 | `application/pdf` (236 páginas, 15 MB) |
| BAE Systems plc | 01470151 | 2026-06-26 | `application/pdf` |
| Pearson plc | 00053723 | 2026-05-14 | `application/pdf` |
| Imperial Brands plc | 03236483 | 2026-02-07 | `application/pdf` |

**4/4 confirmado: solo PDF, ningún recurso iXBRL/XBRL disponible.** Esto no es una casualidad de la muestra — explica exactamente el hueco documentado del 25-40% de presentaciones no electrónicas: está concentrado precisamente en las grandes cotizadas auditadas, no en la cola larga de pymes. Las grandes PLC suelen depositar en Companies House la copia estatutaria de sus cuentas ya auditadas como PDF de su informe anual completo, mientras que el requisito de iXBRL nació ligado a la presentación conjunta del Impuesto de Sociedades ante HMRC (dirigido sobre todo a pymes), no a la copia depositada en el registro mercantil. Mismo patrón de fondo ya visto con Finlandia (`v2.38BH`: el sistema XBRL de PRH solo cubre pymes, 0/7 grandes cotizadas) — pero aquí ni siquiera existe un sistema paralelo de gran capitalización: simplemente no se presenta en formato estructurado.

## Vía 2: FCA National Storage Mechanism (NSM) — fuente real y prometedora en principio, pero sin API pública y con una medida activa contra el acceso automatizado

Investigación real (no solo documental): desde 2021, las cotizadas del Reino Unido están obligadas por las normas de transparencia de la FCA (DTR 4.1.14) a presentar su Informe Financiero Anual etiquetado en iXBRL bajo el estándar ESEF — exactamente la población que interesa a este proyecto (grandes cotizadas, no pymes). Estos informes se publican de forma gratuita, sin cuenta, en el National Storage Mechanism (`data.fca.org.uk`), buscable por nombre de empresa, con opciones de descarga que desde una actualización reciente de la plataforma incluyen JSON y CSV además del formato original.

**Prueba real en vivo**: se abrió la interfaz de búsqueda del NSM (gratuita, sin login) y se confirmó que el formulario de búsqueda por nombre de organización es real y funcional. Pero, al inspeccionar el código fuente JavaScript de la propia aplicación en busca del endpoint real de búsqueda (para poder automatizarlo), se encontró una constante `honey_pot_url` real, expuesta en el bundle de configuración de la aplicación — un endpoint señuelo deliberadamente sembrado en el código para detectar acceso automatizado no autorizado a su backend real.

**Esto se trata como una señal de parada, no como un rompecabezas a resolver** — la misma disciplina ya aplicada en este proyecto ante cualquier medida anti-automatización real (el CAPTCHA de InfoCamere en Italia, el bloqueo de acceso automatizado de bvc.com.co en Colombia): no se intenta identificar el endpoint real detrás del señuelo, no se hace scraping del HTML renderizado, y no se construye ningún script contra este servicio.

## Conclusión

**Los datos existen y son gratuitos para un humano** — el NSM aloja informes financieros anuales reales, estructurados en iXBRL/ESEF, de exactamente la población de grandes cotizadas del Reino Unido que interesa a este proyecto. Pero no hay ninguna vía confirmada para obtenerlos de forma automatizada y segura a la escala de 791 empresas: Companies House (la única vía con API pública real) solo tiene PDF para las grandes cotizadas, y el NSM (la única vía con el dato estructurado correcto) activamente desincentiva el acceso programático.

Esto deja al Reino Unido en una categoría real y distinta de las ya vistas: ni el "dato no es público en absoluto" de Alemania (`v2.38AP`), ni el "cuota agotada" de Austria (`v2.38BG`), ni el "cubre solo pymes" de Finlandia (`v2.38BH`) — aquí el dato correcto SÍ es público y gratuito, pero solo de forma manual, empresa por empresa, vía la interfaz web del NSM. Descargar manualmente 791 informes no es una tarea que este pipeline deba automatizar sorteando una medida anti-bot activa.

## Seguridad y alcance

- Red real usada: consulta de la API ya aprobada de Companies House (misma credencial ya en uso, 8 llamadas reales: 4 `filing-history` + 4 `document-metadata`), y navegación real de la interfaz pública del NSM (sin scraping, sin bypass del honeypot, sin descarga de ningún documento).
- Ninguna cuenta nueva creada, ninguna credencial nueva usada.
- Sin rodeo de ninguna medida de anti-automatización.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.
- No se modifica `v2.38AL` — nada nuevo que conectar, ya que no se obtuvo ningún dato real de fundamentales.

**Estado del bloque: `COMPLETED_EUROPE_UK_FUNDAMENTALS_SOURCE_RESEARCH_NO_SAFE_AUTOMATED_SOURCE_FOUND`.** Hallazgo real y honesto: el dato correcto existe y es gratuito, pero no hay una vía automatizable con seguridad a la escala de este proyecto. La identidad real de las 791 candidatas GB (GLEIF + los 40 originales con SIC de Companies House) permanece intacta y sin cambios — solo la extracción de fundamentales queda cerrada por ahora.
