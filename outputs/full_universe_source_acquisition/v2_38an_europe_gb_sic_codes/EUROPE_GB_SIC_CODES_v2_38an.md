# v2.38AN — Reino Unido: códigos SIC reales vía el endpoint correcto de Companies House

Fecha: 2026-09-06. Alcance: atacar el hallazgo de `v2.38AM` (0/689 empresas europeas con coincidencia real de sector) empezando por Reino Unido, donde ya existía acceso confirmado y gratuito a Companies House.

## Bug real encontrado, no un rodeo

`v2.38Y` ya tenía una columna `sic_codes` en su matriz de resultados — pero llevaba vacía desde el principio. La causa real: `search_company()` llama al endpoint de **búsqueda** de Companies House (`/search/companies`), cuyos resultados **nunca** incluyen `sic_codes` — ese campo solo existe en el endpoint de **perfil completo** (`/company/{numero}`). Confirmado en vivo antes de escribir este script: una llamada real a `/company/00023307` (Diageo plc) devuelve `sic_codes: ["70100"]`, mientras que la búsqueda por nombre nunca lo trae. Este script llama al endpoint correcto para las 29 empresas ya confirmadas por `v2.38Y`, reutilizando la misma credencial y el mismo ritmo de peticiones.

## Resultado real

**29/29 empresas con código SIC real obtenido, 0 errores.** Los 23 códigos reales distintos que aparecieron se verificaron uno a uno contra la lista oficial condensada de Companies House (`resources.companieshouse.gov.uk/sic/`) antes de traducirlos — ninguna descripción se adivinó. Ejemplos reales: Barclays → `64191` "Banks", BAE Systems → `25400`/`29100`/`30110`/`30300` (armamento, vehículos, buques, aeroespacial), London Stock Exchange → `66110` "Administration of financial markets", TechnipFMC → `09100` "Support activities for petroleum and natural gas mining".

## Hallazgo honesto: la mayoría son entidades holding, no operativas

**14 de las 29 empresas** (Diageo, Imperial Brands, Rio Tinto, SSE, BP, Kingfisher, easyJet, Compass Group, National Grid, Haleon, GSK, Shell, Aviva, Unilever) muestran el código `70100` "Activities of head offices" — la entidad legal registrada en Companies House es la matriz/holding del grupo, no la operación real. Esto es exactamente el mismo patrón ya documentado para Austria (`v2.38AI`, individual vs. consolidado) y ahora confirmado también en GB: el registro oficial refleja la estructura jurídica de la matriz, no necesariamente el sector operativo real de la marca.

## Salvaguardas

Bloqueado por defecto; requiere `--execute` y la misma credencial `SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY` ya usada en `v2.38Y`. 7 pruebas offline nuevas. Sin scoring, sin ranking, sin recomendaciones.

**Estado del bloque: `COMPLETED_EUROPE_GB_SIC_CODES`.** Alimenta directamente la reconstrucción de `v2.38AM` (contexto geopolítico).
