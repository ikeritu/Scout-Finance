# v2.32F — cierre y freeze final de la interfaz local

Estado esperado: **PASS · roadmap 6/6 · versión estable congelada**.

Este cierre acumula el arranque real v2.32A y el paquete operativo v2.32E, que a su vez repite los recorridos reales, la revisión visual/responsive, accesibilidad y los cierres históricos de la UI.

## Evidencias

- `closure_report.json`: resultado reproducible del gate final.
- `releases/MANIFEST_v2.32F_local_ui_final_freeze.json`: hashes de los archivos congelados.
- `releases/FREEZE_REPORT_v2.32F_local_ui_final_freeze.md`: alcance, límites y política posterior.
- `VERSION_LOCAL_UI.md`: ficha breve de la línea estable.

## Reproducir

```powershell
.\.venv\Scripts\python.exe tests\qa_final_closure_v2_32f.py `
  --json-output outputs\local_ui\v2_32f_final_closure\closure_report.json
```

El gate no modifica el dataset ni los pointers. El scoring productivo permanece sin autorización y `allow_ranking=false`.
