from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.24F"
PHASE = "Metadata Promotion / Freeze Decision"
OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
DRY_RUN_JSON = OUTPUT_DIR / "metadata_improvement_dry_run_v2_24e.json"
OVERLAY = OUTPUT_DIR / "metadata_improvement_dry_run_overlay_v2_24e.csv"

PROMOTED = OUTPUT_DIR / "expanded_universe_v2_24f_metadata_promoted.csv"
REPORT_JSON = OUTPUT_DIR / "metadata_promotion_freeze_decision_v2_24f.json"
REPORT_MD = OUTPUT_DIR / "metadata_promotion_freeze_decision_v2_24f.md"
SUMMARY = OUTPUT_DIR / "metadata_promotion_freeze_decision_summary_v2_24f.csv"
CHECKS = OUTPUT_DIR / "metadata_promotion_freeze_decision_checks_v2_24f.csv"
MANIFEST = OUTPUT_DIR / "metadata_promotion_freeze_decision_artifact_manifest_v2_24f.csv"
DECISIONS = OUTPUT_DIR / "metadata_promotion_freeze_decision_register_v2_24f.csv"
POINTER_MANIFEST = OUTPUT_DIR / "metadata_promotion_pointer_manifest_v2_24f.json"

EXPECTED_ROWS = 43089
EXPECTED_CANONICAL_CONTRACT_SHA = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"
EXPECTED_DRY_STATUS = "METADATA_IMPROVEMENT_DRY_RUN_COMPLETED_NO_PROMOTION"
EXPECTED_DERIVED_CELLS = 56002
FIELDS = ["country", "mic", "currency", "asset_type", "instrument_type", "instrument_scope"]

STATUS_PASS = "METADATA_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_CREATED_POINTER_UNCHANGED"
STATUS_FAIL = "METADATA_PROMOTION_FREEZE_DECISION_FAILED_REVIEW_REQUIRED"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_contract_sha(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(data).hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


def missing(value: str | None) -> bool:
    return not (value or "").strip()


def main() -> None:
    outputs = [PROMOTED, REPORT_JSON, REPORT_MD, SUMMARY, CHECKS, MANIFEST, DECISIONS, POINTER_MANIFEST]
    for path in outputs:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    canonical_sha_before = sha256(CANONICAL)
    canonical_contract_before = canonical_contract_sha(CANONICAL)
    pointer_sha_before = sha256(POINTER)
    dry = json.loads(DRY_RUN_JSON.read_text(encoding="utf-8"))
    header, canonical_rows = read_csv(CANONICAL)
    _, overlay_rows = read_csv(OVERLAY)

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str, severity: str = "critical") -> None:
        checks.append({"check": name, "passed": passed, "severity": severity, "detail": detail})

    check("dry_run_status_expected", dry.get("status") == EXPECTED_DRY_STATUS, str(dry.get("status")))
    check("dry_run_critical_failed_checks_zero", dry.get("summary", {}).get("critical_failed_checks") == 0,
          str(dry.get("summary", {}).get("critical_failed_checks")))
    check("canonical_contract_sha_expected", canonical_contract_before == EXPECTED_CANONICAL_CONTRACT_SHA,
          canonical_contract_before)
    check("row_count_43089", len(canonical_rows) == len(overlay_rows) == EXPECTED_ROWS,
          f"canonical={len(canonical_rows)};overlay={len(overlay_rows)}")

    promoted_rows: list[dict[str, str]] = []
    derived_cells = 0
    overwrite_attempts = 0
    identity_mismatches = 0
    original_mismatches = 0
    provenance_missing = 0

    for index, (source, overlay) in enumerate(zip(canonical_rows, overlay_rows), start=1):
        identity_ok = (
            overlay.get("row_number") == str(index)
            and overlay.get("ticker", "") == source.get("ticker", "")
            and overlay.get("exchange", "") == source.get("exchange", "")
            and overlay.get("source_provider", "")
            == (source.get("source_provider", "").strip() or "__MISSING_PROVIDER__")
        )
        identity_mismatches += int(not identity_ok)
        promoted = dict(source)
        for field in FIELDS:
            original = overlay.get(f"original_{field}", "")
            proposed = overlay.get(f"proposed_{field}", "")
            rule_id = overlay.get(f"{field}_rule_id", "")
            if original != source.get(field, ""):
                original_mismatches += 1
            if proposed != original:
                if not missing(original):
                    overwrite_attempts += 1
                if missing(rule_id):
                    provenance_missing += 1
                promoted[field] = proposed
                derived_cells += 1
        promoted_rows.append(promoted)

    check("row_identity_exact", identity_mismatches == 0, str(identity_mismatches))
    check("overlay_originals_match_canonical", original_mismatches == 0, str(original_mismatches))
    check("zero_overwrites", overwrite_attempts == 0, str(overwrite_attempts))
    check("derived_cells_expected", derived_cells == EXPECTED_DERIVED_CELLS, str(derived_cells))
    check("derived_provenance_100pct", provenance_missing == 0,
          f"derived={derived_cells};missing_provenance={provenance_missing}")

    prewrite_failed = sum(not row["passed"] for row in checks if row["severity"] == "critical")
    if prewrite_failed:
        raise SystemExit(f"PREWRITE_GATE_FAILED: {prewrite_failed} critical checks failed")

    write_csv(PROMOTED, promoted_rows, header)
    promoted_header, promoted_check_rows = read_csv(PROMOTED)
    promoted_sha = sha256(PROMOTED)

    changed_non_metadata = 0
    changed_metadata_cells = 0
    for source, promoted in zip(canonical_rows, promoted_check_rows):
        changed_non_metadata += sum(source[col] != promoted[col] for col in header if col not in FIELDS)
        changed_metadata_cells += sum(source[field] != promoted[field] for field in FIELDS)

    check("promoted_header_exact", promoted_header == header, f"columns={len(promoted_header)}")
    check("promoted_rows_43089", len(promoted_check_rows) == EXPECTED_ROWS, str(len(promoted_check_rows)))
    check("only_metadata_fields_changed", changed_non_metadata == 0, str(changed_non_metadata))
    check("promoted_changes_match_overlay", changed_metadata_cells == EXPECTED_DERIVED_CELLS,
          str(changed_metadata_cells))
    check("canonical_file_unchanged", sha256(CANONICAL) == canonical_sha_before, sha256(CANONICAL))
    check("canonical_contract_unchanged", canonical_contract_sha(CANONICAL) == canonical_contract_before,
          canonical_contract_sha(CANONICAL))
    check("active_pointer_unchanged", sha256(POINTER) == pointer_sha_before, sha256(POINTER))

    critical_failed = sum(not row["passed"] for row in checks if row["severity"] == "critical")
    status = STATUS_PASS if critical_failed == 0 else STATUS_FAIL
    approved = critical_failed == 0

    pointer_manifest = {
        "version": VERSION,
        "decision": "PROMOTE_METADATA_ARTIFACT" if approved else "FREEZE_REVIEW_REQUIRED",
        "promoted_dataset": str(PROMOTED),
        "promoted_dataset_rows": len(promoted_check_rows),
        "promoted_dataset_sha256": promoted_sha,
        "active_pointer_modified": False,
        "active_pointer_sha256": pointer_sha_before,
        "activation_deferred": True,
        "reason": "Create a controlled promoted artifact without silently replacing the operational pointer.",
    }
    write_json(POINTER_MANIFEST, pointer_manifest)

    decisions = [
        {"decision_id": "V2_24F_001", "decision": "Promote the deterministic v2.24E overlay as a new immutable metadata artifact.",
         "result": "APPROVED" if approved else "FROZEN", "effect": f"{derived_cells} traced metadata cells; 43,089 rows."},
        {"decision_id": "V2_24F_002", "decision": "Preserve the existing canonical dataset and active pointer unchanged.",
         "result": "ENFORCED", "effect": "No in-place mutation and no blind operational activation."},
        {"decision_id": "V2_24F_003", "decision": "Freeze unresolved HKEX, missing-provider and ambiguous CBOE Europe metadata.",
         "result": "ENFORCED", "effect": "Unresolved values remain blank instead of being guessed."},
        {"decision_id": "V2_24F_004", "decision": "Keep production scoring blocked pending v2.25 readiness gates.",
         "result": "ENFORCED", "effect": "Metadata promotion does not authorize or promote scoring."},
    ]
    write_csv(DECISIONS, decisions, ["decision_id", "decision", "result", "effect"])

    summary = [{
        "version": VERSION, "phase": PHASE, "status": status,
        "canonical_rows": len(canonical_rows), "promoted_rows": len(promoted_check_rows),
        "promoted_sha256": promoted_sha, "derived_cells": derived_cells,
        "provenance_coverage_pct": 100.0 if derived_cells and provenance_missing == 0 else 0.0,
        "overwrite_attempts": overwrite_attempts, "critical_failed_checks": critical_failed,
        "metadata_artifact_promoted": approved, "canonical_dataset_modified": False,
        "active_pointer_modified": False, "production_scoring_authorized": False,
        "scoring_promoted": False, "openai_called": False, "broker_called": False,
        "full59k": "DEPRECATED_DEFERRED",
    }]
    write_csv(SUMMARY, summary, list(summary[0]))
    write_csv(CHECKS, checks, ["check", "passed", "severity", "detail"])

    report = {
        "version": VERSION, "phase": PHASE, "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "PROMOTE_METADATA_ARTIFACT" if approved else "FREEZE_REVIEW_REQUIRED",
        "summary": summary[0], "checks": checks, "decisions": decisions,
        "inputs": {"canonical": str(CANONICAL), "canonical_sha256": canonical_sha_before,
                   "canonical_contract_sha256": canonical_contract_before,
                   "dry_run": str(DRY_RUN_JSON), "overlay": str(OVERLAY), "overlay_sha256": sha256(OVERLAY)},
        "outputs": {"promoted_dataset": str(PROMOTED), "promoted_sha256": promoted_sha,
                    "pointer_manifest": str(POINTER_MANIFEST)},
        "holds": ["hkex_securities_list", "HKEX", "__MISSING_PROVIDER__", "cboe_europe_ambiguous_geography"],
        "next_phase": "v2.24G - Metadata Closure Report" if approved else "v2.24F - Review required",
    }
    write_json(REPORT_JSON, report)

    md = f"""# Scout Finance — v2.24F Metadata Promotion / Freeze Decision

**Status:** `{status}`

## Decision

The v2.24E deterministic overlay is **approved and promoted as a controlled immutable metadata artifact**. The existing canonical dataset and active operational pointer remain unchanged; activation is deliberately deferred rather than performed silently.

- Promoted dataset: `{PROMOTED}`
- Rows: **{len(promoted_check_rows):,}**
- Promoted SHA256: `{promoted_sha}`
- Deterministically improved cells: **{derived_cells:,}**
- Provenance: **100%**
- Overwrites: **{overwrite_attempts}**
- Critical failed checks: **{critical_failed}**

## Freeze boundary

HKEX, missing-provider rows and ambiguous CBOE Europe geography remain frozen and unresolved. No value is guessed. ASX/SGX controls remain unchanged through the accepted v2.24E overlay.

## Operational guardrails

- `metadata_artifact_promoted={approved}`
- `canonical_dataset_modified=False`
- `active_pointer_modified=False`
- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `openai_called=False`
- `broker_called=False`
- `full59k=DEPRECATED_DEFERRED`

**Recommended next phase:** `v2.24G — Metadata Closure Report`.
"""
    write_text(REPORT_MD, md)

    manifest_rows = []
    for path in [PROMOTED, POINTER_MANIFEST, DECISIONS, SUMMARY, CHECKS, REPORT_JSON, REPORT_MD]:
        rows = 0
        if path.suffix == ".csv":
            _, content = read_csv(path)
            rows = len(content)
        manifest_rows.append({"artifact": path.name, "path": str(path), "rows": rows, "sha256": sha256(path)})
    write_csv(MANIFEST, manifest_rows, ["artifact", "path", "rows", "sha256"])

    if critical_failed:
        raise SystemExit(status)
    print(json.dumps(summary[0], indent=2))


if __name__ == "__main__":
    main()
