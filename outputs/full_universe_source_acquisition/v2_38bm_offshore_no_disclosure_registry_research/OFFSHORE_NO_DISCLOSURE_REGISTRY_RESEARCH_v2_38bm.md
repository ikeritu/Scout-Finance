# v2.38BM — 6 jurisdicciones offshore: cierre real por hecho legal estructural, y Jersey dejado deliberadamente abierto

Fecha: 2026-09-08. Alcance: cierres rápidos para las jurisdicciones offshore restantes tras el cierre ya confirmado de Islas Caimán (`v2.38AZ`) — Bermudas (74), Islas Vírgenes Británicas (24), Jersey (45), Guernsey (63), Isla de Man (12), Islas Marshall (4), 222 empresas nuevas más 100 de Caimán ya identificadas por `v2.38BC` pero nunca cerradas formalmente en la matriz.

## Investigación real por jurisdicción, cada una con su propia fuente citada

**Bermudas**: confirmado (Appleby, Conyers — despachos legales de referencia ya citados en este proyecto) que una "exempted company" **no tiene obligación general de presentar cuentas ante el Registrador** — solo una declaración estatutaria del capital social a efectos de la tasa anual. Los datos financieros no son públicos salvo excepciones regulatorias (aseguradoras comerciales) que no aplican a esta población.

**Islas Vírgenes Británicas**: desde el ejercicio 2023, las empresas BVI SÍ deben presentar una declaración financiera anual (balance + cuenta de resultados) — pero **se guarda de forma privada en la oficina del agente registrado, nunca se presenta ante el Registro de Asuntos Corporativos ni se hace pública**. Confirmado explícitamente que las empresas cotizadas en bolsas reconocidas están además exentas de esta obligación.

**Guernsey**: confirmado que **no existe obligación de presentar cuentas públicamente ante el Registro de Guernsey** — las cuentas se distribuyen a los accionistas, nunca al registro.

**Islas Marshall**: confirmado que las corporaciones domésticas no residentes **no tienen ninguna obligación de presentar estados financieros, declaración de impuestos ni informe anual** ante el Registrador (Trust Company of the Marshall Islands).

**Isla de Man**: investigación real en dos pasos, con un hallazgo inicial parcialmente engañoso corregido antes de cerrar. Una primera búsqueda sugería que las empresas públicas (PLC) sí depositan cuentas auditadas junto a su declaración anual. Una segunda búsqueda más específica lo contradice y aclara: **las cuentas no se presentan ante el Registro de Empresas de forma centralizada, ni siquiera para las PLC** — se preparan y se auditan, pero se conservan en la empresa, no en el registro público. Se documenta la contradicción encontrada, no se oculta.

**Islas Caimán**: ya confirmado en `v2.38AZ` (mismo régimen de "exempted company" sin obligación pública de depósito) — nunca antes conectado a esta matriz como un cierre formal pese a que la resolución masiva de `v2.38BC` ya había identificado 100 empresas reales bajo este país.

## Jersey, dejado deliberadamente sin cerrar — un hallazgo real distinto al resto

A diferencia de las 6 jurisdicciones anteriores, Jersey **sí exige por ley que las empresas públicas depositen cuentas auditadas** en un plazo de 7 meses tras el cierre del ejercicio — solo las empresas privadas están exentas. Al revisar las 45 empresas reales de Jersey del censo, **la inmensa mayoría llevan "PLC"/"plc" en su propia razón social** (3i Infrastructure PLC, B&M European Value Retail plc, CVC Capital Partners PLC, Genel Energy Plc...) — exactamente el tipo de entidad que sí tiene esta obligación real de divulgación pública.

Cerrar Jersey con el mismo hallazgo que las otras 6 habría sido deshonesto: ocultaría una divulgación real que probablemente existe. Se investigó si el registro de la JFSC (`sir.jerseyfsc.org`/`myreg.jerseyfsc.org`) permite un acceso automatizado real: la navegación directa al portal fue bloqueada, y una petición HTTP directa a la página de ayuda de búsqueda del registro devolvió **403 Forbidden real** — una señal de bloqueo activo contra acceso no interactivo, del mismo tipo ya visto con el NSM del Reino Unido (`v2.38BL`) e InfoCamere en Italia. Además, la documentación oficial describe un flujo de "añadir al carrito y pagar" para recuperar documentos del registro, lo que sugiere que al menos parte de la recuperación de documentos podría no ser gratuita.

**Jersey queda explícitamente abierto, no cerrado**: el dato correcto probablemente existe y es una obligación legal real, pero ni la vía de acceso ni el coste están confirmados como gratuitos y automatizables con seguridad. Se deja como pregunta real y honesta para una investigación futura, no como un hallazgo negativo.

## Resultado real en la matriz de las 43.089 (decimoquinta reconstrucción de `v2.38AL`)

Nuevo estado terminal `IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED`, distinto de `IDENTITY_ONLY_FUNDAMENTALS_BLOCKED_REAL_REASON_CONFIRMED` (que implica una fuente bloqueada o insuficiente) porque aquí no hay ninguna fuente que bloquear — es un hecho legal estructural: estas empresas nunca publican, por diseño jurídico de su jurisdicción.

| País | Empresas | Estado |
|---|---:|---|
| Islas Caimán (KY) | 100 | `IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED` (fuente: `v2.38AZ/BM`) |
| Bermudas (BM) | 74 | `IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED` (fuente: `v2.38BM`) |
| Guernsey (GG) | 63 | `IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED` (fuente: `v2.38BM`) |
| Islas Vírgenes Británicas (VG) | 24 | `IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED` (fuente: `v2.38BM`) |
| Isla de Man (IM) | 12 | `IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED` (fuente: `v2.38BM`) |
| Islas Marshall (MH) | 4 | `IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED` (fuente: `v2.38BM`) |
| **Total cerrado** | **277** | |
| Jersey (JE) | 45 | Sin cambios — `IDENTITY_ONLY_NO_FUNDAMENTALS_YET`, abierto deliberadamente |

**Verificación cruzada real**: 74+63+24+12+4+100 = 277, exacto contra el resultado real de la reconstrucción. `NO_DATA_YET` se mantiene en 38.055 (sin cambios, ninguna identidad nueva resuelta en este bloque — solo se reclasifica el estado de fundamentales de empresas ya identificadas).

## Qué NO hace este bloque

No cierra Jersey — queda como una investigación real pendiente, con una pista concreta para retomarla (probar si el 403 persiste con una petición desde un navegador real interactivo antes de descartar la vía, y confirmar si la recuperación de documentos es realmente de pago o solo el flujo de "carrito" es cosmético). No modifica ningún dato de identidad ya resuelto. Sin scoring, ranking, recomendaciones ni fase 9C.

## Pruebas offline

3 pruebas nuevas en `tests/qa_global_coverage_matrix_v2_38al.py` (21 en total): una jurisdicción offshore cerrada recibe el estado correcto y no el genérico de "sin fundamentales todavía", Islas Caimán cita ambas fuentes (`v2.38AZ` y `v2.38BM`), y Jersey queda explícitamente sin cerrar pese a tener país e identidad reales.

**Estado del bloque: `COMPLETED_OFFSHORE_NO_DISCLOSURE_REGISTRY_RESEARCH_JERSEY_LEFT_OPEN`.** 6 de 7 jurisdicciones offshore cerradas con un hecho legal real y citado; Jersey queda honestamente sin resolver en vez de forzado a encajar en un cierre que no le corresponde.
