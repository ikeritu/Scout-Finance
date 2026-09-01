# Scout Finance v2.38B — contrato de enriquecimiento global

Fecha: 2026-09-01. Base inmutable: tag `v2.38A_PHASE9A_GLOBAL_UNIVERSE_AUDITED`, commit `6b5230a`.

## Alcance

La fase conserva las 43.089 filas del censo y solo permite planificar adquisición automática para las 21.165 elegibles. No reclasifica excluidos, revisables o bloqueados. Cada lote se limita a 500 activos y toda ejecución real requiere `--execute`, credencial cuando corresponda y un adaptador autorizado.

## Guardas

- Credenciales exclusivamente mediante variables de entorno.
- Datos brutos y datos con licencia fuera de Git.
- Escritura futura reanudable y atómica por activo.
- Símbolos ambiguos bloqueados; no se permiten aproximaciones por nombre.
- Valores ausentes permanecen ausentes; no se permiten valores sintéticos.
- No se autoriza scoring, ranking, recomendaciones ni fase 9C.
- Ninguna suscripción o gasto puede contratarse automáticamente.

## Criterio de lote

Un activo es `READY_FOR_CONTROLLED_BATCH` solo si es elegible, tiene identidad completa y su símbolo de proveedor está resuelto. Esto produce 42 JPX ya verificados por coincidencia exacta en v2.33G y 696 TWSE deterministas. Los otros 3.659 JPX requieren consulta individual al catálogo y coincidencia exacta de nombre. Estados Unidos permanece `USER_ACTION_REQUIRED` hasta disponer de cuenta, condiciones de almacenamiento confirmadas y piloto real.
