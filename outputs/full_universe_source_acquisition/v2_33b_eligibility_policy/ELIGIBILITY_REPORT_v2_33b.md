# Scout Finance v2.33B — definición de activos elegibles

## Decisión completa

| Estado | Activos | Consecuencia |
|---|---:|---|
| Elegible para enriquecimiento financiero | 23.888 | Buscar precios, históricos y fundamentales |
| Excluido del universo de oportunidades de acciones | 10.409 | ETF, ETC y ETN; requieren otra metodología |
| Revisión de instrumento sin clasificar | 8.765 | No se incorpora hasta resolver su tipo |
| Revisión de tipo específico del proveedor | 20 | Requiere regla explícita |
| Revisión de vehículo condicional | 7 | Requiere decisión individual o por clase |

Las 43.089 filas reciben una decisión y un motivo. Ninguna se elimina del catálogo original.

## Qué entra en el grupo de enriquecimiento

Se admiten como candidatos las acciones ordinarias y los recibos depositarios ADR/DR cuya identidad operativa contiene, como mínimo:

- ticker;
- nombre de empresa;
- mercado;
- proveedor de origen.

Este filtro produce **23.888 candidatos**. Su inclusión solo autoriza buscar y validar datos; no presupone calidad financiera ni atractivo de inversión.

## Qué queda fuera

Los 10.409 ETF, ETC y ETN se excluyen del futuro ranking de acciones porque no pueden evaluarse correctamente con las mismas métricas que una empresa. Podrán recuperarse más adelante mediante un motor específico para fondos y productos cotizados.

Los 8.792 casos ambiguos quedan en revisión. No se fuerza su clasificación ni se les asigna una puntuación inventada.

## Cotizaciones cruzadas y duplicados

La fase v2.33A encontró 133 grupos de ISIN repetido, todos dentro del conjunto todavía no clasificado. v2.33B no los elimina automáticamente: un ISIN repetido puede ser una cotización legítima en otro mercado. La futura resolución debe conservar la empresa económica y diferenciar sus líneas de negociación.

## Condiciones pendientes para poder puntuar

Incluso un activo elegible para enriquecimiento seguirá bloqueado hasta disponer y validar:

1. precio actual y fecha;
2. histórico de precios;
3. estados financieros;
4. moneda normalizada;
5. sector o grupo comparable;
6. procedencia y fecha de cada dato.

## Garantías

- 43.089 filas decididas y trazables;
- dataset original y punteros sin cambios;
- ningún ranking generado;
- scoring productivo no autorizado;
- casos ambiguos mantenidos fuera del motor por defecto.
