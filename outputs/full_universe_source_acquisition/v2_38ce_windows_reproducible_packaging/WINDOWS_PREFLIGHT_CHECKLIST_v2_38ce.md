# Windows Preflight Checklist v2.38CE

- Open PowerShell.
- Run `cd "D:\Proyectos\💰 Scout Finance"`.
- Run `git status` and confirm the branch is `phase9b-global-enrichment-v2-38b`.
- Run `python --version`.
- Run `python -m pip install -r requirements.txt` if dependencies are missing.
- Run `.\run_local_ui_v2_37.bat`.
- Open `http://localhost:8501`.
- Confirm `Inicio` loads.
- Open `Ranking global (experimental)`.
- Confirm the ranking loads with the expected warning/disclaimer context.
- Review known warnings from v2.38CD before using the app for research.
