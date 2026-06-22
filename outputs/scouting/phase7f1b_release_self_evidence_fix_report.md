# Scout Finance — Phase 7F.1b release self-evidence fix

Generated at: `2026-06-10T11:39:20+00:00`

## Status

- Status: **OK**
- Release directory: `C:\Users\ikeri\proyectos\Scout Finance\releases\v0.7`

## Problem fixed

The v0.7 release package was valid, but the 7F packaging summary/report were generated after the release evidence copy step and were not included inside:

```text
releases/v0.7/outputs/scouting/
```

## Copied files

- `outputs/scouting/phase7f_release_v07_packaging_summary.json`: copied=True exists=True
- `outputs/scouting/phase7f_release_v07_packaging_report.md`: copied=True exists=True

## Manifest changes

- ADDED_MANIFEST_ENTRY:outputs/scouting/phase7f_release_v07_packaging_summary.json
- ADDED_MANIFEST_ENTRY:outputs/scouting/phase7f_release_v07_packaging_report.md

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- release modified: `True`

## Next

```text
Re-run 7F.1 integrity validator.
```
