# Scout Finance — versión de la interfaz local

## Versión estable

`v2.32F — Local UI Final Freeze`

Esta ficha corresponde exclusivamente a la interfaz local estable iniciada con `INICIAR_SCOUT_FINANCE.bat`. No reemplaza ni reescribe los freezes históricos de `app.py` ni las fases del pipeline de adquisición de datos.

## Estado congelado

- entrada estable: `app_v2_28.py`;
- acceso Windows: `INICIAR_SCOUT_FINANCE.bat`;
- universo operativo: 43.089 identidades únicas y 14/14 proveedores completos;
- watchlists: almacenamiento local privado con copia `.json.bak`;
- scoring productivo: no autorizado;
- rankings, recomendaciones, señales y acciones de broker: bloqueados;
- guía de usuario: `GUIA_SCOUT_FINANCE.md`;
- manifiesto verificable: `releases/MANIFEST_v2.32F_local_ui_final_freeze.json`.

## Política posterior al freeze

Los cambios futuros deben abrir una versión nueva, conservar el comportamiento fail-closed y superar de nuevo los gates de arranque real, recorridos de usuario, usabilidad, accesibilidad, empaquetado e integridad. No se deben sobrescribir datasets ni pointers operativos como parte de cambios de interfaz.
