# v2.38AO — Francia: códigos NAF/NACE reales vía la misma API gubernamental ya validada

Fecha: 2026-09-06. Alcance: continuar el ataque al hallazgo de `v2.38AM` (0/689 empresas europeas con coincidencia real de sector) con Francia, reutilizando `recherche-entreprises.api.gouv.fr` (ya validada en `v2.38AD`, gratuita, sin clave, sin cuenta).

## Qué se añade

`v2.38AD` nunca capturó clasificación de actividad porque estaba fuera de su alcance. Confirmado en vivo que la misma API, consultada por SIREN, devuelve `activite_principale` (código NAF Rev.2, p. ej. "70.10Z") y `section_activite_principale` (letra de sección NACE, p. ej. "M") para la empresa exacta. Este script consulta las 18 empresas francesas ya resueltas por `v2.38AD`, emparejando **estrictamente por SIREN** (nunca el primer resultado de una búsqueda de texto libre) para evitar un falso positivo.

## Verificación real, no adivinada

Los 9 códigos NAF y las 6 secciones NACE reales que aparecieron se verificaron uno a uno contra las páginas oficiales de metadatos del INSEE (`insee.fr/fr/metadonnees/nafr2/...`) antes de traducirlos al inglés (para alimentar el mismo motor de coincidencia por palabra clave ya usado con EE. UU./GB). El texto en francés original nunca se descarta silenciosamente — cada código queda trazable a su fuente oficial.

## Resultado real

**18/18 empresas con código NAF real, 0 errores, 0 códigos sin verificar.** Ejemplos reales: ENGIE → `35.23Z` "Trade in gaseous fuel via pipelines", Soitec → `26.11Z` "Manufacture of electronic components", Innate Pharma y Abivax → `72.11Z` "Research and development in biotechnology".

## Mismo hallazgo honesto que en Reino Unido y Austria

**9 de las 18 empresas** (Sanofi, Danone, Pernod Ricard, Forvia, Thales, Kering, Capgemini, Vivendi, Alstom) muestran `70.10Z` "Head office activities" — el SIREN consultado es, de nuevo, la entidad matriz/holding registrada, no la operación real. Es el mismo patrón exacto ya confirmado en `v2.38AI` (Austria) y `v2.38AN` (Reino Unido): el registro oficial refleja la estructura jurídica de la matriz, una limitación estructural del dato, no un fallo de este script.

## Salvaguardas

Bloqueado por defecto; requiere `--execute` (sin credencial, misma convención que `v2.38AD`). 6 pruebas offline nuevas, incluida una que confirma el emparejamiento estricto por SIREN (nunca adivinar con el primer resultado). Sin scoring, sin ranking, sin recomendaciones.

**Estado del bloque: `COMPLETED_EUROPE_FRANCE_SECTOR_CODES`.** Alimenta directamente la reconstrucción de `v2.38AM` (contexto geopolítico).
