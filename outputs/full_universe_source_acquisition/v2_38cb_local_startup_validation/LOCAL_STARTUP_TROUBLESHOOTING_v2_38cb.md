# Local Startup Troubleshooting v2.38CB

## `fatal: not a git repository`

You are probably in `C:\Users\ikeri` instead of the project folder.

```powershell
cd "D:\Proyectos\💰 Scout Finance"
git status
```

## Python Missing

Install Python 3 and make sure `python` is available in PowerShell:

```powershell
python --version
```

## Dependencies Missing

Install the project requirements:

```powershell
python -m pip install -r requirements.txt
```

For the minimal UI path, this also works:

```powershell
python -m pip install -r requirements-ui-v2_28.txt
```

## Streamlit Does Not Start

Run the local launcher:

```powershell
.\run_local_ui_v2_37.bat
```

If port `8501` is occupied, close the previous Streamlit process or run Streamlit manually on another port:

```powershell
python -m streamlit run app_v2_37.py --server.address localhost --server.port 8502
```

## Required Output Missing

Stop and inspect which phase output is missing. Do not fabricate replacement ranking data. Re-run the corresponding offline builder only when its inputs are present.

## Reminder

The ranking screen is for local research only. It is not financial advice, not a buy/sell/hold signal, and not connected to brokers.
