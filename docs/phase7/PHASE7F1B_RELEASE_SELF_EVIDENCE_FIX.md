# Scout Finance — Fase 7F.1b: release self-evidence fix

## Problema

La release v0.7 no incluía dentro de `releases/v0.7/outputs/scouting/` el resumen e informe de empaquetado 7F, porque esos archivos se generan al final del empaquetado.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m src.fix_phase7f1b_release_self_evidence
```

## Validar fix

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7f1b_release_self_evidence.py
```

## Revalidar integridad 7F.1

```powershell
.\.venv\Scripts\python.exe -m src.validate_phase7f1_release_v07_integrity
.\.venv\Scripts\python.exe scripts/check_phase7f1_release_v07_integrity.py
```
