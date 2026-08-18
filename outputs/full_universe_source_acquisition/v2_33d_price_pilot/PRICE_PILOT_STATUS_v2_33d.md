# Scout Finance v2.33D — estado del piloto de precios

## Trabajo completado

Se ha creado una muestra determinista de 240 activos sobre los 23.888 candidatos de v2.33B. La representación por origen es:

| Origen | Piloto |
|---|---:|
| Cboe Europe | 108 |
| JPX | 37 |
| Nasdaq listed | 32 |
| Nasdaq other listed | 24 |
| Xetra | 14 |
| ASX | 13 |
| TWSE | 7 |
| SGX | 4 |
| SFC/BVC | 1 |

El descargador valida el esquema EOD, limita la frecuencia, no imprime la clave y escribe una respuesta independiente por activo.

El preflight adicional deja **224/240** filas sin anomalías inmediatas y **16/240** en revisión: 8 nombres de fondo/trust, 2 productos cotizados, 1 SPAC, 1 nombre de prueba y 4 filas SGX con posible desplazamiento de campos.

## Por qué no se han descargado precios

Hay tres requisitos todavía ausentes:

1. **Resolución de símbolos.** Los tickers internos no equivalen necesariamente al símbolo que espera EODHD. Los activos Cboe Europe necesitan además recuperar su bolsa principal. Una coincidencia errónea contaminaría históricos y cualquier análisis posterior.
2. **Clave autorizada.** No existe `SCOUT_FINANCE_EODHD_API_TOKEN` ni se ha contratado un plan. El proyecto no puede comprarlo ni aceptar sus condiciones de licencia automáticamente.
3. **Corrección de elegibilidad.** El preflight de la muestra ha encontrado falsos candidatos: nombres de prueba, instrumentos cuyo nombre indica ETN/fondo/trust/SPAC y filas con ticker numérico que sugieren campos desplazados. v2.33B debe reabrirse y endurecerse antes de adquirir precios.

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
