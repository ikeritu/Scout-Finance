# Scout Finance para el escritorio de Windows

`Scout Finance.exe` es un lanzador pequeño (unos 44 KB, sin Python propio ni ventana negra). Al abrirlo:

1. arranca la aplicación con el `.venv` de tu proyecto, solo en tu equipo (`127.0.0.1`) y en un puerto libre;
2. abre una **ventana propia** (Chrome o Edge en modo aplicación, sin barra de direcciones ni pestañas);
3. cuando cierras esa ventana, **apaga el servidor** y se cierra solo.

Si ya está abierto, un segundo intento avisa «Scout Finance ya está abierto» y no arranca otra copia.

## Instalar el acceso directo
Desde la carpeta del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File desktop\install_shortcut.ps1
```

Compila `desktop\Scout Finance.exe` (con el compilador de .NET que trae Windows: no hay que instalar nada) y crea el acceso directo «Scout Finance» con su icono en el escritorio. Para recompilar después de cambiar el código: añade `-Rebuild`. Para quitar el acceso directo: añade `-Remove`.

## Requisitos
- La carpeta del proyecto con su `.venv` (se prepara una vez con `INICIAR_SCOUT_FINANCE.bat`). El `.exe` busca el proyecto a su lado o en una carpeta superior; si lo mueves, vuelve a ejecutar `install_shortcut.ps1`.
- Google Chrome o Microsoft Edge instalado. Se prefiere Chrome: en el PC donde se desarrolló, una ventana de Edge en un perfil nuevo se cerraba sola a los pocos segundos.
- La clave de CoinGecko sigue en tu variable de entorno de usuario `SCOUT_FINANCE_COINGECKO_API_KEY`. Si abres el acceso directo antes de que Windows la vea, el lanzador la lee del registro y la pasa solo al proceso de la aplicación; nunca la escribe ni la muestra.

## Si algo falla
- El registro de la aplicación está en `%LOCALAPPDATA%\ScoutFinance\launcher.log`.
- El perfil de la ventana (sin tus datos de navegación) está en `%LOCALAPPDATA%\ScoutFinance\app-window-profile`.
- `"Scout Finance.exe" --check informe.txt` escribe qué ve el lanzador (proyecto, entorno, navegador, si hay clave) sin mostrar la clave.
- Tus datos (notas, caché cifrada, lista de Revolut) siguen en la carpeta `data\` del proyecto, igual que antes.

Archivos: `ScoutFinanceLauncher.cs` (el código), `build_launcher.ps1`, `install_shortcut.ps1`, `make_icon.py` y `scout_finance.ico`. El `.exe` no se sube a git: se reconstruye.
