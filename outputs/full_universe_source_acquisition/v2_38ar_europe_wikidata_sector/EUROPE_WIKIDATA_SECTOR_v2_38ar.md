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

---

## Re-ejecución (mismo día, 2026-09-06): Italia, tercer país con el mismo mecanismo generalizado

Instrucción del usuario: "sigue con Italia para el hueco de sector" (22/689 activos). Investigación real del registro oficial (InfoCamere/Registro Imprese):

1. **Existe un portal de datos abiertos genuinamente gratuito por regulación europea** (`hvdataset.infocamere.it`, licencia CC BY 4.0, incluye código ATECO junto con el nombre de la empresa — a diferencia del dataset abierto anonimizado del KVK neerlandés) — pero su frontend real usa **reCAPTCHA de Google**, y fuentes independientes confirman que el acceso vía API/descarga masiva está sujeto a "criterios muy restrictivos" que no permiten una consulta simple por empresa sin pasar por ese control. Este proyecto nunca sortea un reto anti-bot real.
2. El otro canal oficial (`accessoallebanchedati.registroimprese.it`) es un producto claramente comercial ("contacta con nuestros expertos", sin precios públicos) — de pago, no de autoservicio gratuito.

Presentada de nuevo la disyuntiva real al usuario (Wikidata, ya comprobado en vivo con 16/22 coincidencias, 0 ambiguas, o dejar el país sin atacar) — **el usuario eligió Wikidata por tercera vez**. Al ser ya la tercera vez que se usa el mismo mecanismo, **no se creó ningún script nuevo** — se reejecutó directamente `v2.38AR` con `--countries CH IT`, confirmando en la práctica que la generalización hecha para Suiza ya cubre cualquier país futuro sin cambios de código.

### Resultado real

**16/22 empresas italianas con industria real capturada, 0 errores, 0 ambiguas, 6 sin coincidencia en Wikidata.** Ejemplos reales: Generali→"insurance industry", Intesa Sanpaolo/UniCredit/BPER/Banco BPM→banca, Eni→"energy industry;petroleum industry", Leonardo→"aerospace engineering;aerospace industry;aircraft industry;information security;weapons industry" (coincide correctamente con el tema `DEFENSE_SECURITY`), Poste Italiane→"economics of banking;logistics;postal sector", Fincantieri→"shipbuilding", Moncler→"clothing industry".

**Estado de la re-ejecución: `COMPLETED_EUROPE_WIKIDATA_SECTOR`.** Sin pruebas nuevas necesarias — el mecanismo genérico de `v2.38AR` (probado con Suiza) ya cubre a Italia sin cambios de código, confirmando que la generalización fue la decisión correcta. Alimenta la quinta reconstrucción de `v2.38AM`.

---

## Re-ejecución (mismo día, 2026-09-06): Dinamarca — el primer caso donde la vía oficial gratuita SÍ existe, solo pendiente de credencial

Instrucción del usuario: "sigue con Dinamarca para el hueco de sector" (21/689 activos). A diferencia de Alemania/Suiza/Italia (donde la vía oficial resultó bloqueada, retenida o detrás de reCAPTCHA), Dinamarca es un caso distinto: el registro oficial **CVR** (Erhvervsstyrelsen) sí tiene una API real y gratuita con el código de rama **DB07** (extensión danesa de NACE) — pero exige una cuenta registrada. Confirmado en vivo: `distribution.virk.dk` devuelve `401 Authorization Required` sin credencial; la vía oficial de acceso sistema-a-sistema exige contactar con `cvrselvbetjening@erst.dk` para obtenerla — el mismo proceso de solicitud de credencial ya iniciado en una fase anterior de este proyecto (para fundamentales, no para sector), pero sin confirmación de si se completó. También se comprobó y descartó `cvrapi.dk`, un proxy no oficial de terceros: **cuota agotada en la primera llamada de prueba**, poco fiable y no gubernamental.

Preguntado directamente al usuario si ya tenía la credencial CVR — **respondió que aún no**, y eligió usar Wikidata mientras tanto (ya comprobado en vivo con 14/21 coincidencias reales, 0 ambiguas). Al ser el cuarto país con el mismo mecanismo, se reejecutó `v2.38AR` con `--countries CH IT DK`, sin ningún script nuevo.

### Resultado real

**14/21 empresas danesas con industria real capturada, 0 errores, 0 ambiguas, 7 sin coincidencia en Wikidata** (incluida, sorprendentemente, Novo Nordisk — un hueco real de datos en Wikidata para esa empresa concreta, no un fallo del script). Ejemplos reales: Carlsberg→"beverage industry;food industry", Maersk (clase B)→"water transport", Genmab/Bavarian Nordic→"biotechnology", Ørsted→"energy industry", Coloplast→"health care", Tryg→"insurance industry", ISS→"facility management".

**Nota para el futuro**: si el usuario completa el registro CVR, este bloque debería revisitarse para sustituir Wikidata por el código DB07 oficial — igual que se hizo con GB/Francia respecto a fuentes oficiales, Dinamarca es el único de los países atacados hasta ahora donde la vía oficial gratuita genuinamente existe y solo falta completar el registro.

**Estado de la re-ejecución: `COMPLETED_EUROPE_WIKIDATA_SECTOR`.** Sin pruebas nuevas necesarias. Alimenta la sexta reconstrucción de `v2.38AM`.

---

## Re-ejecución (mismo día, 2026-09-06): España — la mejor cobertura de todos los países atacados hasta ahora

Instrucción del usuario: "sigue con España para el hueco de sector" (15/689 activos, todos del IBEX 35). Reconfirmado que las tres vías oficiales españolas siguen bloqueadas exactamente igual que en `v2.38AA`: el Colegio de Registradores sigue devolviendo el mismo bloqueo WAF, y se comprobó además que la propia herramienta de "Distribución por Sectores" de la CNMV (que sí clasifica emisores por sector) es un formulario web ASPX sin ningún API — automatizarla sería scraping.

Presentada de nuevo la disyuntiva real (Wikidata, ya comprobado en vivo con 13/15 coincidencias reales, o dejar el país sin atacar) — **el usuario eligió Wikidata por cuarta vez**. Se reejecutó `v2.38AR` con `--countries CH IT DK ES`, sin ningún script nuevo.

### Resultado real

**13/15 empresas españolas con industria real capturada — la mejor cobertura relativa de todos los países atacados hasta ahora (86,7%)**, 1 ambigua (Banco Santander, el mismo tipo de caso real ya visto con Ahold Delhaize — dos elementos de Wikidata distintos), 1 sin coincidencia (AENA). Ejemplos reales: Cellnex→"telecommunications infrastructure", Amadeus IT→"software industry", BBVA/Sabadell/CaixaBank→banca, Indra→"IT service management", Endesa/Iberdrola/Redeia→energía eléctrica, Inditex→"fast fashion;retail;textile industry", Repsol→"petroleum industry", IAG→"aviation", Telefónica→telecomunicaciones.

**Estado de la re-ejecución: `COMPLETED_EUROPE_WIKIDATA_SECTOR`.** Sin pruebas nuevas necesarias. Alimenta la octava reconstrucción de `v2.38AM`.
