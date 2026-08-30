# Scout Finance v2.33H — mapeo de identificadores de Cboe Europe (OpenFIGI)

Estado: **`PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`**. Se identificó la empresa real detrás de 89/119 símbolos bloqueados de Cboe Europe, pero esto **no** produce todavía una fuente de precios descargable: para la mayoría de esas 89 empresas no es posible determinar de forma segura y automática cuál es su bolsa de cotización primaria a partir de los datos públicos disponibles. No se ha descargado ningún precio, no se ha creado ninguna cuenta, no se ha usado ninguna clave y no se ha gastado dinero.

## Por qué se hizo

v2.33F identificó que los 119 símbolos de "Cboe Europe" no son una sola bolsa, sino empresas de docenas de países cruzadas en una plataforma paneuropea, y que el paso previo necesario era mapear cada empresa a su identidad real (vía OpenFIGI, ya aprobado en v2.33C) antes de poder buscar una fuente de precios por bolsa.

## Método (fail-closed, sin adivinar)

Para cada uno de los 119 símbolos: se llamó a la búsqueda pública de OpenFIGI (`/v3/search`, sin cuenta ni clave) con el nombre de empresa de nuestro dataset, filtrando por `securityType`/`securityType2 == "Common Stock"` (excluyendo ADR, futuros, warrants y otros instrumentos que comparten el mismo nombre). Solo se acepta una empresa como **identificada** si, tras normalizar mayúsculas/puntuación y retirar sufijos legales conocidos (`AG`, `SE`, `PLC`, `INC`, `CORP`, `GROUP`, `-REG`, etc.), el nombre coincide de forma **exacta** con el nombre devuelto por OpenFIGI para un único `shareClassFIGI` (identificador global de la empresa/clase de acción). Si hay cero o varias empresas distintas que coinciden, se bloquea sin adivinar.

## Resultado

- **89/119 (74.8%) identificadas** de forma inequívoca (un único `shareClassFIGI` con coincidencia exacta de nombre).
- **30/119 sin identificar**: 29 por no encontrar una coincidencia exacta de nombre (variaciones de formato no cubiertas por la normalización aplicada) y 1 (`BlackRock Inc`, `P060`) por ambigüedad real: dos empresas distintas coinciden exactamente con ese nombre normalizado.
- **153 llamadas de red en total** (119 + 34 de reintento tras añadir la normalización de sufijo `-REG`, que recuperó 4 identificaciones adicionales: Siemens AG, Swisscom AG, y 2 más).

## El hallazgo clave: identificar la empresa no basta para descargar sus precios

De las 89 empresas identificadas:

- **13/89 (14.6%)** tienen un único código de mercado "compuesto" en OpenFIGI — pero, como se detalla abajo, esto **no equivale** a haber identificado su bolsa primaria real.
- **76/89 (85.4%)** tienen **varios** códigos de mercado compuestos simultáneamente (por ejemplo, Deutsche Boerse AG aparece con compuestos etiquetados `EO`, `GR`, `MM`, `SW` y `US` a la vez), porque OpenFIGI trata como "compuesto" tanto el mercado de origen como otros mercados donde la acción se cruza intensamente.

Sin un dato adicional que indique cuál de esos mercados es realmente el de cotización primaria (por ejemplo, capitalización, volumen, o un indicador explícito que las fuentes gratuitas consultadas no ofrecen), **elegir uno automáticamente sería adivinar** — exactamente lo que este proyecto se ha comprometido a no hacer. Por eso este piloto se detiene aquí en vez de forzar una selección.

Peor aún: incluso los 13 casos "inequívocos" (un único código de mercado compuesto) **no son de fiar como indicador de bolsa primaria**. Al inspeccionar qué empresas concretas caen en cada código:

| Código de mercado (OpenFIGI) | Empresas con ese único código |
|---|---|
| `EO` | UBS Group AG (Suiza), Aalborg Boldspilklub A/S (Dinamarca), Achilles Investment Co Ltd (Reino Unido), EJF Investments Ltd (Reino Unido), Future PLC (Reino Unido), Krynica Vitamin SA (Polonia), Société française de Casinos (Francia) |
| `GR` | DHH SpA (Italia), Flerie AB (Suecia), Unibap Space Solutions AB (Suecia) |
| `US` | Journeo PLC (Reino Unido) |
| `XS` | Cake Box Holdings PLC (Reino Unido) |
| `X2` | Solnaberg Property AB (Suecia) |

El mismo código (`GR`) aparece para una empresa italiana y dos suecas; el código `US` aparece para una empresa británica. **Esto descarta que estos códigos identifiquen el país o la bolsa de origen real**: son, casi con certeza, una categorización interna de OpenFIGI (por ejemplo, un segmento de liquidez o una agrupación técnica de su propio pipeline de datos) sin relación directa con la nacionalidad de la empresa. La correlación que parecía sugerir "GR = Alemania" o "US = Estados Unidos" en los ejemplos grandes usados para probar el script (Boeing → `US`, BHP Group → `AU`) era una coincidencia propia de esas empresas concretas, no una regla general.

**Conclusión reforzada:** ni siquiera en el caso "sin ambigüedad de código" hay una señal fiable de bolsa primaria en los datos gratuitos de OpenFIGI. Determinar la bolsa de cotización real de cualquiera de las 89 empresas identificadas exigiría, como mínimo, consultar el registro completo de cada `shareClassFIGI` y aplicar criterio adicional (capitalización, volumen, o confirmación externa por empresa) — no hay atajo automatizable con la evidencia disponible aquí.

## Por qué no se continúa más allá de este punto ahora

1. Incluso para las empresas con mercado inequívoco, v2.33F ya estableció que la mayoría de bolsas europeas principales (Alemania/Xetra confirmado, y por patrón esperado Reino Unido, Francia, Suiza, países nórdicos) no ofrecen una fuente oficial de precios gratuita — el hallazgo de v2.33F sobre Xetra (único dataset gratuito conocido, descatalogado) sería el escenario más probable para el resto.
2. Para el 85% de empresas con mercado ambiguo, resolver "cuál es la bolsa primaria" de forma fiable requeriría datos adicionales (capitalización de mercado, volumen por venue, o un indicador explícito de bolsa primaria) que no están disponibles gratuitamente con la misma rigurosidad que hemos exigido en el resto del proyecto.
3. Dado (1) y (2), seguir invirtiendo tiempo en resolver más símbolos de Cboe Europe tiene un retorno esperado bajo sin antes decidir si se acepta una fuente de pago (ya descartada para EODHD) o un nivel de certeza menor al exigido hasta ahora.

## Decisión

**`PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`**

- Se identifica la empresa real de 89/119 símbolos de Cboe Europe, con cero falsos positivos conocidos (el único caso ambiguo, BlackRock Inc, queda correctamente bloqueado).
- Esto **no** habilita ninguna descarga de precios nueva: no hay una bolsa primaria determinable de forma segura para el 85% de las empresas identificadas, y las que sí la tienen probablemente carecen de fuente gratuita oficial (según v2.33F).
- No se autoriza scoring, ranking, recomendaciones, fundamentales, contratación de planes de pago, conexión con brokers ni el inicio de la fase 5.
- Los 30 símbolos no identificados y los 76 con mercado ambiguo siguen bloqueados de forma fail-closed, sin equivalencias inferidas.

## Seguridad y alcance

- No se ha creado ninguna cuenta, no se ha usado ninguna clave (OpenFIGI no la requiere para este uso), no se ha gastado dinero.
- No se ha descargado ningún precio; solo metadatos de identificación de empresas (FIGI), que son identificadores públicos sin restricción de licencia para este uso.
- `production_scoring_authorized: false`, `allow_ranking: false`.

## Estado del roadmap

- No cambia el estado de v2.33D1, v2.33E, v2.33F ni v2.33G.
- Progreso global: 3/8 fases cerradas, fase 4 en curso.
- Siguiente paso recomendado (no ejecutado, no autorizado por este cierre): decidir si el usuario quiere invertir en una fuente de datos más rica (de pago, o con indicador explícito de bolsa primaria) para desambiguar las 76 empresas con mercado múltiple, o si se acepta cerrar Cboe Europe como bloqueado de forma permanente dado el patrón ya observado en v2.33F (bolsas europeas sin fuente gratuita oficial).
