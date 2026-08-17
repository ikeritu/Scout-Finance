# v2.32E — paquete operativo de la interfaz local

Gate de entrega para usuarios Windows sin conocimientos técnicos.

## Entregables

- `INICIAR_SCOUT_FINANCE.bat`: acceso único por doble clic, preparación automática en el primer uso y verificación fail-closed en los siguientes.
- `GUIA_SCOUT_FINANCE.md`: inicio, cierre, flujo recomendado, FAQ, copia de seguridad y recuperación.
- alias histórico `run_local_ui_v2_28.bat` y setup PowerShell compatibles.
- `package_report.json`: hashes del paquete, estado de los gates y evidencia de que QA no altera datos ni pointers.

## Reproducir el gate

```powershell
.\.venv\Scripts\python.exe tests\qa_operational_package_v2_32e.py `
  --json-output outputs\local_ui\v2_32e_operational_package\package_report.json
```

El gate acumula v2.28F y v2.32D. El universo permanece en 43.089 filas; el scoring productivo y los rankings continúan bloqueados.
