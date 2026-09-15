# Scout Finance v2.39D - Clean Windows install validation checklist
# Run manually in PowerShell from a clean folder.

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/ikeritu/Scout-Finance.git"
$Branch = "phase9b-global-enrichment-v2-38b"
$Target = "$env:USERPROFILE\ScoutFinanceCleanInstall"

git clone --branch $Branch $RepoUrl $Target
cd "$Target"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m py_compile app_v2_37.py
python -m py_compile src\ui_v2_37\global_ranking.py
.\run_local_ui_v2_37.bat
# Open http://localhost:8501 and verify "Ranking global (experimental)" loads.
