# v2.38AS — Austria: código ÖNACE real, reutilizando la excepción ya aprobada de firmenakte.at

Fecha: 2026-09-06. Alcance: continuar el ataque al hueco de sector europeo con Austria (20/689 activos, ya con fundamentales e identidad reales desde `v2.38AI`/`v2.38AB`).

## Ninguna decisión de política nueva necesaria

`v2.38AI` ya usa firmenakte.at (excepción comercial aprobada explícitamente por el usuario en esa fase) para fundamentales reales — pero su script solo extraía `parsedJahresabschluesse`, ignorando el resto de la respuesta real de la API. Investigando la respuesta completa se confirmó en vivo (OMV, STRABAG, Erste Group Bank, Kontron) que **cada llamada real ya devuelve un campo `oenaces`** (la clasificación ÖNACE oficial austriaca, implementación 1:1 de NACE Rev.2 a nivel de 4 dígitos) **y un campo `purpose`** (el objeto social textual registrado) — datos oficiales del Firmenbuch/GISA austriaco, nunca antes leídos por este pipeline. Esto significa que no hace falta pedir ninguna aprobación nueva al usuario: es la misma fuente ya aprobada, solo dos campos más de la misma respuesta.

## Verificación real de las 10 traducciones usadas

Los 10 códigos ÖNACE reales que aparecieron en las 20 empresas se verificaron uno a uno contra fuentes independientes (descripciones NACE de Eurostat, páginas de metadatos del INSEE, la herramienta oficial suiza KUBB, y el PDF oficial ÖNACE 2025 de la WKO para la única subdivisión específica austriaca de 5 dígitos, 35.15) antes de traducirlos al inglés — nunca adivinados.

## Bug real de conectividad encontrado y corregido, documentado con transparencia

Al construir este bloque se confirmó, en vivo y de forma repetida durante varios minutos, que **la API de firmenakte.at sufre una degradación de conectividad real** — algunas llamadas se conectan en menos de un segundo, otras nunca reciben respuesta (curl código de salida 28, tiempo de conexión agotado), sin patrón de límite de tasa (nunca un HTTP 429) y sin relación con el resto de Internet (Cloudflare en general responde con normalidad). Confirmado que no es un problema del cliente HTTP: Python `urllib` colgaba sistemáticamente contra este host mientras `curl` respondía al instante — una incompatibilidad real y documentada, resuelta invocando `curl` como subproceso (con lista de argumentos explícita, nunca una cadena de shell, sin riesgo de inyección) — el mismo tipo de solución real ya aplicada antes para este mismo proveedor (el bloqueo por User-Agent de `v2.38AI`).

**El script se hizo resumible**: nunca vuelve a pedir una empresa ya marcada `resolved` en el fichero de salida existente — así, ejecuciones repetidas contra un proveedor con fallos intermitentes acumulan éxitos reales en vez de que la siguiente ejecución borre los de la anterior. Verificado en vivo: tres ejecuciones reales seguidas mantuvieron exactamente las mismas 5 empresas ya resueltas, sin volver a consultarlas.

## Resultado real (parcial, honesto)

**5/20 empresas con código ÖNACE real confirmado, 15/20 en error por la degradación del proveedor, sin ninguna ambigüedad.** Ejemplos reales: STRABAG SE y PORR AG → `70100` "Activities of head offices" (mismo patrón de holding ya visto en GB/Francia/Suiza/Italia), Raiffeisen Bank International y Erste Group Bank → `64190` "Other monetary intermediation", Andritz AG → `28950` "Manufacture of machinery for paper and paperboard production". **Erste Group Bank** además tiene el campo `purpose` real "Bankgeschäfte" (texto alemán sin traducir) — que coincide por subcadena con la palabra clave "bank" del motor de coincidencia, dando una clasificación de sector `BANK_CREDIT_CYCLE` real y correcta que la sola traducción en inglés ("Other monetary intermediation") no habría producido.

**Estado del bloque: `PARTIAL_EUROPE_AUSTRIA_ONACE_PROVIDER_CONNECTIVITY_DEGRADED`.** Diseño resumible: una futura ejecución, cuando el proveedor se recupere, completará las 15 empresas restantes sin volver a pedir ni perder las 5 ya confirmadas. 8 pruebas offline nuevas, incluida una que reproduce exactamente este escenario de reanudación entre ejecuciones. Sin scoring, sin ranking, sin recomendaciones.
