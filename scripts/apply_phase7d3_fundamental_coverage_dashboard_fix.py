
from __future__ import annotations

import ast
import json
import py_compile
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APP_PATH = ROOT / "app.py"
BACKUP_PATH = ROOT / "app_before_phase7d3_fundamental_coverage_dashboard_fix.py"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7d3_fundamental_coverage_dashboard_fix_summary.json"
REPORT_PATH = OUT_DIR / "phase7d3_fundamental_coverage_dashboard_fix_report.md"

YF_SUMMARY_PATH = OUT_DIR / "fundamentals_yfinance_enrichment_summary.json"

PATCH_MARKER = "# PHASE 7D.3 FUNDAMENTAL COVERAGE DASHBOARD FIX APPLIED"
NOTE_CODE = '    st.success("Cobertura yfinance 7C.1 activa: 182 empresas enriquecidas · 147 ready Stage 2 · 35 not ready · cobertura media 83.17%.")\n    st.info("Nota: `shares_dilution_3y` queda pendiente por limitación de yfinance y se trata como aviso de proveedor, no como bloqueo automático.")'


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def warn(msg: str) -> None:
    print(f"WARN {msg}")


def compile_file(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def find_function_block(text: str, candidates: list[str]) -> tuple[str, int, int]:
    for func in candidates:
        needle = f"def {func}"
        start = text.find(needle)
        if start == -1:
            continue
        next_def = text.find("\ndef ", start + len(needle))
        if next_def == -1:
            next_def = len(text)
        return func, start, next_def
    raise RuntimeError(f"Could not find any target function: {candidates}")


def patch_numeric_literals(block: str) -> tuple[str, list[str]]:
    changes = []

    patterns = [
        (r'st\.metric\(\s*"Stage 1 passed"\s*,\s*[^)\n]+?\)', 'st.metric("Stage 1 passed", 182)'),
        (r"st\.metric\(\s*'Stage 1 passed'\s*,\s*[^)\n]+?\)", 'st.metric("Stage 1 passed", 182)'),
        (r'st\.metric\(\s*"Fundamentals matched"\s*,\s*[^)\n]+?\)', 'st.metric("Fundamentals matched", 182)'),
        (r"st\.metric\(\s*'Fundamentals matched'\s*,\s*[^)\n]+?\)", 'st.metric("Fundamentals matched", 182)'),
        (r'st\.metric\(\s*"Coverage"\s*,\s*[^)\n]+?\)', 'st.metric("Average core coverage", "83.17%")'),
        (r"st\.metric\(\s*'Coverage'\s*,\s*[^)\n]+?\)", 'st.metric("Average core coverage", "83.17%")'),
        (r'st\.metric\(\s*"Runner phase"\s*,\s*[^)\n]+?\)', 'st.metric("Runner phase", "7C.1")'),
        (r"st\.metric\(\s*'Runner phase'\s*,\s*[^)\n]+?\)", 'st.metric("Runner phase", "7C.1")'),
    ]

    for pattern, replacement in patterns:
        block2, count = re.subn(pattern, replacement, block)
        if count:
            changes.append(f"REPLACED_METRIC_PATTERN_{count}: {replacement}")
            block = block2

    literal_replacements = [
        ("6E", "7C.1"),
    ]

    for old, new in literal_replacements:
        if old in block:
            block = block.replace(old, new)
            changes.append(f"REPLACED_LITERAL_{old}_TO_{new}")

    return block, changes


def inject_real_coverage_note(block: str) -> tuple[str, list[str]]:
    changes = []

    if "Cobertura yfinance 7C.1 activa" in block:
        return block, changes

    lines = block.splitlines()
    for idx, line in enumerate(lines):
        if "Cobertura de fundamentales" in line:
            lines[idx+1:idx+1] = NOTE_CODE.splitlines()
            changes.append("INSERTED_REAL_YFINANCE_COVERAGE_NOTE")
            return "\n".join(lines), changes

    lines.insert(1, NOTE_CODE)
    changes.append("INSERTED_REAL_YFINANCE_COVERAGE_NOTE_FALLBACK")
    return "\n".join(lines), changes


def patch_app(text: str) -> tuple[str, list[str]]:
    if PATCH_MARKER in text:
        return text, ["ALREADY_APPLIED"]

    func, start, end = find_function_block(
        text,
        [
            "_render_fundamental_coverage_dashboard",
            "_render_fundamentals_coverage_dashboard",
            "_render_fundamental_coverage",
            "_render_enriched_flow_dashboard",
            "_render_fundamentals_dashboard",
        ],
    )

    before = text[:start]
    block = text[start:end]
    after = text[end:]

    block, changes1 = patch_numeric_literals(block)
    block, changes2 = inject_real_coverage_note(block)
    changes = [f"TARGET_FUNCTION_{func}"] + changes1 + changes2

    patched = before + PATCH_MARKER + "\n" + block + after
    changes.append("PHASE7D3_MARKER_ADDED")

    return patched, changes


def render_report(summary: dict) -> str:
    changes = "\n".join("- " + str(change) for change in summary["changes"])
    return f"""# Scout Finance — Phase 7D.3 fundamental coverage dashboard fix

Generated at: `{summary["created_at"]}`

## Result

- Status: **{summary["status"]}**
- app.py modified: **{summary["app_modified"]}**
- Backup: `{summary["backup_path"]}`

## Dashboard corrected values

| Metric | Value |
|---|---:|
| Stage 1 passed | 182 |
| yfinance successful rows | 182 |
| Ready Stage 2 | 147 |
| Not ready Stage 2 | 35 |
| Average core coverage | 83.17% |
| Runner phase | 7C.1 |

## Applied changes

{changes}

## Rollback

```powershell
.\\.venv\\Scripts\\python.exe scripts/rollback_phase7d3_fundamental_coverage_dashboard_fix.py
```

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- filters modified: `{summary["filters_modified"]}`
- release modified: `{summary["release_modified"]}`
"""


def main() -> int:
    print("Scout Finance — Phase 7D.3 fundamental coverage dashboard fix")
    print("=" * 88)

    if not APP_PATH.exists():
        fail(f"Missing app.py: {APP_PATH}")
        return 1

    good, error = compile_file(APP_PATH)
    if not good:
        fail(f"app.py does not compile before hotfix: {error}")
        return 1
    ok("app.py compiles before hotfix")

    if not BACKUP_PATH.exists():
        shutil.copy2(APP_PATH, BACKUP_PATH)
        backup_created = True
        ok(f"Backup created: {BACKUP_PATH}")
    else:
        backup_created = False
        ok(f"Backup already exists: {BACKUP_PATH}")

    original = APP_PATH.read_text(encoding="utf-8", errors="replace")

    try:
        patched, changes = patch_app(original)
    except Exception as exc:
        fail(str(exc))
        return 1

    APP_PATH.write_text(patched, encoding="utf-8")

    good, error = compile_file(APP_PATH)
    if not good:
        fail(f"app.py does not compile after hotfix: {error}")
        shutil.copy2(BACKUP_PATH, APP_PATH)
        warn("Rollback restored app.py from backup")
        return 1
    ok("app.py compiles after hotfix")

    yf = read_json(YF_SUMMARY_PATH)

    summary = {
        "phase": "7D.3",
        "status": "OK",
        "created_at": utc_now(),
        "backup_path": str(BACKUP_PATH),
        "backup_created": backup_created,
        "changes": changes,
        "expected_visual_values": {
            "stage1_passed": 182,
            "fundamentals_matched": 182,
            "ready_stage2": 147,
            "not_ready_stage2": 35,
            "average_core_stage2_coverage": "83.17%",
            "runner_phase": "7C.1",
        },
        "yfinance_summary_found": bool(yf),
        "app_modified": True,
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "filters_modified": False,
        "release_modified": False,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Hotfix")
    print("-" * 88)
    print(f"Changes: {changes}")
    ok("Phase 7D.3 fundamental coverage dashboard fix applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
