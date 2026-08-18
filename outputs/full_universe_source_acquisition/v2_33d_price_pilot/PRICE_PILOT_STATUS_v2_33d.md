# Scout Finance v2.33D — estado del piloto de precios

## Trabajo completado

Se ha creado una muestra determinista de 240 activos sobre los 22.589 candidatos corregidos de v2.33B2. La representación por origen es:

| Origen | Piloto |
|---|---:|
| Cboe Europe | 111 |
| JPX | 39 |
| Nasdaq listed | 32 |
| Nasdaq other listed | 21 |
| Xetra | 15 |
| ASX | 14 |
| TWSE | 7 |
| SFC/BVC | 1 |

El descargador valida el esquema EOD, limita la frecuencia, no imprime la clave y escribe una respuesta independiente por activo.

Tras v2.33B2, el preflight deja **240/240** filas sin anomalías inmediatas. SGX permanece fuera del piloto hasta reparar su esquema.

## Por qué no se han descargado precios

Hay dos requisitos todavía ausentes:

1. **Resolución de símbolos.** Los tickers internos no equivalen necesariamente al símbolo que espera EODHD. Los activos Cboe Europe necesitan además recuperar su bolsa principal. Una coincidencia errónea contaminaría históricos y cualquier análisis posterior.
2. **Clave autorizada.** No existe `SCOUT_FINANCE_EODHD_API_TOKEN` ni se ha contratado un plan. El proyecto no puede comprarlo ni aceptar sus condiciones de licencia automáticamente.

El sistema falla de forma cerrada si falta cualquiera de ellos.

## Qué necesita hacer el usuario

Antes de continuar debe decidir si quiere probar EODHD. Si la respuesta es afirmativa:

1. crear una cuenta en EODHD;
2. confirmar qué plan o prueba permite EOD mundial y fundamentales;
3. revisar que el uso personal local y el almacenamiento en caché están permitidos;
4. configurar la clave localmente como variable de entorno, sin enviarla por chat ni guardarla en GitHub.

Después se ejecutará primero la resolución de los 240 símbolos y únicamente entonces la descarga piloto.

## Estado del roadmap

v2.33D todavía **no está cerrada**. La infraestructura y la muestra están listas, pero incorporar precios exige resultados reales y superar los umbrales de v2.33C.
