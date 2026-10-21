# v2.50M — Ejecutable de escritorio para Windows

Estado: `DESKTOP_LAUNCHER_COMPLETED`. Petición del usuario (2026-10-21): un ejecutable para el escritorio de Windows. Decisiones (preguntadas): un **lanzador `.exe` para este PC** (no un paquete autónomo) que abre una **ventana de aplicación propia**. No cambia la aplicación, sus datos ni su puntuación.

## Qué hay
- `desktop/ScoutFinanceLauncher.cs` → `Scout Finance.exe` (≈ 44 KB), un programa nativo de .NET Framework compilado con el compilador que trae Windows (C# 5, sin instalar nada, sin Python propio, sin PyInstaller). Sin ventana de consola.
- Flujo: busca el proyecto (variable `SCOUT_FINANCE_ROOT`, la carpeta del `.exe` y sus superiores, o `%LOCALAPPDATA%\ScoutFinance\root.txt`) → arranca `app_v2_37.py` con el `.venv` del proyecto, en `127.0.0.1`, en un puerto libre y en modo `headless` → muestra una pequeña pantalla de carga hasta que `/_stcore/health` responde → abre la ventana de aplicación (Chrome, o Edge si no hay Chrome, con `--app`, un perfil propio y una marca en la línea de comandos para reconocer sus procesos) → cuando no queda ningún proceso con esa marca, apaga el árbol de procesos del servidor (`taskkill /T /F`) y sale.
- Una sola instancia (mutex): un segundo intento avisa y no arranca otra copia.
- La clave de CoinGecko: se hereda del entorno; si solo está en el registro del usuario, se pasa únicamente al entorno del proceso de la aplicación. Nunca se escribe, se registra ni se muestra (el modo `--check` solo dice «present» o «absent»).
- `desktop/install_shortcut.ps1` (compila si hace falta, escribe `root.txt` y crea el acceso directo con icono en el escritorio; `-Rebuild`, `-Remove`), `desktop/build_launcher.ps1`, `desktop/make_icon.py` → `desktop/scout_finance.ico` (siete tamaños), `desktop/README.md` (guía de uso). Los `.ps1` llevan BOM (Windows PowerShell 5 lee bien los acentos) y el código se compila con `/codepage:65001`.
- El `.exe` está en `.gitignore`: se reconstruye desde el código.

## Hechos observados
Probado en el PC del usuario con la carpeta principal, la clave real y los datos reales:
- **Ciclo completo**: la ventana se abre a los 3 s; a los 25 s el lanzador sigue vivo y `health` responde `ok`; un segundo lanzamiento muestra el aviso y no arranca otro servidor; al cerrar la ventana, el lanzador sale en 3 s con código 0, el puerto deja de escuchar y no quedan procesos de Streamlit.
- La aplicación abierta por el lanzador ve la clave y los datos de siempre (contador de CoinGecko 752 de 8.000; botón de búsqueda activo).
- Tres fallos encontrados y corregidos durante la prueba: (1) `localhost` se resuelve primero a IPv6 y Streamlit solo escucha en IPv4, así que la comprobación de salud esperaba en vano hasta el límite de 120 s (ahora todo va por `127.0.0.1`); (2) la opción `--disable-background-mode` hacía que Chrome se cerrara a los pocos segundos (se probó en cuatro variantes: solo esa lo hacía) y se quitó; (3) en el PC de pruebas una ventana de Edge en un perfil nuevo se cerraba sola a los ~7 s, sin error registrado, mientras Chrome aguantaba: por eso se prueba Chrome antes que Edge. El comportamiento de Edge como alternativa no está verificado.
- No se tocó la aplicación que el usuario pudiera tener abierta por su cuenta: el lanzador usa su propio puerto y solo detiene su propio servidor.

**Pruebas** (`tests/qa_desktop_launcher_v2_50m.py`, 5 casos): la aplicación que arranca y que existe, solo `127.0.0.1`, sin consola, marca y perfil, Chrome antes que Edge, parada del árbol de procesos y mutex; la clave no se escribe en ningún sitio; solo sintaxis de C# 5 y `.ps1` con BOM; el icono con todos los tamaños; y, en Windows con el compilador, una **compilación real** cuyo `--check` con una clave FALSA comprueba que el informe dice que hay clave pero nunca su valor. Se comprobó por mutación (8 mutaciones, todas detectadas) que las pruebas fallan si se usa `localhost`, vuelve la opción de segundo plano, se escribe la clave en el registro o en el informe, no se mata el árbol de procesos, se apunta a la aplicación antigua, se usa sintaxis de C# 6 o se quita la página de códigos. El ciclo de la ventana necesita un escritorio y se verificó a mano (arriba).

## Límites
- Solo funciona en este PC: necesita la carpeta del proyecto y su `.venv`. Para llevarlo a otro equipo habría que hacer un paquete autónomo (no se hizo: unos 500 MB, frágil con Streamlit, y la clave y los datos habría que configurarlos allí).
- Necesita Chrome o Edge. Con un navegador sin soporte de `--app` (o ninguno) avisa y no arranca.
- Si se cierra el `.exe` a la fuerza, el servidor se apaga al terminar el proceso (controlador de salida); si el sistema lo mata, puede quedar un servidor huérfano en un puerto aleatorio hasta reiniciar o cerrar su proceso `python.exe`.
- `INICIAR_SCOUT_FINANCE.bat` sigue arrancando `app_v2_28.py` (la versión antigua), no `app_v2_37.py`; el lanzador nuevo sí usa la actual. Está sin tocar a la espera de decisión.
