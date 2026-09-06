# v2.38AY — Bulgaria, Liechtenstein y Malta: investigación real de registro, sin vía gratuita confirmada

Fecha: 2026-09-06. Alcance: investigar, con la misma disciplina de desk research ya aplicada a los 13 países originales y a Luxemburgo, si Bulgaria, Liechtenstein y Malta tienen una vía oficial gratuita para fundamentales reales de las 4 empresas que `v2.38AV` reveló en esos países — Shelly Group PLC y Sirma Group Holding (Bulgaria), Cerdios SE (Liechtenstein), Samara Asset Group (Malta).

## Por qué no se construyó ningún script

Como en Alemania (`v2.38AC`/`v2.38AP`) y Suiza (`v2.38AG`), la investigación por sí sola alcanza una conclusión negativa clara con evidencia real y en vivo — construir un script sería atacar una vía ya confirmada como bloqueada.

## Bulgaria — WAF real confirmado en el portal nacional de datos abiertos

- `data.egov.bg` (el catálogo nacional de datos abiertos, donde según fuentes de terceros se publican los informes financieros anuales — ГФО — del Registro Mercantil bajo licencia CC-BY) devuelve **403 real y confirmado en vivo** para cualquier petición automatizada, con o sin cabecera `User-Agent` de navegador, en múltiples rutas (`/`, `/organisation/`, `/api/3/action/package_list`). Mismo patrón exacto que el WAF ya documentado para España (`v2.38AA`).
- El propio portal del Registro Mercantil (`portal.registryagency.bg`, antes `brra.bg`, que redirige ahí) es el "ЕПЗЕУ" — un portal web JavaScript/Bootstrap de solicitud de servicios electrónicos, sin ningún API documentado.
- Existe un agregador privado, **CompanyBook.BG**, que anuncia una "API completa" con datos financieros reales (activo, patrimonio neto, ingresos) reutilizando los datos abiertos oficiales. Comprobado en vivo: el sitio funciona (200), pero es una empresa privada con sistema de cuenta/login y planes de suscripción de pago (`free`/`register`/`subscribe`/`account` aparecen todos repetidamente en su portada) — no es una reutilización neutral de datos abiertos como Wikidata, sino un producto comercial de un tercero no verificado. **Presentado al usuario, quien decidió no usarlo** — Bulgaria queda sin vía gratuita confirmada.

## Liechtenstein — mismo patrón estructural que Suiza, más un bloqueo de acceso real

- `llv.li` (la página oficial de la Oficina de Justicia sobre el Registro Mercantil) devuelve **403 real confirmado en vivo**, incluso con cabecera de navegador.
- El portal real de búsqueda, `handelsregister.li`, permite buscar gratis por nombre y ver solo nombre legal, forma jurídica, municipio, estado y objeto social — sin ninguna cifra financiera. El extracto detallado (capital, representantes, accionistas) es un PDF no certificado de pago, aproximadamente 10 CHF.
- Sin API, sin dataset abierto. Dado que Liechtenstein es, junto con Suiza, una de las jurisdicciones europeas con menor obligación legal de divulgación pública de cuentas anuales para sociedades no cotizadas, este hallazgo es coherente con el ya documentado en `v2.38AG` — un límite estructural, no solo de acceso. **Presentado al usuario, quien decidió cerrar sin pagar el extracto** — 1 sola empresa (Cerdios SE), coherente con la política ya establecida del proyecto de no usar fuentes de pago.

## Malta — un subdominio de API real pero completamente sin configurar

- La Malta Business Registry (MBR) modernizó su plataforma en 2025 y anunció públicamente "tres nuevas API" — pero **comprobado en vivo que `api.mbr.mt` es literalmente la plantilla de ejemplo sin configurar de ASP.NET Web API** (título "Application name", controlador de ejemplo "Values", texto genérico de Microsoft sobre ASP.NET) — no una API real, documentada ni funcional para datos de empresas.
- El acceso real a estados financieros ("Public Accounts") exige, desde agosto de 2025, una cuenta gratuita registrada — pero cada documento se **compra individualmente**, no se consulta como dato estructurado gratis.
- **Presentado al usuario, quien decidió cerrar sin crear la cuenta ni comprar el documento** — 1 sola empresa (Samara Asset Group), mismo espíritu que el bloqueo de política ya aplicado a fuentes de pago en Irlanda/Países Bajos.

## Resultado real

**0/4 empresas con fundamentales reales** — las tres jurisdicciones quedan confirmadas sin vía gratuita, con evidencia real y en vivo para cada una, presentada al usuario antes de cerrar (no asumida unilateralmente). Ninguna de las 4 empresas tenía ya sector clasificado por Wikidata en el esfuerzo anterior (`v2.38AM`) tampoco, así que quedan como identidad confirmada (`v2.38AV`) sin ningún enriquecimiento adicional por ahora.

## Qué NO hace este bloque

No modifica `v2.38AV` (la identidad de las 4 empresas sigue siendo real y válida). No reconstruye `v2.38AL` ni `v2.38AM`. No descarta la posibilidad de revisar CompanyBook.BG con más detalle en el futuro si el usuario cambia de opinión.

## Seguridad y alcance

Sin scripts, sin credenciales, sin cuentas creadas, sin pagos realizados. Toda la evidencia (códigos HTTP reales, contenido real de las páginas) comprobada en vivo antes de presentar las opciones al usuario. Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_BULGARIA_LIECHTENSTEIN_MALTA_REGISTRY_RESEARCH_NO_VIABLE_FREE_SOURCE`.** Cierra la investigación de registro para los 5 países nuevos revelados por `v2.38AV` — junto con Luxemburgo (`v2.38AW`/`v2.38AX`, 16/20 con fundamentales reales) y Islas Caimán (nunca investigado, 1 empresa, Joby Aviation, pendiente si el usuario lo pide).
