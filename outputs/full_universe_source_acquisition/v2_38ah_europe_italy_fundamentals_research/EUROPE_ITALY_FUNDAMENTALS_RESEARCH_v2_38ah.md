# v2.38AH — Italia: investigación de fundamentales (real, sin script nuevo)

Fecha: 2026-09-06. Alcance: investigar si existe alguna vía oficial gratuita **y automatizable sin scraping** para obtener fundamentales reales de las 22 empresas italianas (identidad y registro ya resueltos al 100% vía GLEIF en v2.38AF — autoridad de registro real confirmada, `RA000407` = Registro delle Imprese, ej. Assicurazioni Generali → 00079760328).

## Hallazgo real: los bilanci XBRL son genuinamente gratuitos — pero solo vía interfaz web, sin API documentado

Italia es uno de los países europeos con **mandato de depósito de cuentas anuales en iXBRL más antiguo** (desde ~2009 vía "bilancio XBRL" en el Registro delle Imprese, gestionado por InfoCamere) — en teoría, la vía más prometedora de todo este bloque de investigación de países. **Confirmado: el fichero XBRL del bilancio es descargable gratis, sin coste**, desde el portal oficial `registroimprese.it`.

**Pero el acceso es exclusivamente mediante navegación web interactiva, sin ningún API documentado ni patrón de URL de descarga directa**: el proceso real confirmado es buscar la empresa → abrir su ficha → ir a la sección "Bilanci" → seleccionar el año → pulsar "Bilancio XBRL" para descargar. No existe ningún endpoint público que acepte, por ejemplo, un P.IVA o código fiscal y devuelva el fichero directamente sin una sesión de navegador. Automatizar esta descarga exigiría simular una sesión de navegador interactiva — **scraping, prohibido por la política de este proyecto** — no una llamada a un API real como en GB, Irlanda, Francia o Países Bajos.

## El API real de InfoCamere existe, pero es de pago e institucional

InfoCamere sí ofrece un API REST propio (`accessoallebanchedati.registroimprese.it/abdo/api`) — pero **exige credenciales de identidad digital italiana (SPID/CIE/CNS) más un saldo de crédito Telemaco de pago por consulta**, la misma tarifa que la interfaz web de pago. No es una vía gratuita ni, previsiblemente, accesible para un proyecto de investigación extranjero sin identidad digital italiana — descartado por la política de no usar fuentes de pago, independientemente de la cuestión de accesibilidad.

## Conclusión

**Existe una fuente real y genuinamente gratuita (los bilanci XBRL), pero no existe ninguna vía de acceso automatizado a ella sin scraping.** Esto es distinto de los hallazgos anteriores:
- No es como Alemania (donde la alternativa gratuita real estaba técnicamente muerta).
- No es como Suiza (donde la ley simplemente no exige la publicación).
- Es más parecido al caso de la CNMV española: **el dato correcto y gratuito existe, pero el único acceso es un formulario/interfaz web pensada para humanos, no un API**.

No se construye ningún script de descarga para Italia. La identidad y el registro (22/22, vía GLEIF) ya están cerrados desde v2.38AF y no requieren ningún trabajo adicional.

## Seguridad y alcance

- Red real usada: solo consultas de solo lectura durante la investigación (páginas públicas de documentación y tutoriales, una comprobación de accesibilidad del portal).
- Ninguna cuenta creada, ninguna credencial solicitada ni usada.
- Sin scraping, sin simulación de sesión de navegador.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.

## Resumen frente a las jurisdicciones ya tratadas

| | GB | Irlanda | Francia | Países Bajos | Suiza | **Italia** |
|---|---:|---:|---:|---:|---:|---:|
| Activos | 40 | 17 | 53 | 44 | 29 | **22** |
| Identidad/registro resuelto | 29/40 | 8/17 | 18/53 | 36/44 | 29/29 (GLEIF) | **22/22 (GLEIF, ya cerrado)** |
| Fundamentales reales accesibles | Sí (2 empresas) | No | No | No | No (causa legal) | **No — dato gratuito real, pero solo accesible vía interfaz web, no API** |

**Estado del bloque: `COMPLETED_EUROPE_ITALY_FUNDAMENTALS_RESEARCH_FREE_DATA_NO_API_ACCESS`.** Hallazgo distinto de los anteriores: el bloqueo no es de coste ni de disponibilidad legal, sino de **forma de acceso** — datos reales y gratuitos que exigirían scraping para automatizar, algo que este proyecto no hace.
