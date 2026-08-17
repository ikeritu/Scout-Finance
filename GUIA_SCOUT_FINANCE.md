# Scout Finance — guía de uso en Windows

Scout Finance es una aplicación local para explorar de forma segura el universo operativo validado de 43.089 instrumentos. No envía órdenes, no recomienda inversiones y no habilita rankings productivos.

**Versión estable congelada:** `v2.32F — Local UI Final Freeze`. Para uso normal no es necesario ejecutar scripts ni modificar archivos: abre únicamente `INICIAR_SCOUT_FINANCE.bat`.

## Abrir la aplicación

Haz doble clic en **`INICIAR_SCOUT_FINANCE.bat`**.

### Primera vez

El iniciador crea automáticamente el entorno privado `.venv`, instala las dependencias y comprueba los archivos y datos operativos antes de abrir el navegador. Puede tardar unos minutos y necesita conexión a Internet. Mantén abierta la ventana negra durante todo el proceso.

### Veces siguientes

El iniciador comprueba primero la instalación, los pointers operativos, el SHA-256 del dataset, las 43.089 filas y el bloqueo del scoring. Solo abre la interfaz si todo es coherente.

Normalmente el navegador abrirá `http://localhost:8501`. Si no lo hace, copia esa dirección desde la ventana negra y pégala en el navegador.

## Cerrar Scout Finance

1. Cierra la pestaña del navegador.
2. Vuelve a la ventana negra.
3. Pulsa **Ctrl+C** y confirma si Windows lo solicita.

No cierres la ventana negra mientras estés usando la aplicación: ahí se ejecuta el servidor local.

## Flujo recomendado

1. Revisa **Inicio / Estado**.
2. Busca instrumentos en **Universo** y abre su detalle.
3. Guarda selecciones en **Watchlists**.
4. Genera archivos en **Informes y exports** cuando los necesites.
5. Usa **Score Explorer** solo como diagnóstico de datos y tras la confirmación explícita.

| Pantalla | Para qué sirve |
|---|---|
| Inicio / Estado | Ver el estado del universo, scoring y mantenimiento |
| Universo | Buscar, filtrar y seleccionar instrumentos |
| Detalle de activo | Revisar identidad, metadatos, linaje y listas |
| Watchlists | Organizar listas locales, etiquetas y notas |
| Score Explorer | Consultar el diagnóstico fail-closed, no rankings |
| Informes y exports | Crear Markdown, HTML, CSV y manifiestos |
| Mantenimiento | Consultar información técnica de solo lectura |
| Ayuda y límites | Recordar capacidades y restricciones |

## Tus listas y copias de seguridad

Las watchlists se guardan solo en `data\watchlists\`; no se publican en GitHub. Copia esa carpeta periódicamente a una ubicación segura para conservar listas, etiquetas y notas.

Cada actualización crea junto al archivo una copia terminada en `.json.bak`. Si una lista no abre, cierra Scout Finance, conserva ambos archivos, renombra el archivo dañado y quita `.bak` al nombre de la copia. Después vuelve a iniciar.

## Límites que debes conocer

- El scoring productivo no está autorizado y `allow_ranking=false`.
- No hay rankings, señales, recomendaciones ni asignación de cartera.
- El diagnóstico muestra calidad y cobertura de datos, no atractivo financiero.
- Al arrancar, la interfaz no llama a OpenAI, yfinance, brokers, proveedores ni pipelines.
- Un fallo de integridad bloquea la apertura; no se sustituuyen datos silenciosamente.

## Solución de problemas y preguntas frecuentes

### Windows dice que Python no está instalado

Instala Python 3.11 desde una fuente oficial, activa la opción para añadir Python a `PATH` y vuelve a hacer doble clic en `INICIAR_SCOUT_FINANCE.bat`.

### La primera instalación falla

Comprueba la conexión a Internet y que un antivirus o proxy no esté bloqueando Python. Ejecuta de nuevo el iniciador: reutilizará lo que ya se haya instalado y volverá a verificarlo.

### El navegador no se abre

Busca en la ventana negra la dirección local y abre `http://localhost:8501` manualmente. Si el puerto está ocupado, Streamlit mostrará otra dirección; usa la que aparezca allí.

### Aparece un error de integridad o SHA-256

La protección fail-closed ha detectado que falta un archivo o no coincide con el pointer operativo. No edites el dataset ni los JSON de pointer. Actualiza el repositorio desde la fuente aprobada y vuelve a iniciar.

### No aparecen rankings o puntuaciones de inversión

Es el comportamiento esperado. El scoring productivo permanece bloqueado y la aplicación no debe convertir el diagnóstico en ranking.

### Falta una watchlist o está dañada

Restaura la copia `.json.bak` como se explica en **Tus listas y copias de seguridad**. Si tienes una copia externa de `data\watchlists\`, restáurala con la aplicación cerrada.

### ¿Puedo cerrar la ventana negra?

Solo cuando termines. Pulsa Ctrl+C para detener el servidor de forma ordenada; cerrar únicamente la pestaña no detiene la aplicación.

### ¿Necesita Internet o envía mis datos?

Internet es necesario para instalar dependencias la primera vez. El uso normal es local; las watchlists permanecen en tu equipo y la aplicación no contacta proveedores al arrancar.

## Reinstalación segura

1. Cierra Scout Finance y copia `data\watchlists\` a una ubicación segura.
2. Elimina únicamente la carpeta `.venv`.
3. Vuelve a hacer doble clic en `INICIAR_SCOUT_FINANCE.bat`.

No borres `outputs`, los pointers JSON ni los datasets. Si el verificador sigue fallando, conserva el mensaje exacto para el soporte técnico.

## Uso avanzado

Preparar y verificar sin abrir:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_local_ui_v2_29a.ps1
```

Verificar una instalación existente:

```powershell
.\.venv\Scripts\python.exe scripts\verify_local_ui_install_v2_29a.py --root .
```

La entrada estable de la interfaz es `app_v2_28.py`. El antiguo `run_local_ui_v2_28.bat` se mantiene como alias compatible del nuevo iniciador.
