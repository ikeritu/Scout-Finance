# v2.33B — política de elegibilidad

Estado: **PASS · 43.089/43.089 filas con decisión · scoring bloqueado**.

## Artefactos

- `eligibility_policy_v2_33b.json`: política, reglas y conteos.
- `eligibility_census_v2_33b.csv.xz`: decisión y motivo por cada fila del universo.
- `ELIGIBILITY_REPORT_v2_33b.md`: lectura ejecutiva y límites.

## Reproducir

```powershell
.\.venv\Scripts\python.exe scripts\classify_eligibility_v2_33b.py `
  outputs\full_universe_source_acquisition\v2_33a_universe_audit\universe_row_audit_v2_33a.csv.xz `
  outputs\full_universe_source_acquisition\v2_33b_eligibility_policy
```

“Elegible para enriquecimiento” significa que se buscarán datos financieros para ese activo. No significa que sea una oportunidad ni que pueda entrar todavía en un ranking.
