from __future__ import annotations
from pathlib import Path
import json

PHASE="v1.0E"

def root(): return Path(__file__).resolve().parents[1]
def ok(m): print("OK   "+m)
def fail(m):
    print("FAIL "+m)
    raise SystemExit(1)
def require(c,m): ok(m) if c else fail(m)
def require_file(p): require(p.exists(),f"File exists: {p}")

def main():
    r=root()
    out=r/"outputs"/"scouting"
    print("Scout Finance — v1.0E User Manual checker")
    print("="*92)
    files=[
        r/"docs"/"USER_GUIDE.md",
        r/"docs"/"QUICKSTART.md",
        r/"docs"/"SAFETY_LIMITS.md",
        r/"docs"/"v1"/"V1_0E_USER_MANUAL.md",
        r/"scripts"/"check_v1_0e_user_manual.py",
    ]
    for p in files:
        require_file(p)
    checks={
        "USER_GUIDE.md":["Finalidad","Flujo completo","revisión manual","final_review_pack","No es un asesor financiero"],
        "QUICKSTART.md":["Arranque rápido","Ver candidatos","Generar pack final","Validar candidate freeze"],
        "SAFETY_LIMITS.md":["No es asesoramiento financiero","No trading automático","IA real desactivada","Decisión humana obligatoria"],
    }
    for name, terms in checks.items():
        text=(r/"docs"/name).read_text(encoding="utf-8")
        for term in terms:
            require(term.lower() in text.lower(),f"{name} contains: {term}")
    out.mkdir(parents=True,exist_ok=True)
    summary={
        "phase":PHASE,
        "title":"User Manual / Operating Guide",
        "version":"v1.0.0-candidate-user-manual-e",
        "status":"OK",
        "files":[str(p.relative_to(r)) for p in files],
        "openai_called":False,
        "api_called":False,
        "yfinance_called":False,
        "pipeline_recalculated":False,
        "app_modified":False,
        "filters_modified":False,
        "release_modified":False,
        "next":"v1.0F — Final Documentation Freeze"
    }
    (out/"v1_0e_user_manual_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    report=["# v1.0E — User Manual / Operating Guide","","Status: **OK**","","## Files",""]
    for f in summary["files"]:
        report.append(f"- `{f}`")
    report += ["","## Safety","","- OpenAI called: False","- API called: False","- yfinance called: False","- Pipeline recalculated: False",""]
    (out/"v1_0e_user_manual_report.md").write_text("\n".join(report),encoding="utf-8")
    print()
    print("Result")
    print("-"*92)
    print("OK   v1.0E User Manual is valid")

if __name__=="__main__":
    main()
