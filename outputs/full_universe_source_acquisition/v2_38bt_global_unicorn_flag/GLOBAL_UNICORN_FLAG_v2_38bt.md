# v2.38BT — el icono 🦄 unicornio: 161 empresas reales, reutilizando datos ya calculados, cero scoring nuevo

Fecha: 2026-09-08. Alcance: el usuario pidió, junto al enlace de "Ver en Google Finance", un icono que marque a las empresas "con más potencial y más expectativas de crecimiento" en la pantalla "Universo global" — llamándolas "unicornios".

## Por qué esto no es la Fase 9C por otra puerta

Elegir un umbral de crecimiento (p. ej. "más del 15% de crecimiento de ingresos") sería exactamente el tipo de decisión metodológica que la Fase 9C, todavía no autorizada, existe para formalizar. Antes de construir nada, se preguntó al usuario qué criterio real usar; eligió "combinación de varias métricas" y aplicarlo a todo el censo. En vez de inventar un umbral nuevo, se encontró que **ya existe un campo real y documentado en `v2.38G`** que hace exactamente eso: `fundamental_momentum_flag` — crecimiento real de ingresos > 0 **Y** expansión real de margen frente al periodo anterior **Y** flujo de caja libre real positivo, los tres ya calculados, combinados con un simple AND, nunca un score ponderado.

## Dos reglas reales, una por región, nunca inventando el dato que falta

**EE. UU. (v2.38G, v2.38BK, v2.38BA — 555 originales + 538 nuevas de Cboe Europe + Joby Aviation)**: se reutiliza tal cual `fundamental_momentum_flag`, sin recalcular nada.

**Austria (v2.38AK, único origen europeo con datos de crecimiento real hoy)**: su propio pipeline nunca calcula flujo de caja libre (su docstring lo dice explícitamente — los conceptos capturados en Austria no incluyen flujo de caja operativo ni capex), así que aplicar la fórmula de EE. UU. tal cual habría fabricado una señal que Austria nunca pudo respaldar. En su lugar, Austria usa el mismo espíritu con solo sus campos reales: crecimiento real de ingresos > 0 **Y** aceleración real de crecimiento (este año supera al anterior) **Y** expansión real de margen.

## Ninguna fila queda en un silencio de "false"

Cada empresa evaluada recibe un estado explícito, nunca un booleano plano: `EVALUATED_UNICORN`, `EVALUATED_NOT_UNICORN` (evaluada de verdad, no cumple los 3 criterios) o `INSUFFICIENT_DATA` (sus features de crecimiento no se pudieron calcular en absoluto). Una empresa sin ninguna fila de features de crecimiento en ninguna de las cuatro fuentes simplemente no aparece en este fichero — la pantalla la deja en blanco, nunca en un "no es unicornio" calculado sin datos reales que lo respalden.

## Resultado real

| Estado | Empresas |
|---|---:|
| `EVALUATED_UNICORN` 🦄 | **161** |
| `EVALUATED_NOT_UNICORN` | 690 |
| `INSUFFICIENT_DATA` | 259 |
| **Total evaluado** | **1.110** |

Ejemplos reales marcados: Apple Inc., Adobe Inc., Analog Devices, ACADIA Pharmaceuticals, ACI Worldwide. El caso real de prueba de Austria (STRABAG SE, `revenue_yoy_growth` real 4,82%, con aceleración y expansión de margen reales) también resuelve correctamente a unicornio.

## El enlace "Ver en Google Finance"

Añadido como columna en la misma tabla, para toda fila (no solo unicornios) — deliberadamente **no** un enlace directo a `google.com/finance/quote/TICKER:EXCHANGE`: este proyecto no tiene un mapeo real y verificado de sus códigos de bolsa internos a los mnemónicos de bolsa de Google (NASDAQ, ETR, BIT, LON...) para las decenas de mercados del censo, y adivinar mal uno solo entre 43.089 empresas enviaría al usuario a la página equivocada sin avisar. En su lugar, es un enlace de búsqueda real de Google (`{empresa} stock`) — siempre resuelve a una página real y legítima de resultados (con la tarjeta de Google Finance cuando Google la tiene), sin ese riesgo. Scout Finance nunca descarga, procesa ni almacena nada de Google — es solo un acceso directo para que el usuario consulte manualmente.

## Qué NO hace este bloque

No calcula ningún score, ranking ni composite ponderado. No modifica `v2.38AL`, `v2.38AM` ni `v2.38BO`. No autoriza ni adelanta la Fase 9C. No aplica el criterio a ninguna empresa fuera de EE. UU./Austria — las demás simplemente no tienen datos de crecimiento reales que evaluar todavía.

## Pruebas offline

7 casos en `tests/qa_global_unicorn_flag_v2_38bt.py`: el flag real de EE. UU. marca unicornio, una empresa evaluada que no cumple queda explícita como `EVALUATED_NOT_UNICORN` (nunca desaparece), datos insuficientes es un estado distinto de "no", Austria exige sus 3 señales reales sin exigir flujo de caja, un crecimiento negativo nunca califica aunque los demás flags sean reales y positivos, el cruce real de Joby Aviation (Caimán↔EE. UU., mismo caso que `v2.38AL`) se replica correctamente, y una empresa ausente de las 4 fuentes no aparece en absoluto en el fichero. Más 4 pruebas nuevas en `tests/qa_ui_global_universe_v2_38al.py` (13 en total): el fichero de unicornio se une correctamente por `asset_id`, la cadena del botón "Actualizar" pasa de 3 a 4 pasos reales, y un fallo real de elegibilidad detiene la cadena antes del paso de unicornio.

## Seguridad y alcance

Sin red, sin credenciales, sin scoring, ranking ni recomendaciones. El enlace de Google Finance no descarga ni procesa ningún dato — es solo una conveniencia de navegación manual para el usuario.

**Estado del bloque: `COMPLETED_GLOBAL_UNICORN_FLAG_DEFINED_NOT_SCORED`.** 161 empresas reales marcadas, reutilizando exclusivamente datos ya calculados y documentados en fases anteriores — ningún umbral nuevo inventado, ningún dato fabricado para Austria, ninguna fila silenciada.
