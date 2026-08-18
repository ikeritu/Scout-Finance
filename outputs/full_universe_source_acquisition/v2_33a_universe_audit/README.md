# v2.33A — auditoría del universo operativo

Estado: **PASS · 43.089/43.089 filas auditadas · solo lectura**.

## Artefactos

- `audit_summary_v2_33a.json`: conteos, cobertura, tipos y duplicados candidatos.
- `universe_row_audit_v2_33a.csv.xz`: censo fila a fila con tipo normalizado y banderas de calidad.
- `AUDIT_REPORT_v2_33a.md`: conclusiones y límites de la fase.

## Reproducir

```powershell
.\.venv\Scripts\python.exe scripts\audit_universe_v2_33a.py `
  outputs\full_universe_source_acquisition\v2_30d_immutable_refresh_candidate\refresh_candidate_v2_30d.csv.xz `
  outputs\full_universe_source_acquisition\v2_33a_universe_audit
```

La auditoría no decide todavía qué instrumentos son elegibles. Esa política corresponde a v2.33B.
