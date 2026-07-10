from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.14K"
PHASE = ".gitattributes / EOL Guard"
PHASE_TYPE = "config-only"

GITATTRIBUTES = Path(".gitattributes")
REPORT_JSON = Path("outputs/audit/eol_guard_v2_14k.json")
REPORT_MD = Path("outputs/audit/eol_guard_v2_14k.md")

GITATTRIBUTES_CONTENT = """# Scout Finance - v2.14K EOL Guard
# Keep line endings stable across Windows/macOS/Linux.
# This phase adds policy only; it does not perform repo-wide renormalization.

* text=auto eol=lf

# Source / text files
*.py text eol=lf
*.md text eol=lf
*.txt text eol=lf
*.json text eol=lf
*.csv text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.toml text eol=lf
*.html text eol=lf
*.css text eol=lf
*.js text eol=lf
*.ts text eol=lf
*.tsx text eol=lf
*.sql text eol=lf
*.ps1 text eol=lf

# Microsoft Office / binary documents
*.doc binary
*.docx binary
*.xls binary
*.xlsx binary
*.ppt binary
*.pptx binary

# Archives / raw dumps / binary data
*.zip binary
*.gz binary
*.tar binary
*.7z binary
*.rar binary
*.pkl binary
*.pickle binary
*.db binary
*.sqlite binary
*.sqlite3 binary
*.parquet binary
*.feather binary

# Media / images / PDFs
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.webp binary
*.ico binary
*.svg text eol=lf
*.pdf binary
*.mp4 binary
*.mov binary
*.avi binary
*.webm binary
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    if GITATTRIBUTES.exists():
        raise SystemExit("NO_OVERWRITE_GUARD: .gitattributes already exists")

    if REPORT_JSON.exists() or REPORT_MD.exists():
        raise SystemExit("NO_OVERWRITE_GUARD: v2.14K reports already exist")

    GITATTRIBUTES.write_text(GITATTRIBUTES_CONTENT, encoding="utf-8", newline="\n")

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "generated_at_utc": utc_now(),
        "status": "EOL_GUARD_POLICY_ADDED_RENORMALIZATION_NOT_PERFORMED",
        "files_created": [
            str(GITATTRIBUTES),
            str(REPORT_JSON),
            str(REPORT_MD),
        ],
        "policy": {
            "default": "* text=auto eol=lf",
            "source_text": "LF",
            "office_documents": "binary",
            "archives_raw_dumps_binary_data": "binary",
            "media_images_pdfs": "binary",
        },
        "decision": {
            "renormalization_performed": False,
            "reason": "Avoid mass noisy commit. Repo-wide renormalization must be a separate explicit phase if needed.",
            "safe_next_check": "git add --renormalize --dry-run .",
        },
        "current_project_state": {
            "canonical_dataset": "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv",
            "expanded_rows": 38287,
            "source_to_50k_completed_percent": 76.6,
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
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": "v2.15A - Next Provider Route For Remaining Full Source Gap",
        "optional_future_phase": "v2.14L - Controlled Repo Renormalization Dry Run",
    }

    write_new(REPORT_JSON, json.dumps(payload, indent=2, ensure_ascii=False))

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **EOL_GUARD_POLICY_ADDED_RENORMALIZATION_NOT_PERFORMED**

Phase type: **{PHASE_TYPE}**

## What changed

- Added `.gitattributes`.
- Declared LF for source/text files.
- Declared Office documents, archives, raw binary dumps, databases, media and PDFs as binary.
- Did **not** run repo-wide renormalization.

## Why conservative

The audit identified CRLF/LF noise as a risk. This phase adds a policy guard but intentionally avoids a mass commit affecting hundreds of files.

Repo-wide renormalization, if needed, should be done in a separate explicit phase after reviewing:

`git add --renormalize --dry-run .`

## Current project state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Expanded rows: `38,287`
- Source-to-50k: `76.6%`
- Rows needed: `11,713`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Guards

- Network download performed: false
- Raw files downloaded: false
- Raw files modified after write: false
- Workbook/CSV parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Recommended next phase

`v2.15A - Next Provider Route For Remaining Full Source Gap`

## Optional future phase

`v2.14L - Controlled Repo Renormalization Dry Run`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.14K EOL guard completed.")
    print("- created: .gitattributes")
    print(f"- created: {REPORT_JSON}")
    print(f"- created: {REPORT_MD}")
    print("")
    print("DECISION:")
    print("- renormalization_performed: False")
    print("- recommended_next_phase: v2.15A - Next Provider Route For Remaining Full Source Gap")
    print("- optional_future_phase: v2.14L - Controlled Repo Renormalization Dry Run")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
