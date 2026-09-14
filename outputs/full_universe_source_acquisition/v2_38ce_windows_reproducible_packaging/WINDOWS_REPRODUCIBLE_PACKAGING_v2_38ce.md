# Windows Reproducible Packaging v2.38CE

Decision: `WINDOWS_PACKAGE_READY_WITH_WARNINGS`.

This phase defines a reproducible Windows local package through a manifest instead of creating a heavy ZIP. The repository already stores the required files, so the package is reproduced by checking out the branch and validating the manifest.

## Included

- Local app entry point and Windows launcher.
- Python requirements.
- Read-only global ranking UI module and watchlist support.
- v2.38BV ranking outputs required by the UI.
- v2.38BX-v2.38CD audit, readiness, startup, user-guide and diagnostics outputs.
- Current README, VERSION, CHANGELOG and roadmap.

## Excluded

- `.git/`
- `.env`
- `*.pyc`
- `__pycache__/`
- `*.log`
- `.pytest_cache/`
- `.streamlit/secrets.toml`
- `outputs/**/raw/**`

## Windows Start

```powershell
cd "D:\Proyectos\💰 Scout Finance"
git status
python --version
python -m pip install -r requirements.txt
.\run_local_ui_v2_37.bat
```

Open `http://localhost:8501` if the browser does not open automatically.

## Reproducibility

- Source phase: `v2.38CD`.
- Included files: 28.
- Total bytes: 3720215.
- ZIP created: `false`.

## Limitations

This is still a local release candidate package. The ranking remains experimental and the documented missing/degraded data from v2.38CD remains visible. This is not financial advice and does not enable broker actions.

Next recommended phase: `v2.38CF -- Streamlit visual smoke test`.
