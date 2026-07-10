from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.14I"
PHASE = "Documentation and Canonical Dataset Path"
PHASE_TYPE = "documentation-only"

README = Path("README.md")
VERSION_MD = Path("VERSION.md")
CHANGELOG = Path("CHANGELOG.md")

DOCS_TECHNICAL_DIR = Path("docs/technical")
OUTPUT_AUDIT_DIR = Path("outputs/audit")

TECH_DOC = DOCS_TECHNICAL_DIR / "data_pipeline_current_state_v2_14i.md"
CANONICAL_DOC = DOCS_TECHNICAL_DIR / "expanded_universe_canonical_path_v2_14i.md"
MANIFEST_JSON = OUTPUT_AUDIT_DIR / "documentation_canonical_dataset_path_v2_14i.json"
REPORT_MD = OUTPUT_AUDIT_DIR / "documentation_canonical_dataset_path_v2_14i.md"

CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CANONICAL_VALIDATION = "outputs/full_universe_source_acquisition/deutsche_boerse_xetra_expanded_validation_v2_14f.json"
CANONICAL_CLOSURE = "outputs/full_universe_source_acquisition/deutsche_boerse_xetra_closure_report_v2_14g.json"

MARKER_START = "<!-- SCOUT_FINANCE_V2_14I_STATE_START -->"
MARKER_END = "<!-- SCOUT_FINANCE_V2_14I_STATE_END -->"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def write_new(path: Path, content: str) -> None:
    ensure_parent(path)
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


def prepend_marker_block(path: Path, title: str, body: str) -> None:
    original = read_text(path)

    if MARKER_START in original or MARKER_END in original:
        raise SystemExit(f"NO_OVERWRITE_GUARD: v2.14I marker already exists in {path}")

    block = f"""{MARKER_START}
## {title}

{body}

{MARKER_END}

"""

    path.write_text(block + original, encoding="utf-8", newline="\n")


def main() -> None:
    OUTPUT_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_TECHNICAL_DIR.mkdir(parents=True, exist_ok=True)

    for path in [TECH_DOC, CANONICAL_DOC, MANIFEST_JSON, REPORT_MD]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    now = utc_now()

    common_body = f"""Estado documental añadido en **{VERSION} — {PHASE}**.

- Línea app/MVP: `v1.1C — MVP Final Freeze`
- Línea pipeline de datos: `v2.14H — Audit Triage / Stability Gate`
- Último cierre de proveedor validado: `v2.14G — Deutsche Boerse Xetra Closure Report`
- Commit de cierre Xetra: `5a4e3f0`
- Commit de triage auditoría: `7f1cb64`
- Dataset expandido canónico vigente: `{CANONICAL_DATASET}`
- Filas actuales: `38,287`
- Fuente hacia 50k: `76.6%`
- Filas pendientes hacia 50k: `11,713`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

Nota: la documentación distingue explícitamente entre la app Streamlit congelada en v1.1C y el pipeline de expansión de universo en v2.x.
"""

    version_body = f"""Estado real del repositorio tras auditoría y cierre Xetra.

- App/MVP: `v1.1C — MVP Final Freeze`
- Pipeline de datos: `v2.14H — Audit Triage / Stability Gate`
- Dataset canónico vigente: `{CANONICAL_DATASET}`
- Siguiente fase recomendada: `v2.14J — Post-Closure Integrity Test` o `v2.15A — Next Provider Route`, según prioridad operativa.
"""

    changelog_body = f"""### {VERSION} — {PHASE}

- Documenta la separación entre app/MVP `v1.1C` y pipeline de datos `v2.14H`.
- Fija la ruta canónica vigente del expanded universe: `{CANONICAL_DATASET}`.
- Documenta estado actual: `38,287` filas, `76.6%` hacia 50k, `11,713` filas pendientes.
- Mantiene full source gate y full 59k dry-run bloqueados.
- Fase documental: no modifica datos, no rebuild, no scoring, no OpenAI, no broker.
"""

    prepend_marker_block(
        README,
        "Estado actual del proyecto / Current Project State",
        common_body,
    )

    prepend_marker_block(
        VERSION_MD,
        "Estado real actual / Current Real State",
        version_body,
    )

    prepend_marker_block(
        CHANGELOG,
        "Entrada documental v2.14I",
        changelog_body,
    )

    tech_doc = f"""# {VERSION} - {PHASE}

Generated at UTC: `{now}`

Phase type: **{PHASE_TYPE}**

## Purpose

This document records the current data-pipeline state after the Deutsche Boerse Xetra closure and the audit triage gate.

It intentionally separates two project tracks:

1. **Streamlit app / MVP track**
   - Documented historical app state: `v1.1C — MVP Final Freeze`

2. **Data pipeline / expanded universe track**
   - Current data-pipeline state: `v2.14H — Audit Triage / Stability Gate`
   - Last provider closure: `v2.14G — Deutsche Boerse Xetra Closure Report`

## Current canonical dataset

- Canonical expanded universe CSV: `{CANONICAL_DATASET}`
- Validation artifact: `{CANONICAL_VALIDATION}`
- Closure artifact: `{CANONICAL_CLOSURE}`

## Current counts

- Expanded universe rows: `38,287`
- Minimum full-source threshold: `50,000`
- Source-to-50k completed: `76.6%`
- Source-to-50k pending: `23.4%`
- Rows still needed: `11,713`

## Gates

- Full source gate: **blocked**
- Full 59k dry-run: **blocked**
- Scoring recalculation: **not performed**
- OpenAI calls: **not performed**
- Broker calls: **not performed**

## Provider breakdown at v2.14F/v2.14G

- cboe_europe_reference_data: 21,154
- jpx_listed_securities: 3,705
- nasdaq_trader_nasdaqlisted: 3,244
- hkex_securities_list: 2,804
- nasdaq_trader_otherlisted: 2,404
- sec_company_tickers_exchange: 2,359
- deutsche_boerse_xetra_all_tradable_instruments: 1,424
- cboe_listed_symbols: 1,193

## Important note

`data/raw/expanded_universe/` contains earlier historical expanded-universe artifacts. The current canonical dataset after v2.14G is in `outputs/full_universe_source_acquisition/`.
"""

    canonical_doc = f"""# Expanded Universe Canonical Path - {VERSION}

Generated at UTC: `{now}`

## Canonical current dataset

`{CANONICAL_DATASET}`

## Why this matters

The expanded-universe path changed during the v2.x provider expansion work. Older files in `data/raw/expanded_universe/` are historical and should not be treated as the current source of truth unless a specific phase explicitly references them.

## Current source of truth

| Concept | Path |
|---|---|
| Current expanded universe | `{CANONICAL_DATASET}` |
| Xetra expanded validation | `{CANONICAL_VALIDATION}` |
| Xetra closure report | `{CANONICAL_CLOSURE}` |
| Audit triage report | `outputs/audit/scout_finance_audit_triage_v2_14h.md` |
| Technical audit evidence | `outputs/audit/auditoria_tecnica_scout_finance_v1.md` |

## Current state

- Rows: `38,287`
- Threshold: `50,000`
- Completed: `76.6%`
- Pending: `23.4%`
- Rows needed: `11,713`

## Rules

- Do not use older expanded-universe CSVs as the current dataset without an explicit phase decision.
- Do not launch full 59k before source completion and explicit gate approval.
- Do not run scoring/OpenAI/broker actions from documentation phases.
"""

    write_new(TECH_DOC, tech_doc)
    write_new(CANONICAL_DOC, canonical_doc)

    manifest = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "generated_at_utc": now,
        "files_updated": [
            str(README),
            str(VERSION_MD),
            str(CHANGELOG),
        ],
        "files_created": [
            str(TECH_DOC),
            str(CANONICAL_DOC),
            str(MANIFEST_JSON),
            str(REPORT_MD),
        ],
        "canonical_dataset": CANONICAL_DATASET,
        "current_state": {
            "app_mvp_track": "v1.1C - MVP Final Freeze",
            "data_pipeline_track": "v2.14H - Audit Triage / Stability Gate",
            "last_provider_closure": "v2.14G - Deutsche Boerse Xetra Closure Report",
            "expanded_rows": 38287,
            "full_source_threshold": 50000,
            "source_to_50k_completed_percent": 76.6,
            "source_to_50k_pending_percent": 23.4,
            "rows_needed": 11713,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed": False,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": "v2.14J - Post-Closure Integrity Test",
        "alternative_next_phase": "v2.15A - Next Provider Route For Remaining Full Source Gap",
    }

    write_new(MANIFEST_JSON, json.dumps(manifest, indent=2, ensure_ascii=False))

    report = f"""# {VERSION} - {PHASE}

Status: **DOCUMENTATION_CANONICAL_PATH_UPDATED**

Generated at UTC: `{now}`

## Updated files

- `README.md`
- `VERSION.md`
- `CHANGELOG.md`

## Created files

- `{TECH_DOC}`
- `{CANONICAL_DOC}`
- `{MANIFEST_JSON}`
- `{REPORT_MD}`

## Canonical dataset

`{CANONICAL_DATASET}`

## Current state

- App/MVP track: `v1.1C — MVP Final Freeze`
- Data pipeline track: `v2.14H — Audit Triage / Stability Gate`
- Last provider closure: `v2.14G — Deutsche Boerse Xetra Closure Report`
- Expanded rows: `38,287`
- Source-to-50k: `76.6%`
- Rows pending: `11,713`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Guards

- Documentation-only: true
- Network download performed: false
- Raw files downloaded: false
- Raw files modified after write: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Recommended next phase

`v2.14J - Post-Closure Integrity Test`

Alternative if prioritizing source expansion:

`v2.15A - Next Provider Route For Remaining Full Source Gap`
"""

    write_new(REPORT_MD, report)

    print("v2.14I documentation and canonical dataset path completed.")
    print(f"- updated: {README}")
    print(f"- updated: {VERSION_MD}")
    print(f"- updated: {CHANGELOG}")
    print(f"- created: {TECH_DOC}")
    print(f"- created: {CANONICAL_DOC}")
    print(f"- created: {MANIFEST_JSON}")
    print(f"- created: {REPORT_MD}")
    print("")
    print("CANONICAL_DATASET:")
    print(f"- {CANONICAL_DATASET}")
    print("")
    print("GUARDS:")
    for key, value in manifest["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
