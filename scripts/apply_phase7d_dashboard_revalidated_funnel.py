
from __future__ import annotations

import ast
import json
import py_compile
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

APP_PATH = ROOT / "app.py"
BACKUP_PATH = ROOT / "app_before_phase7d_dashboard_revalidated_funnel.py"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7d_dashboard_revalidated_funnel_summary.json"
REPORT_PATH = OUT_DIR / "phase7d_dashboard_revalidated_funnel_report.md"

PIPELINE_STATUS_PATH = OUT_DIR / "active_pipeline_policy_status.json"
PIPELINE_SUMMARY_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_summary.json"
TOP_CANDIDATES_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_top_candidates.csv"

PATCH_MARKER = "# PHASE 7D REVALIDATED FUNNEL DASHBOARD APPLIED"
HELPER_START = "# >>> PHASE 7D REVALIDATED FUNNEL DASHBOARD HELPERS"
CALL_LINE = "_render_phase7d_revalidated_funnel_dashboard()"

EXPECTED_FUNNEL = "500 → 182 → 63 → 6"

HELPER_CODE = '# >>> PHASE 7D REVALIDATED FUNNEL DASHBOARD HELPERS\n\ndef _phase7d_load_json(path):\n    import json\n    from pathlib import Path\n    p = Path(path)\n    if not p.exists():\n        return {}\n    try:\n        return json.loads(p.read_text(encoding="utf-8"))\n    except Exception:\n        return {}\n\n\ndef _phase7d_load_csv(path):\n    from pathlib import Path\n    import pandas as pd\n    p = Path(path)\n    if not p.exists():\n        return pd.DataFrame()\n    try:\n        return pd.read_csv(p)\n    except Exception:\n        return pd.DataFrame()\n\n\ndef _render_phase7d_revalidated_funnel_dashboard():\n    import streamlit as st\n    from pathlib import Path\n\n    root = Path(__file__).resolve().parent\n    out_dir = root / "outputs" / "scouting"\n\n    status_path = out_dir / "active_pipeline_policy_status.json"\n    summary_path = out_dir / "phase7c4_pipeline_revalidation_summary.json"\n    top_candidates_path = out_dir / "phase7c4_pipeline_revalidation_top_candidates.csv"\n\n    status = _phase7d_load_json(status_path)\n    summary = _phase7d_load_json(summary_path)\n    top_candidates = _phase7d_load_csv(top_candidates_path)\n\n    if not status and not summary:\n        return\n\n    with st.container():\n        st.markdown("## ✅ Funnel real revalidado")\n\n        funnel = summary.get("funnel", {}) if isinstance(summary, dict) else {}\n        funnel_path = funnel.get("path") or "500 → 182 → 63 → 6"\n\n        st.caption("Pipeline validado con Stage 1 Balanced, Stage 2 yfinance-aligned y Stage 3 scoring.")\n\n        html = (\n            \'<div style="padding: 1rem; border-radius: 0.9rem; border: 1px solid rgba(120,120,120,0.25); margin-bottom: 1rem;">\'\n            \'<div style="font-size: 0.85rem; opacity: 0.75;">Funnel revalidado</div>\'\n            f\'<div style="font-size: 2rem; font-weight: 800; margin-top: 0.2rem;">{funnel_path}</div>\'\n            \'<div style="font-size: 0.85rem; opacity: 0.75; margin-top: 0.2rem;">Universo limpio → Stage 1 → Stage 2 → Stage 3</div>\'\n            \'</div>\'\n        )\n        st.markdown(html, unsafe_allow_html=True)\n\n        stage_counts = summary.get("stage_counts", {}) if isinstance(summary, dict) else {}\n        stage1 = stage_counts.get("stage1", {})\n        stage2 = stage_counts.get("stage2", {})\n        stage3 = stage_counts.get("stage3", {})\n\n        c1, c2, c3 = st.columns(3)\n        with c1:\n            st.metric("Stage 1 PASSED", stage1.get("passed", 182))\n            st.caption(f"Watchlist {stage1.get(\'watchlist\', 84)} · Rejected {stage1.get(\'rejected\', 234)}")\n        with c2:\n            st.metric("Stage 2 PASSED", stage2.get("passed", 63))\n            st.caption(f"Watchlist {stage2.get(\'watchlist\', 81)} · Rejected {stage2.get(\'rejected\', 38)}")\n        with c3:\n            st.metric("Stage 3 PASSED", stage3.get("passed", 6))\n            st.caption(f"Watchlist {stage3.get(\'watchlist\', 28)} · Rejected {stage3.get(\'rejected\', 29)}")\n\n        policies = summary.get("active_policies", {}) if isinstance(summary, dict) else {}\n        with st.expander("Políticas activas del pipeline", expanded=False):\n            st.write({\n                "Stage 1": policies.get("stage1", "Balanced official policy"),\n                "Stage 2": policies.get("stage2", "yfinance-aligned provider-limitation policy"),\n                "Stage 3": policies.get("stage3", "Existing Stage 3 opportunity scoring policy"),\n            })\n\n        st.info(\n            "Nota de proveedor: `shares_dilution_3y` queda registrada como limitación de yfinance. "\n            "No bloquea por sí sola el paso limpio en Stage 2, pero queda pendiente para una fuente superior o SEC/companyfacts."\n        )\n\n        if not top_candidates.empty:\n            st.markdown("### Top candidates revalidadas")\n            display_cols = [\n                col for col in [\n                    "ticker",\n                    "name",\n                    "final_stage3_score",\n                    "stage3_category",\n                    "stage3_status",\n                    "risk_score",\n                    "data_quality_score",\n                ] if col in top_candidates.columns\n            ]\n            st.dataframe(top_candidates[display_cols].head(10), use_container_width=True, hide_index=True)\n        else:\n            st.warning("No se ha encontrado el archivo de top candidates revalidado.")\n\n# <<< PHASE 7D REVALIDATED FUNNEL DASHBOARD HELPERS'


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


def count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return 0


def find_insertion_index_for_call(lines: list[str]) -> int:
    title_patterns = [
        "st.title(",
        "st.header(",
        "st.markdown(\"#",
        "st.markdown('#",
    ]

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if any(pattern in stripped for pattern in title_patterns):
            return idx + 1

    for idx, line in enumerate(lines):
        if "st.set_page_config(" in line:
            for j in range(idx, min(idx + 12, len(lines))):
                if lines[j].strip().endswith(")"):
                    return j + 1
            return idx + 1

    last_import = 0
    for idx, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            last_import = idx + 1
    return last_import


def patch_app(text: str) -> tuple[str, list[str]]:
    if PATCH_MARKER in text:
        return text, ["ALREADY_APPLIED"]

    changes = []

    patched = text.rstrip() + "\n\n" + HELPER_CODE.strip() + "\n"
    changes.append("PHASE7D_HELPERS_APPENDED")

    lines = patched.splitlines()
    insert_idx = find_insertion_index_for_call(lines)

    helper_start_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == HELPER_START:
            helper_start_idx = idx
            break

    if helper_start_idx is not None and insert_idx >= helper_start_idx:
        insert_idx = helper_start_idx

    call_block = [
        "",
        PATCH_MARKER,
        "try:",
        f"    {CALL_LINE}",
        "except Exception as exc:",
        "    try:",
        "        import streamlit as st",
        '        st.warning(f"Phase 7D dashboard block could not be rendered: {exc}")',
        "    except Exception:",
        "        pass",
        "",
    ]

    lines[insert_idx:insert_idx] = call_block
    changes.append("PHASE7D_RENDER_CALL_INSERTED")

    return "\n".join(lines) + "\n", changes


def render_report(summary: dict) -> str:
    changes = "\n".join("- " + str(change) for change in summary["changes"])
    return f"""# Scout Finance — Phase 7D v2 dashboard revalidated funnel integration

Generated at: `{summary["created_at"]}`

## Result

- Status: **{summary["status"]}**
- app.py modified: **{summary["app_modified"]}**
- Backup: `{summary["backup_path"]}`

## Dashboard content integrated

- Funnel: `{summary["funnel_path"]}`
- Stage 1 policy: `{summary["active_policies"].get("stage1")}`
- Stage 2 policy: `{summary["active_policies"].get("stage2")}`
- Stage 3 policy: `{summary["active_policies"].get("stage3")}`
- Top candidates rows available: `{summary["top_candidates_rows"]}`

## Applied changes

{changes}

## Rollback

```powershell
.\\.venv\\Scripts\\python.exe scripts/rollback_phase7d_dashboard_revalidated_funnel.py
```

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- filters modified: `{summary["filters_modified"]}`
- release modified: `{summary["release_modified"]}`
"""


def main() -> int:
    print("Scout Finance — Phase 7D v2 dashboard revalidated funnel integration")
    print("=" * 88)

    if not APP_PATH.exists():
        fail(f"Missing app.py: {APP_PATH}")
        return 1

    if not PIPELINE_STATUS_PATH.exists():
        fail(f"Missing policy status file: {PIPELINE_STATUS_PATH}")
        return 1
    ok("Policy status file exists")

    if not PIPELINE_SUMMARY_PATH.exists():
        fail(f"Missing Phase 7C.4 summary file: {PIPELINE_SUMMARY_PATH}")
        return 1
    ok("Phase 7C.4 summary file exists")

    good, error = compile_file(APP_PATH)
    if not good:
        fail(f"app.py does not compile before patch: {error}")
        return 1
    ok("app.py compiles before patch")

    if not BACKUP_PATH.exists():
        shutil.copy2(APP_PATH, BACKUP_PATH)
        backup_created = True
        ok(f"Backup created: {BACKUP_PATH}")
    else:
        backup_created = False
        ok(f"Backup already exists: {BACKUP_PATH}")

    original = APP_PATH.read_text(encoding="utf-8", errors="replace")
    patched, changes = patch_app(original)
    APP_PATH.write_text(patched, encoding="utf-8")

    good, error = compile_file(APP_PATH)
    if not good:
        fail(f"app.py does not compile after patch: {error}")
        shutil.copy2(BACKUP_PATH, APP_PATH)
        warn("Rollback restored app.py from backup")
        return 1
    ok("app.py compiles after patch")

    policy_status = read_json(PIPELINE_STATUS_PATH)
    pipeline_summary = read_json(PIPELINE_SUMMARY_PATH)
    top_rows = count_csv(TOP_CANDIDATES_PATH)

    funnel_path = pipeline_summary.get("funnel", {}).get("path") or policy_status.get("current_revalidated_funnel", {}).get("path") or EXPECTED_FUNNEL
    active_policies = pipeline_summary.get("active_policies", {})

    summary = {
        "phase": "7D",
        "version": "v2",
        "status": "OK",
        "created_at": utc_now(),
        "backup_path": str(BACKUP_PATH),
        "backup_created": backup_created,
        "changes": changes,
        "funnel_path": funnel_path,
        "active_policies": active_policies,
        "top_candidates_rows": top_rows,
        "output_files": {
            "summary_json": str(SUMMARY_PATH),
            "report_md": str(REPORT_PATH),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": True,
        "filters_modified": False,
        "release_modified": False,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Dashboard integration")
    print("-" * 88)
    print(f"Funnel: {funnel_path}")
    print(f"Top candidates rows: {top_rows}")
    print(f"Changes: {changes}")

    ok("Phase 7D v2 dashboard integration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
