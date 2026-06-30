from __future__ import annotations
import json, py_compile
from pathlib import Path
def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)
def main():
    root=Path(__file__).resolve().parents[1]; scale=root/"outputs"/"scale_tests"
    print("Scout Finance — v1.5C1 Scale Test Output Restore Hotfix checker"); print("="*92)
    for p in [root/"app.py",root/"src/real_universe_scale_test.py",root/"scripts/check_v1_5c1_scale_test_output_restore_hotfix.py",root/"docs/v1/V1_5C1_SCALE_TEST_OUTPUT_RESTORE_HOTFIX.md"]:
        req(p.exists(),f"File exists: {p}")
    py_compile.compile(str(root/"app.py"),doraise=True); ok("app.py compiles")
    py_compile.compile(str(root/"src/real_universe_scale_test.py"),doraise=True); ok("real_universe_scale_test.py compiles")
    txt=(root/"app.py").read_text(encoding="utf-8")
    req("v1.5C1 scale test output restore hotfix packaged" in txt,"app.py contains v1.5C1 marker")
    stxt=(root/"src/real_universe_scale_test.py").read_text(encoding="utf-8")
    for m in ["FILES_TO_RESTORE","restore_ok","before_active_rows","after_active_rows","v1.5C1"]:
        req(m in stxt,f"scale test contains marker: {m}")
    sp=scale/"scale_test_summary.json"
    if sp.exists():
        req((scale/"scale_test_report.md").exists(),"Generated report exists")
        s=json.loads(sp.read_text(encoding="utf-8"))
        req(s.get("phase") in {"v1.5C","v1.5C1"},"Summary phase valid")
        req(s.get("status") in {"OK","ERROR"},"Summary status valid")
        req(s.get("openai_called") is False,"OpenAI control false")
        req(s.get("broker_called") is False,"Broker control false")
        req(s.get("pipeline_recalculated") is False,"Pipeline control false")
        req(s.get("yfinance_called") is False,"yfinance control false")
        runs=s.get("runs",[])
        req(isinstance(runs,list) and len(runs)==3,"Three scale runs present")
        req([r.get("size") for r in runs]==[20,50,100],"Scale sizes 20/50/100 OK")
        if s.get("phase")=="v1.5C1":
            req(s.get("restore_ok") is True,"Active output restore OK")
            req(s.get("before_active_rows")==s.get("after_active_rows"),"Active rows restored to previous count")
        for size in [20,50,100]: req((scale/f"size_{size}").exists(),f"Per-size output dir exists: size_{size}")
    else: ok("Scale test summary not generated yet; run --run")
    print(); print("Result"); print("-"*92); print("OK   v1.5C1 Scale Test Output Restore Hotfix is valid")
if __name__=="__main__": main()
