#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(path):
 result=subprocess.run([sys.executable,str(ROOT/path)],cwd=ROOT,capture_output=True,text=True)
 if result.returncode:raise AssertionError(f"{path} failed: {result.stdout} {result.stderr}")
 return result.stdout.strip()
def main():
 expected=("app_v2_28.py","LOCAL_UI_V2_28.md","run_local_ui_v2_28.bat","src/ui_v2_28/adapters.py","src/ui_v2_28/catalog.py","src/ui_v2_28/watchlists.py","src/ui_v2_28/scoring.py","src/ui_v2_28/reports.py","src/ui_v2_28/ui.py")
 missing=[path for path in expected if not (ROOT/path).is_file()]
 if missing:raise AssertionError(f"missing closure files: {missing}")
 app=(ROOT/"app_v2_28.py").read_text(encoding="utf-8");guide=(ROOT/"LOCAL_UI_V2_28.md").read_text(encoding="utf-8");ignore=(ROOT/".gitignore").read_text(encoding="utf-8")
 assert "Local Analyst UI · v2.28 · estable" in app and "app_v2_28.py" in guide
 assert "data/watchlists/*.json" in ignore and "app.py` permanece intacta" in guide
 results=[run(path) for path in ("tests/qa_catalog_watchlist_ui_v2_28c.py","tests/qa_score_reports_ui_v2_28d.py","tests/qa_ux_accessibility_v2_28e.py")]
 assert all(result.startswith("PASS:") for result in results)
 print("PASS: inventory/launcher/guide/private-watchlists/v2.28C-D-E-regression/stable-freeze");return 0
if __name__=="__main__":raise SystemExit(main())
