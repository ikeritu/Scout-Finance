# v2.38BR — Jersey: tres vías reales probadas, ninguna accesible con seguridad, cierre honesto sin fundamentales

Fecha: 2026-09-08. Alcance: retomar la investigación real que `v2.38BL` había dejado explícitamente abierta — Jersey (45 empresas, casi todas PLC reales con obligación legal genuina de depositar cuentas auditadas) es distinto de las 6 jurisdicciones offshore ya cerradas por hecho legal (`v2.38BM`): aquí el dato correcto probablemente existe, la pregunta real era si se puede acceder a él con seguridad.

## Tres vías reales probadas en vivo, cada una con un resultado real y distinto

**Vía 1 — petición HTTP directa (ya confirmada en `v2.38BL`)**: una petición directa a la página de ayuda de búsqueda del registro (`jerseyfsc.org/registry/myregistry-help/registry-search-guidance/`) devolvió **403 Forbidden real**, confirmado entonces.

**Vía 2 — navegación real e interactiva con un navegador de verdad (nueva, esta sesión)**: se navegó directamente al sitio principal (`jerseyfsc.org`) y a su enlace público oficial "Search the public register" (encontrado en `myreg.jerseyfsc.org/home`, un enlace real, sin necesidad de cuenta). Ambas rutas devuelven la misma pantalla real: una interstitial activa de verificación anti-bot ("Verificación de seguridad en curso... Este sitio web utiliza un servicio de seguridad para protegerse contra bots maliciosos"), que **no se resolvió sola tras más de 15 segundos de espera real**. Dos subdominios relacionados sí cargan sin problema (`sir.jerseyfsc.org`, el Registro de Garantías Mobiliarias — un servicio distinto, sobre cesión de créditos y garantías, no sobre cuentas de empresas; y `myreg.jerseyfsc.org`, el portal de acceso), lo que confirma que la protección anti-bot está específicamente en el dominio principal donde vive la búsqueda pública de empresas y sus documentos.

**Vía 3 — el propio portal `myRegistry`**: la única forma de superar la interstitial y llegar a la búsqueda real de documentos es a través de `myreg.jerseyfsc.org`, que **exige iniciar sesión o registrarse** para cualquier función, incluida la búsqueda básica.

## Por qué esto se trata como un cierre real, no como un rompecabezas a resolver

Ninguna de las tres vías es compatible con las reglas ya establecidas de este proyecto: no se intenta nunca sortear una medida de verificación anti-bot activa y real (misma disciplina ya aplicada con el CAPTCHA de InfoCamere en Italia y el señuelo activo del NSM del Reino Unido en `v2.38BL`), y no se crea nunca una cuenta de terceros en nombre del usuario (protocolo ya establecido y respetado durante toda esta sesión). Con la petición HTTP directa ya confirmada bloqueada, la navegación interactiva real topando con la misma protección activa, y el único acceso restante exigiendo una cuenta, las tres vías reales están agotadas.

## Conclusión

Jersey queda en una categoría real y distinta de las 6 jurisdicciones offshore ya cerradas: allí el hecho era legal y estructural (nunca exigen divulgación pública); aquí el hecho legal es el contrario (sus PLC sí tienen una obligación real de depositar cuentas auditadas), pero **el acceso a ese dato real está activamente restringido** por el propio registro, no por ausencia del dato. Es la misma categoría de hallazgo que el NSM del Reino Unido en `v2.38BL` — un dato real y gratuito en principio, inaccesible con seguridad en la práctica.

## Qué NO hace este bloque

No se crea ninguna cuenta en `myRegistry`. No se intenta resolver ni sortear la verificación anti-bot del sitio principal. No se modifica la identidad ya resuelta de las 45 empresas de Jersey — sigue intacta. No se construye ningún script, ya que no hay ninguna vía real y seguible que automatizar.

## Seguridad y alcance

Red real usada solo para navegación interactiva de exploración (sin scraping, sin intento de sortear la verificación anti-bot, sin envío de ningún formulario ni credencial). Ninguna cuenta nueva creada. Sin scoring, ranking, recomendaciones ni fase 9C. No se modifica `v2.38AL` — ningún dato real de fundamentales obtenido.

**Estado del bloque: `COMPLETED_EUROPE_JERSEY_REGISTRY_ACCESS_RESEARCH_NO_SAFE_ACCESS_FOUND`.** Cierra la investigación abierta por `v2.38BL` con evidencia real de las tres vías agotadas — Jersey se une a Reino Unido como un caso real de "el dato existe y es gratuito en principio, pero ninguna vía de acceso es segura de automatizar o siquiera de investigar más allá sin crear una cuenta o sortear una medida de seguridad activa."
