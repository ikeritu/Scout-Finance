# Scout Finance v2.33B2 — corrección de falsos candidatos

## Motivo

El preflight de precios detectó instrumentos que v2.33B había aceptado por confiar demasiado en el tipo declarado por el proveedor. Se ha repetido el control sobre toda la población elegible.

## Reclasificaciones

| Motivo | Filas | Decisión |
|---|---:|---|
| Fondo o trust | 697 | Revisión |
| Fuente SGX con esquema sospechoso | 358 | Reparación previa |
| SPAC o sociedad de adquisición | 216 | Revisión |
| ETF/ETN/producto cotizado | 17 | Exclusión |
| Warrant, right o unit | 5 | Revisión |
| Registro de prueba o marcador | 4 | Exclusión |
| Acción preferente | 2 | Exclusión del motor de acciones comunes |

Total: **1.299 filas refinadas**.

## Nueva población

| Estado | Antes | Después |
|---|---:|---:|
| Elegible para enriquecimiento | 23.888 | 22.589 |
| Excluido | 10.409 | 10.432 |
| Revisión o reparación | 8.792 | 10.068 |

No se elimina ninguna fila del catálogo original. Los casos dudosos conservan su identidad y un motivo específico.

## Validación posterior

La muestra de precios de 240 activos se ha regenerado con el nuevo censo. Las 240 filas superan el preflight de elegibilidad y SGX ya no entra en la adquisición automática.

Scoring, rankings y recomendaciones continúan bloqueados.
