from __future__ import annotations
import py_compile
import re
from pathlib import Path

def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)

def main():
    root=Path(__file__).resolve().parents[1]
    app=root/"app.py"

    print("Scout Finance — v1.6B1 Remove Duplicate Main Invocation Hotfix checker")
    print("="*92)

    req(app.exists(), f"File exists: {app}")
    text=app.read_text(encoding="utf-8")

    for marker in [
        "v1.6B1 remove duplicate main invocation hotfix packaged",
        "v1.6B fundamentals UI integration packaged",
        "v1.6B FUNDAMENTALS UI INTEGRATION HELPERS",
        "_sf16b_render_fundamentals_block",
        "Fundamentales",
        "Revenue",
        "manual_fundamentals.csv",
    ]:
        req(marker in text, f"app.py contains marker: {marker}")

    req('if __name__ == "__main__":' in text, "Proper __main__ guard exists")
    req(re.search(r'if __name__ == "__main__":\s*\n\s*main\(\)', text) is not None, "Proper guarded main call exists")

    bare_main_tuple = re.search(r'(?m)^\s*main\(\),\s*$', text)
    req(bare_main_tuple is None, "No bare duplicate main(), invocation remains")

    guarded_calls = len(re.findall(r'(?m)^\s*main\(\)\s*$', text))
    req(guarded_calls == 1, f"Exactly one executable bare-line main() call remains ({guarded_calls})")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")

    print()
    print("Result")
    print("-"*92)
    print("OK   v1.6B1 Remove Duplicate Main Invocation Hotfix is valid")

if __name__=="__main__":
    main()
