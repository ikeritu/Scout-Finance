# v2.38B — global enrichment infrastructure

Estado: `BLOCKED_EXTERNAL_ACTIONS_AFTER_INFRASTRUCTURE_READY`.

Ejecutar:

```text
python scripts/build_global_acquisition_manifest_v2_38b.py
python tests/qa_phase9b_full_suite_v2_38b.py
python scripts/run_global_acquisition_v2_38b.py --market JPX --limit 50
```

La última orden es un dry-run. Toda adquisición real permanece bloqueada.
