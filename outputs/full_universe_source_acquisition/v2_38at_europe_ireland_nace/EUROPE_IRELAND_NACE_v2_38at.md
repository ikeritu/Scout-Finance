# v2.38AT — Irlanda: código NACE real, reutilizando el CRO ya aprobado — y un campo confirmado no fiable

Fecha: 2026-09-06. Alcance: continuar el ataque al hueco de sector europeo con Irlanda (17/689 activos, 8/17 con perfil CRO real desde `v2.38Z`).

## Ninguna decisión de política nueva necesaria

`v2.38Z` ya usa el dataset abierto del CRO irlandés (`opendata.cro.ie`, API CKAN gratuita, sin clave) para confirmar identidad — pero solo extraía `company_status`/`company_type`/`company_reg_date`. Investigando la respuesta completa se confirmó en vivo que **cada registro ya incluye un campo `nace_v2_code`** (el código NACE Rev.2 oficial), nunca antes leído. Es la misma fuente ya usada, sin ninguna aprobación nueva del usuario.

## Un segundo campo real, confirmado NO fiable — y por qué

Los registros del CRO también incluyen `princ_object_code` — pero se comprobó en vivo un caso real y concreto que desaconseja usarlo: **Alkermes plc** (número de sociedad 498284, una farmacéutica real y conocida) muestra `princ_object_code: "24.41"` — "Fabricación de metales preciosos y otros metales no férreos". Esto no puede ser su actividad real. Se confirmó además que Alkermes plc **no es una sociedad reutilizada con historial previo** — se constituyó de nuevo en Irlanda específicamente para la fusión Alkermes/Elan Drug Technologies de 2011 (confirmado vía el propio comunicado de relación con inversores de Alkermes) — así que el código erróneo probablemente refleja texto genérico de la cláusula de objeto social de la memoria de constitución, no una clasificación real. Dado un caso confirmado de error en una empresa muy conocida, `princ_object_code` se captura solo para trazabilidad, **nunca se usa como texto de coincidencia de sector**.

## Resultado real

**3/8 empresas con código NACE real confirmado** (Smurfit Westrock, TE Connectivity, Linde — las tres con código `6420` "Activities of holding companies", verificado contra el registro oficial INSPIRE de la UE). **5/8 sin `nace_v2_code`** pero con `princ_object_code` presente y deliberadamente no usado (ICON, Alkermes, Willis Towers Watson, Allegion, Medtronic).

**Mismo patrón ya visto en GB/Francia/Suiza/Italia/Austria**: las 3 empresas con código real muestran "actividades de sociedades holding" — la entidad irlandesa registrada es el vehículo de domicilio del grupo, no su operación real (todas son empresas estadounidenses reales que se redomiciliaron a Irlanda). Ninguna de las 3 coincide con ningún tema de sector de la taxonomía (no hay palabra clave para "holding companies" en el motor actual) — resultado honesto, no un fallo.

## Salvaguardas

Bloqueado por defecto; requiere `--execute` (sin credencial). Emparejamiento estricto por número de sociedad, nunca el primer resultado de una búsqueda de texto libre. 6 pruebas offline nuevas, incluida una que reproduce exactamente el caso real de Alkermes. Sin scoring, sin ranking, sin recomendaciones.

**Estado del bloque: `COMPLETED_EUROPE_IRELAND_NACE`.** Alimenta la octava reconstrucción de `v2.38AM` (sin subir el contador de coincidencias reales de sector, un resultado honesto: "holding company" no coincide con ningún tema actual, pero la fuente queda correctamente atribuida y trazable para las 3 empresas).
