# v2.38AZ — Islas Caimán: sin vía pública por diseño legal, y un hallazgo real que cambia la pregunta

Fecha: 2026-09-06. Alcance: investigar si existe una vía oficial gratuita de fundamentales para la única empresa que `v2.38AV` asignó a Islas Caimán — `8TQ` / Joby Aviation / ISIN `KYG651631007` / RCS-equivalente pendiente.

## El registro caimanés: mismo tipo de hallazgo estructural que Suiza

Fuentes jurídicas de referencia (Conyers, Mourant — despachos líderes en derecho offshore, citados literalmente): **"no hay obligación general de que una `exempted company` presente estados financieros públicamente"** en las Islas Caimán. Solo las entidades reguladas por CIMA (bancos, gestoras de fondos) deben depositar cuentas auditadas, y esas cuentas **tampoco se hacen públicas** — quedan solo ante el regulador. El portal oficial (`ciregistry.ky`, comprobado en vivo, responde `200`) permite gestionar la presentación de la declaración anual (`annual return`) pero no publica ninguna cifra financiera. Es, por diseño legal, una jurisdicción sin divulgación pública — el mismo tipo de hallazgo ya documentado para Suiza (`v2.38AG`), aún más absoluto: en Suiza al menos bancos y cotizadas divulgan; en Caimán, ni eso.

## El hallazgo real que cambia la pregunta: esta empresa no es realmente "de Caimán"

Antes de cerrar, se comprobó si la empresa detrás del ticker `8TQ` tenía alguna otra vía real. Resultado, verificado en vivo contra el EDGAR de la SEC:

- La ISIN `KYG651631007` lleva el prefijo `KY` porque la entidad se emitió originalmente como una SPAC caimanesa (**"Reinvent Technology Partners"**, confirmado como nombre anterior en el propio registro de la SEC).
- Tras la fusión de 2021, la empresa real y actual — **Joby Aviation, Inc.** — está **domiciliada en Delaware** (`state-of-incorporation: DE`, confirmado en vivo vía `sec.gov/cgi-bin/browse-edgar`), con sede operativa en Santa Cruz, California, y reporta regularmente a la SEC (CIK `0001819848`, código SIC `3721` "AIRCRAFT", último 10-K real presentado).
- El censo de 43.089 empresas de este proyecto **ya contiene la acción real de Joby Aviation** bajo un `asset_id` distinto: `U04441` (ticker `JOBY`, NYSE, país `USA`) — y esa fila **ya tiene su CIK de la SEC resuelto** desde `v2.38D` (`US_SEC_CIK_RESOLVED`), pero **nunca ha pasado por la extracción real de fundamentales** de `v2.38G` (no aparece en `us_sec_fundamental_features_v2_38g.csv`).

En otras palabras: `8TQ` (Xetra) y `JOBY` (NYSE, `U04441`) son la misma empresa real vista desde dos cotizaciones distintas del mismo censo. El prefijo `KY` del ISIN refleja el historial de la SPAC, no la realidad operativa ni regulatoria actual de la empresa. Investigar el registro caimanés para esta empresa sería una vía muerta por diseño (nunca habrá cifras públicas ahí); la vía real y ya parcialmente construida en este proyecto es el pipeline de la SEC que ya identifica a Joby Aviation, simplemente todavía no le ha extraído fundamentales reales.

## Qué NO hace este bloque

No modifica `v2.38AV` (la clasificación "Islas Caimán" para el ISIN sigue siendo técnicamente correcta como dato de emisión, no se reescribe con retroactividad). No ejecuta ninguna extracción de fundamentales de la SEC para `U04441` — eso sería un bloque nuevo y explícito, no una tarea de registro europeo, y se deja a decisión del usuario. No toca ningún ratio, feature de crecimiento ni matriz de candidatos.

## Seguridad y alcance

Sin scripts, sin credenciales, sin cuentas creadas. Toda la evidencia (fuentes jurídicas citadas, respuesta en vivo de `ciregistry.ky`, datos reales del EDGAR de la SEC) comprobada antes de cerrar. Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_CAYMAN_ISLANDS_REGISTRY_RESEARCH_NO_VIABLE_FREE_SOURCE_STRUCTURAL`.** Cierra la investigación de registro para los 5 países nuevos revelados por `v2.38AV` (Luxemburgo resuelto en `v2.38AW`/`v2.38AX`; Bulgaria, Liechtenstein y Malta cerrados sin vía en `v2.38AY`; Islas Caimán cerrado aquí). Queda documentado un hallazgo real y accionable para una decisión futura del usuario: extender el pipeline de fundamentales de EE. UU. (`v2.38G`) a Joby Aviation (`U04441`), ya identificado pero nunca procesado.
