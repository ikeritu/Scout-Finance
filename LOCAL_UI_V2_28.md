# Scout Finance v2.28 — UI local estable

Esta es la interfaz local segura y recomendada para explorar el universo operativo de Scout Finance.

## Inicio rápido en Windows

### Instalación automática recomendada

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_local_ui_v2_29a.ps1
```

El script crea `.venv`, instala únicamente las dependencias necesarias y valida Python, archivos, pointers, dataset y estado fail-closed. Para instalar y abrir la UI directamente:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_local_ui_v2_29a.ps1 -Launch
```

### Instalación manual

1. Clona o actualiza el repositorio.
2. Abre PowerShell en la carpeta del proyecto.
3. Crea el entorno si todavía no existe:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Inicia la interfaz con doble clic en `run_local_ui_v2_28.bat`, o ejecuta:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_v2_28.py
```

Streamlit mostrará una dirección local, normalmente `http://localhost:8501`.

## Qué puedes hacer

- comprobar el estado operativo verificado por pointers;
- buscar y filtrar los 43.089 instrumentos del universo;
- consultar identidad, metadatos y linaje de un activo;
- crear watchlists locales con etiquetas y notas;
- descargar watchlists como CSV seguro;
- generar informes de universo y watchlists en Markdown o HTML;
- abrir, tras confirmación explícita, el diagnóstico de preparación de datos.

## Límites importantes

- El scoring productivo no está autorizado.
- No existe ranking de inversión operativo.
- El diagnóstico mide calidad y cobertura de datos, no atractivo financiero.
- No hay recomendaciones, señales, asignación de cartera ni acciones de broker.
- La interfaz no llama a OpenAI, yfinance, proveedores o pipelines al arrancar.

## Datos locales

Las watchlists se guardan en `data/watchlists/`. Están excluidas de Git para evitar publicar notas o listas personales. Cada actualización crea una copia `.json.bak` recuperable.

## Pantallas

| Pantalla | Función |
|---|---|
| Inicio / Estado | Universo, scoring y mantenimiento |
| Universo | Búsqueda, filtros, paginación y selección |
| Watchlists | Listas, notas, etiquetas y exportación |
| Score Explorer | Estado fail-closed y diagnóstico confirmado |
| Informes y exports | Markdown/HTML y manifiestos |
| Detalle de activo | Identidad, metadatos, linaje y listas |
| Mantenimiento | Estado técnico de solo lectura |
| Ayuda y límites | Capacidades y restricciones |

## Solución de problemas

- **No abre la aplicación:** instala dependencias con el comando del paso 3.
- **Catálogo no disponible:** comprueba que el dataset apuntado existe y no ha cambiado; la UI falla de forma cerrada ante un SHA incorrecto.
- **No aparece el diagnóstico:** confirma la casilla en Score Explorer. También debe coincidir su SHA-256 y número de filas.
- **No aparecen rankings:** es el comportamiento correcto mientras `allow_ranking=false`.
- **Watchlist dañada:** recupera la copia contigua terminada en `.json.bak`.

## Validación

```powershell
.\.venv\Scripts\python.exe tests\qa_catalog_watchlist_ui_v2_28c.py
.\.venv\Scripts\python.exe tests\qa_score_reports_ui_v2_28d.py
.\.venv\Scripts\python.exe tests\qa_ux_accessibility_v2_28e.py
.\.venv\Scripts\python.exe tests\qa_local_ui_closure_v2_28f.py
```

La entrada heredada `app.py` permanece intacta. Para esta versión estable usa siempre `app_v2_28.py`.
