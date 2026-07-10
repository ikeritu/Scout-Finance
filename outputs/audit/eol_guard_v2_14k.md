# v2.14K - .gitattributes / EOL Guard

Status: **EOL_GUARD_POLICY_ADDED_RENORMALIZATION_NOT_PERFORMED**

Phase type: **config-only**

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
