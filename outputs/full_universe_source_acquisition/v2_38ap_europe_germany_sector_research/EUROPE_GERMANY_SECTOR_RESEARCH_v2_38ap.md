# v2.38AP — Alemania: investigación de clasificación sectorial, hallazgo negativo estructural confirmado (real, sin script)

Fecha: 2026-09-06. Alcance: continuar el ataque al hueco de sector europeo (0/689 al inicio, 7/689 tras GB/`v2.38AN` y Francia/`v2.38AO`) con Alemania — el país más grande del universo europeo (413/689 activos, ya con identidad 100% resuelta desde `v2.38AB`).

## Diferencia real con GB y Francia, confirmada antes de escribir ningún código

En GB y Francia el problema era de **acceso** (GB: consultar el endpoint equivocado de una API que sí tenía el dato; Francia: un campo de una API ya validada que nunca se había leído). En Alemania el problema es distinto y más fundamental, confirmado con evidencia real de fuentes oficiales alemanas:

> "Den WZ-Code eines Unternehmens kannst du meist nicht öffentlich nachschlagen" — el código WZ 2008 (la clasificación sectorial oficial alemana, equivalente a NACE) **no se puede consultar públicamente para una empresa concreta**, ni siquiera cuando el propio Destatis (Oficina Federal de Estadística) lo mantiene internamente en su Unternehmensregister estadístico.

El propio registro estadístico de Destatis contiene el "Wirtschaftszweig" de cada empresa alemana activa — pero **no lo publica por empresa individual a terceros**; solo la propia empresa puede consultar su código a través de la oficina estadística de su Land, o un tercero puede intentar inferirlo manualmente vía el "Klassifikationsserver" de Destatis (una búsqueda por texto libre de la definición del código, no una consulta por empresa).

## Tres vías reales investigadas, todas con resultado negativo real

### 1. Handelsregister / Bundesanzeiger (ya confirmado en v2.38AC, reconfirmado aquí)

Ya documentado: sin API oficial, portal de solo consulta humana. Además, **confirmado ahora específicamente para el código WZ**: ni el Handelsregister ni el Bundesanzeiger incluyen nunca el código WZ en sus publicaciones — el dato de clasificación sectorial no vive en ninguno de los dos registros mercantiles/de cuentas, a diferencia de Companies House (GB) o SIRENE (Francia), donde el código de actividad SÍ es parte del registro público.

### 2. Unternehmensregister estadístico de Destatis

Existe y contiene el dato real — pero es explícitamente **no público por empresa** (confirmado arriba). Un tercero solo puede consultar la definición de un código WZ (el "Klassifikationsserver"), nunca qué código tiene una empresa concreta.

### 3. Sistema europeo BRIS (Business Registers Interconnection System)

Vía oficial de la UE que interconecta los registros mercantiles nacionales — comprobado que solo ofrece un portal humano (e-Justice Portal), sin API pública documentada, y que además **explícitamente no incluye clasificación sectorial ni datos financieros**, solo verificación básica de existencia de la empresa. Descartado incluso si tuviera API, por no llevar el dato que se busca.

## Comprobación adicional real, fuera de alcance de esta investigación pero relevante para el próximo país

Se comprobó también si el KVK (registro mercantil neerlandés, ya usado para identidad de 44 activos vía GLEIF en `v2.38AE`) ofrece un camino gratuito: su API real de producción **exige suscripción de pago** ("a standard amount per month and a small fee per query", confirmado en `developers.kvk.nl`) — descartado por la política ya establecida de este proyecto de no usar fuentes de pago, igual que EODHD y Cboe Europe. Solo su portal web humano ("Company Check") es gratuito, limitado a 30 consultas/año por usuario, sin API. Se deja documentado para cuando el usuario decida continuar con otro país.

## Conclusión

**No existe hoy ninguna vía gratuita, oficial y accesible sin scraping para obtener la clasificación sectorial de las 413 empresas alemanas.** A diferencia de GB/Francia, esto no es un problema de "encontrar el endpoint correcto" — es que el dato de clasificación sectorial alemán **no se publica por empresa a través de ningún canal gubernamental**, por diseño de la confidencialidad estadística alemana. No se construye ningún script.

## Seguridad y alcance

- Red real usada: solo búsquedas e investigación de documentación pública durante esta investigación.
- Ninguna cuenta creada, ninguna credencial usada ni necesaria.
- Sin scraping, sin rodeo de ninguna medida de acceso, sin pago.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_GERMANY_SECTOR_RESEARCH_NO_VIABLE_FREE_SOURCE_STRUCTURAL`.** Hallazgo negativo real y estructural (el dato no es público, no solo "difícil de alcanzar") — distinto en naturaleza de los hallazgos de GB/Francia, y coherente con el propio patrón de "causa raíz distinta según el país" ya visto en Suiza (`v2.38AG`: sin obligación legal de depósito) frente a Italia (`v2.38AH`: dato gratuito pero solo vía interfaz web).
