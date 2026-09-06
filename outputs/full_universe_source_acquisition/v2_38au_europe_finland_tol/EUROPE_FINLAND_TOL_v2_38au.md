# v2.38AU — Finlandia: el mejor código de sector encontrado en todo este esfuerzo, con descripción en inglés incluida

Fecha: 2026-09-06. Alcance: continuar el ataque al hueco de sector europeo con Finlandia (5/689 activos), el país donde `v2.38AF` ya confirmó una laguna real de GLEIF (0/5 registros para ISIN finlandeses).

## La mejor fuente oficial encontrada hasta ahora

El PRH (Oficina finlandesa de patentes y registro) publica una API de datos abiertos real (`avoindata.prh.fi/opendata-ytj-api/v3`), licencia CC BY 4.0, sin cuenta ni clave. A diferencia de **todos** los países anteriores, esta API devuelve el código TOL 2008 (la clasificación finlandesa, alineada con NACE Rev.2) **con su descripción ya traducida al inglés** en la propia respuesta — confirmado en vivo para Nokia Oyj: código `70100` con descripciones en finés, sueco **e inglés** ("Activities of head offices"). Ninguna tabla de traducción propia fue necesaria.

## Dos problemas reales de identidad resueltos en vivo, no asumidos

1. **Sin número de registro conocido**: al no tener GLEIF ningún registro para Finlandia, no había un identificador previo — hubo que buscar por nombre desde cero, con los mismos riesgos de nombre mal transliterado por Xetra ya vistos en otros países, pero con dos giros nuevos y reales:
   - **Transliteración real de vocales finlandesas**: `"SRV YHTIOET OYJ"` es la transliteración ASCII de Xetra del nombre real `"SRV Yhtiöt Oyj"` — la o-diéresis renderizada como el dígrafo "OE", la misma convención alemana ya vista en nombres alemanes/austriacos/suizos, pero nunca antes revertida. `normalize_full()`/`normalize_core()` la revierten antes de comparar.
   - **La búsqueda del API es literal, no tolerante a espacios/guiones**: comprobado en vivo que buscar `"UPM KYMMENE"` (con espacio, como escribe Xetra) devuelve 0 resultados, mientras que `"UPM-Kymmene"` (con guion real) sí — la solución adoptada es buscar siempre por la primera palabra normalizada (segura frente a cualquier separador interno), y **paginar todos los resultados** (confirmado en vivo: una sola palabra común como "NOKIA" puede devolver 991 resultados no relacionados).

2. **Ambigüedad real por nombres comerciales históricos**: comprobado en vivo que "Nordea Bank Abp" comparte, tras eliminar el sufijo legal, una colisión con **cuatro entidades distintas y no relacionadas** que llevan un nombre comercial auxiliar genérico "Nordea Bank" (sin sufijo) heredado de la histórica fusión Merita/Nordea de 2001. La solución real: **solo se compara contra el nombre oficial actual/paralelo (tipos PRH "1"/"2"), nunca contra un nombre comercial auxiliar (tipos "3"/"4")** — confirmado en vivo que esto resuelve limpiamente el caso.

3. **Colisión real Oy vs. Oyj**: comprobado en vivo que "SRV Yhtiöt Oy" (privada) y "SRV Yhtiöt Oyj" (pública) son dos empresas finlandesas reales y activas, distintas solo por su forma jurídica — eliminar ambos sufijos como si fueran intercambiables (como hacían otros países) crearía una colisión falsa. La solución: comparar primero manteniendo el sufijo legal real (`normalize_full`), y solo recurrir a la versión sin sufijo (`normalize_core`) cuando Xetra registró un sufijo extranjero incorrecto (como "Corp." para UPM-Kymmene) y la comparación con sufijo no encuentra nada.

## Resultado real

**5/5 empresas finlandesas con código TOL real — cobertura perfecta, 0 errores, 0 ambigüedades**, verificado con los mismos IDs de negocio confirmados manualmente antes de escribir el script. Nokia Oyj→`70100` "Activities of head offices", UPM-Kymmene Oyj→`17120` "Manufacture of paper and paperboard", Nordea Bank Abp→`66190` "Other activities auxiliary to financial services...", SRV Yhtiöt Oyj→`41000` "Construction of residential and non-residential buildings", Sampo Oyj→`64210` "Activities of holding companies".

## Salvaguardas

Bloqueado por defecto; requiere `--execute` (sin credencial). 11 pruebas offline, incluidas dos que reproducen exactamente los casos reales de colisión Oy/Oyj y de nombres comerciales Nordea/Merita. Sin scoring, sin ranking, sin recomendaciones.

**Estado del bloque: `COMPLETED_EUROPE_FINLAND_TOL`.** Alimenta la décima reconstrucción de `v2.38AM`. Finlandia se convierte en el segundo país (tras Bélgica) con cobertura de industria perfecta, y el único con descripciones nativas en inglés directamente desde la fuente oficial.
