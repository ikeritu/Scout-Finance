# v2.38AR — Suiza (y generalización): Wikidata, tras confirmar en vivo que el registro oficial suizo no expone NOGA en su nivel público

Fecha: 2026-09-06. Alcance: continuar el ataque al hueco de sector europeo con Suiza (29/689 activos, identidad ya resuelta al 100% desde `v2.38AB`), generalizando `v2.38AQ` (hasta ahora específico de Países Bajos) a cualquier país europeo.

## Investigación real, con prueba en vivo antes de decidir nada

A diferencia de Alemania (donde la investigación de escritorio ya bastó), aquí se implementó y probó en vivo un cliente SOAP real contra el registro oficial suizo **UID** (Oficina Federal de Estadística, `uid-wse-a.admin.ch`):

1. **Confirmado en vivo, gratis, sin cuenta**: el servicio `PublicServices` responde con datos reales (probado con Nestlé, Novartis vía otras pruebas, Sika, Straumann, Logitech) — nombre legal, dirección, número UID, estado de IVA, estado del registro mercantil, todo real y correcto.
2. **El esquema oficial (WSDL/XSD) SÍ define un campo `NOGACode`** (y `uidBrancheText`) dentro del tipo de organización — la clasificación sectorial existe en el sistema.
3. **Pero en la práctica, nunca aparece**: probado con 4 empresas reales distintas Y con el registro de ejemplo oficial del propio servicio (`GetOrganisationSample`, un "Beispiel GmbH" diseñado para mostrar todos los campos posibles) — **ni `NOGACode` ni `uidBrancheText` aparecen nunca** en el nivel `PublicServices` (sin autenticación). Exactamente el mismo patrón que Alemania (`v2.38AP`): el dato existe en el sistema oficial pero se retiene para el nivel autenticado/registrado.

Esta es una investigación más rigurosa que un simple hallazgo de escritorio: se construyó y ejecutó un cliente SOAP real, con evidencia de 5 llamadas en vivo (4 empresas + 1 registro de ejemplo), antes de concluir el hallazgo negativo.

## La decisión, presentada de nuevo al usuario

Igual que con Países Bajos, se comprobó Wikidata como alternativa **antes** de proponerla: 16/29 empresas suizas con industria real, 0 ambiguas. Presentada la elección (Wikidata / dejar el país sin atacar) — **el usuario eligió Wikidata de nuevo**.

## Por qué se generalizó en vez de duplicar v2.38AQ

Con un segundo país usando exactamente el mismo mecanismo (Wikidata por ISIN), se generalizó siguiendo el mismo patrón ya aplicado repetidamente en este proyecto (GLEIF: `v2.38AE`→`v2.38AF`; alias de conceptos contables). `v2.38AQ` (Países Bajos) queda intacto como registro histórico; `v2.38AR` es el script que se reejecutará para cualquier país futuro (acepta `--countries`).

## Resultado real

**15/29 empresas suizas con industria real capturada, 0 errores, 1 ambigua, 6 sin coincidencia en Wikidata, 7 con elemento pero sin industria.** Ejemplos reales: Novartis→"chemical industry;pharmaceutical industry", Nestlé→"food industry", ABB→"electrical engineering;robotics", UBS→"economics of banking;financial sector;...", Sika→"chemical industry;construction", Alcon→"pharmaceutical industry".

## Salvaguardas

Bloqueado por defecto; requiere `--execute` (sin credencial). 6 pruebas offline nuevas. Sin scoring, sin ranking, sin recomendaciones. Cada fila lleva el mismo `non_official_source_caveat` que `v2.38AQ`.

**Estado del bloque: `COMPLETED_EUROPE_WIKIDATA_SECTOR`.** Alimenta la cuarta reconstrucción de `v2.38AM`. El hueco de sector europeo pasa de 21/689 a 27/689 con este bloque.
