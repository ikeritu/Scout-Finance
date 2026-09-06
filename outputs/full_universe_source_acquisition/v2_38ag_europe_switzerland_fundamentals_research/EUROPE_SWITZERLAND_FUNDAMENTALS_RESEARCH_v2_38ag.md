# v2.38AG — Suiza: investigación de fundamentales (real, sin script nuevo)

Fecha: 2026-09-06. Alcance: investigar si existe alguna vía oficial gratuita para obtener fundamentales reales de las 29 empresas suizas (identidad y registro ya resueltos al 100% vía GLEIF en v2.38AF — dos autoridades de registro reales confirmadas, RA000548 y RA000549, con números de registro cantonal reales como CHE-100.136.893 para Holcim AG).

## Hallazgo estructural: Suiza no exige depositar cuentas anuales en el registro mercantil

**A diferencia de GB, Irlanda, Francia y Países Bajos** (todos con un régimen legal de depósito público de cuentas anuales, aunque con distinto grado de accesibilidad gratuita), **la legislación suiza no exige de forma general que las empresas depositen sus cuentas anuales en el registro mercantil (Handelsregister/Zefix) en absoluto**. Las empresas deben preparar sus cuentas conforme al Código de Obligaciones suizo, pero se presentan al órgano societario competente (p. ej. la junta de accionistas), no a un registro público. **La única excepción son bancos, entidades financieras y empresas cotizadas**, que deben depositar sus cuentas — pero no en el registro mercantil, sino a través del sistema de divulgación regulada de SIX Exchange Regulation, típicamente como documentos PDF publicados en el propio canal de la empresa o de la bolsa (comunicados "ad hoc"), no como datos estructurados en un API gubernamental abierto.

Esta es una diferencia estructural real, no una simple ausencia de herramienta técnica: mientras que GB/Irlanda/Francia/Países Bajos tienen un régimen de transparencia pública de cuentas (con distinto grado de accesibilidad gratuita ya investigado en cada caso), Suiza —al no formar parte de la UE/EEE— no tiene el mandato ESEF/iXBRL, y su propio derecho societario no exige depósito público de cuentas para la inmensa mayoría de las empresas.

## Zefix: API de registro real y gratuita, pero no relevante para fundamentales

Se investigó también **Zefix** (el índice central de empresas suizas, gestionado por la Oficina Federal de Justicia): tiene un **API REST real, documentado (Swagger/OpenAPI)**, y la propia Confederación confirma que **"no se ofrecen suscripciones"** (`"Es werden keine Abonnemente angeboten"`) — es decir, no es una fuente de pago. Sin embargo, **el acceso programático exige credenciales que se solicitan por correo** a `zefix@bj.admin.ch` (comprobado en vivo: una consulta real sin credencial devuelve `HTTP 401`), un proceso similar en espíritu al de UK Companies House pero sin registro de autoservicio inmediato.

**Esto es irrelevante para el objetivo de fundamentales**: Zefix es un registro de identidad/estado societario (igual que Companies House o la CRO irlandesa), **nunca ha publicado cifras financieras** — y la identidad de las 29 empresas suizas ya está completamente resuelta desde v2.38AF vía GLEIF, sin necesidad de credencial alguna. Solicitar acceso a Zefix no añadiría ningún fundamental real; solo enriquecería campos de identidad ya cubiertos. No se pide al usuario que solicite esta credencial, ya que no serviría al objetivo real de este bloque.

## Conclusión

**No existe ninguna vía oficial gratuita, estructurada y accesible para obtener fundamentales reales de empresas suizas** — no por falta de una herramienta técnica (como en Alemania, donde el dato podría existir pero el acceso está bloqueado), sino porque **el régimen legal suizo no exige, en general, la publicación pública de esas cifras**. Las empresas cotizadas sí divulgan sus cuentas, pero vía SIX Exchange Regulation en PDF, sin ningún dataset estructurado ni API abierto conocido — extraerlas exigiría scraping de comunicados individuales por empresa, prohibido por la política de este proyecto.

Ningún script de extracción de fundamentales se construye para Suiza. La identidad y el registro (29/29, dos autoridades reales confirmadas) ya están cerrados desde v2.38AF y no requieren ningún trabajo adicional.

## Seguridad y alcance

- Red real usada: solo consultas de solo lectura durante la investigación (páginas públicas, y una comprobación `curl` real contra el API de Zefix que confirmó el requisito de credencial con `HTTP 401`).
- Ninguna cuenta creada, ninguna credencial solicitada ni usada.
- Sin scraping, sin rodeos.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.

## Resumen frente a las jurisdicciones ya tratadas

| | GB | Irlanda | España | Alemania | Francia | Países Bajos | **Suiza** |
|---|---:|---:|---:|---:|---:|---:|---:|
| Activos | 40 | 17 | 15 | 413 | 53 | 44 | **29** |
| Identidad/registro resuelto | 29/40 | 8/17 | — | — | 18/53 | 36/44 | **29/29 (ya cerrado, v2.38AF)** |
| Fundamentales reales accesibles | Sí (2 empresas) | No | — | — | No | No | **No — causa estructural: sin obligación legal de depósito público** |

**Estado del bloque: `COMPLETED_EUROPE_SWITZERLAND_FUNDAMENTALS_RESEARCH_NO_LEGAL_DISCLOSURE_REGIME`.** Hallazgo distinto y más fundamental que en cualquier país anterior: no es un problema de acceso técnico, sino de que la propia ley suiza no exige la publicación que buscamos.
