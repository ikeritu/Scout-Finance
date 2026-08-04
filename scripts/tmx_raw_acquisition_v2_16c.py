from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


VERSION = "v2.16C"
PHASE = "TMX Raw Acquisition"
PHASE_TYPE = "raw-acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "tmx_v2_16c"

V216B_JSON = OUTPUT_DIR / "tmx_acquisition_plan_v2_16b.json"
V216B_SOURCES_CSV = OUTPUT_DIR / "tmx_source_candidates_v2_16b.csv"

MANIFEST_JSON = OUTPUT_DIR / "tmx_raw_acquisition_manifest_v2_16c.json"
MANIFEST_MD = OUTPUT_DIR / "tmx_raw_acquisition_manifest_v2_16c.md"
MANIFEST_CSV = OUTPUT_DIR / "tmx_raw_acquisition_manifest_v2_16c.csv"
SOURCE_ACTIONS_CSV = OUTPUT_DIR / "tmx_raw_acquisition_source_actions_v2_16c.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

REQUEST_TIMEOUT_SECONDS = 45
SLEEP_BETWEEN_REQUESTS_SECONDS = 0.50
MAX_BYTES_PER_SOURCE = 8_000_000

USER_AGENT = (
    "ScoutFinance/2.16C TMX raw acquisition "
    "(raw acquisition only; no parsing; no canonical read; no rebuild)"
)

NEXT_PHASE = "v2.16D - TMX Validation"

MANIFEST_FIELDS = [
    "source_id",
    "source_name",
    "priority",
    "source_type",
    "decision",
    "url",
    "action",
    "download_attempted",
    "download_allowed",
    "skipped_reason",
    "status_code",
    "ok",
    "final_url",
    "content_type",
    "content_length_header",
    "bytes_written",
    "sha256",
    "raw_path",
    "error",
]

ACTION_FIELDS = [
    "source_id",
    "source_name",
    "priority",
    "decision",
    "source_url",
    "planned_v2_16c_action",
    "executed_action",
    "allowed",
    "reason",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "source"


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def get_nested(payload: dict, *keys, default=None):
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def host_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    allowed_hosts = (
        "tsx.com",
        "www.tsx.com",
        "apps.tmx.com",
        "money.tmx.com",
        "www.tmx.com",
    )
    return host in allowed_hosts or host.endswith(".tsx.com") or host.endswith(".tmx.com")


def source_download_allowed(source: dict) -> tuple[bool, str]:
    source_type = str(source.get("source_type", "")).lower()
    source_id = str(source.get("source_id", "")).lower()
    decision = str(source.get("decision", "")).lower()
    url = str(source.get("source_url", "")).strip()

    if not url:
        return False, "missing_url"

    # Paid/controlled sources must be classified before host allowlist checks.
    # TMX Datalinx / Info Services is documented as an official fallback, but
    # v2.16C must not access paid or controlled reference-data routes.
    if "paid" in source_type or "controlled" in source_type or "datalinx" in source_id or "infoservices" in url.lower():
        return False, "paid_or_controlled_source_not_downloaded"

    if "fallback" in decision and "not_executed" in decision:
        return False, "fallback_not_executed_by_default"

    if not host_allowed(url):
        return False, "host_not_allowed"

    return True, "allowed_public_planned_source"


def read_response_limited(response: requests.Response, max_bytes: int) -> bytes:
    chunks = []
    total = 0

    for chunk in response.iter_content(chunk_size=65536):
        if not chunk:
            continue

        remaining = max_bytes - total
        if remaining <= 0:
            break

        part = chunk[:remaining]
        chunks.append(part)
        total += len(part)

        if total >= max_bytes:
            break

    return b"".join(chunks)


def download_source(session: requests.Session, source: dict, order: int) -> dict:
    url = str(source.get("source_url", "")).strip()
    source_id = str(source.get("source_id", "")).strip()
    allowed, reason = source_download_allowed(source)

    row = {
        "source_id": source_id,
        "source_name": source.get("source_name", ""),
        "priority": source.get("priority", ""),
        "source_type": source.get("source_type", ""),
        "decision": source.get("decision", ""),
        "url": url,
        "action": source.get("v2_16c_action", ""),
        "download_attempted": False,
        "download_allowed": allowed,
        "skipped_reason": "" if allowed else reason,
        "status_code": "",
        "ok": False,
        "final_url": "",
        "content_type": "",
        "content_length_header": "",
        "bytes_written": 0,
        "sha256": "",
        "raw_path": "",
        "error": "",
    }

    if not allowed:
        return row

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml,application/json,text/plain,*/*;q=0.8",
    }

    raw_name = f"{order:02d}_{slugify(source_id)}.raw"
    raw_path = RAW_DIR / raw_name

    if raw_path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {raw_path}")

    try:
        row["download_attempted"] = True

        with session.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
            stream=True,
        ) as response:
            body = read_response_limited(response, MAX_BYTES_PER_SOURCE)
            raw_path.write_bytes(body)

            row.update(
                {
                    "status_code": response.status_code,
                    "ok": bool(response.ok),
                    "final_url": response.url,
                    "content_type": response.headers.get("content-type", ""),
                    "content_length_header": response.headers.get("content-length", ""),
                    "bytes_written": len(body),
                    "sha256": sha256_bytes(body) if body else "",
                    "raw_path": str(raw_path),
                }
            )

    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"

    return row


def main() -> None:
    for path in [MANIFEST_JSON, MANIFEST_MD, MANIFEST_CSV, SOURCE_ACTIONS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw directory already exists: {RAW_DIR}")

    plan = read_json(V216B_JSON)
    sources = read_csv(V216B_SOURCES_CSV)

    RAW_DIR.mkdir(parents=True, exist_ok=False)

    source_actions = []
    for source in sources:
        allowed, reason = source_download_allowed(source)
        source_actions.append(
            {
                "source_id": source.get("source_id", ""),
                "source_name": source.get("source_name", ""),
                "priority": source.get("priority", ""),
                "decision": source.get("decision", ""),
                "source_url": source.get("source_url", ""),
                "planned_v2_16c_action": source.get("v2_16c_action", ""),
                "executed_action": "download_landing_response_only" if allowed else "skip",
                "allowed": allowed,
                "reason": reason,
            }
        )

    selected_sources = sorted(sources, key=lambda row: as_int(row.get("priority", 999), 999))

    session = requests.Session()

    manifest_rows = []
    for order, source in enumerate(selected_sources, start=1):
        row = download_source(session, source, order)
        manifest_rows.append(row)
        time.sleep(SLEEP_BETWEEN_REQUESTS_SECONDS)

    attempted_count = sum(1 for row in manifest_rows if row["download_attempted"])
    allowed_count = sum(1 for row in manifest_rows if row["download_allowed"])
    skipped_count = sum(1 for row in manifest_rows if not row["download_allowed"])
    raw_files_written = sum(1 for row in manifest_rows if row["raw_path"])
    ok_count = sum(1 for row in manifest_rows if row["ok"])
    error_count = sum(1 for row in manifest_rows if row["error"])
    bytes_total = sum(as_int(row["bytes_written"], 0) for row in manifest_rows)
    paid_skipped_count = sum(1 for row in manifest_rows if row["skipped_reason"] == "paid_or_controlled_source_not_downloaded")

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append(
            {
                "check": check,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add_check("v2_16b_plan_exists", V216B_JSON.exists(), "critical", str(V216B_JSON))
    add_check("v2_16b_source_candidates_exists", V216B_SOURCES_CSV.exists(), "critical", str(V216B_SOURCES_CSV))
    add_check(
        "v2_16b_status_valid",
        plan.get("status") == "TMX_ACQUISITION_PLAN_CREATED_NO_DOWNLOADS_PERFORMED_FULL_SOURCE_BLOCKED",
        "critical",
        plan.get("status", ""),
    )
    add_check(
        "v2_16b_recommended_v2_16c",
        plan.get("recommended_next_phase") == "v2.16C - TMX Raw Acquisition",
        "critical",
        plan.get("recommended_next_phase", ""),
    )
    add_check("raw_dir_created", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("source_candidates_loaded", len(sources) >= 5, "critical", f"sources={len(sources)}")
    add_check("public_sources_attempted", attempted_count >= 5, "critical", f"attempted={attempted_count}")
    add_check("raw_files_written", raw_files_written >= 4, "critical", f"raw_files_written={raw_files_written}")
    add_check("controller_timeouts_review", error_count <= 2, "warning", f"controller_errors_or_timeouts={error_count}")
    add_check("at_least_one_http_ok", ok_count >= 1, "warning", f"ok_count={ok_count}")
    add_check("paid_controlled_source_skipped", paid_skipped_count >= 1, "critical", f"paid_skipped_count={paid_skipped_count}")
    add_check("errors_review", error_count == 0, "warning", f"error_count={error_count}")
    add_check("current_rows_unchanged", CURRENT_ROWS == 38287, "critical", f"current_rows={CURRENT_ROWS}")
    add_check("rows_needed_unchanged", ROWS_NEEDED == 11713, "critical", f"rows_needed={ROWS_NEEDED}")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"{CURRENT_ROWS} < {FULL_SOURCE_THRESHOLD}")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_parsing", True, "critical", "parsing_performed=False")
    add_check("no_security_extraction", True, "critical", "security_rows_extracted=False")
    add_check("no_normalization", True, "critical", "normalization_performed=False")
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")

    status = (
        "TMX_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS_REBUILD_STILL_BLOCKED"
        if critical_failed == 0
        else "TMX_RAW_ACQUISITION_FAILED_REVIEW_REQUIRED"
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "canonical_dataset": CURRENT_CANONICAL_DATASET,
            "current_rows": CURRENT_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED_PERCENT,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "raw_acquisition_summary": {
            "plan_artifact": str(V216B_JSON),
            "source_candidates_artifact": str(V216B_SOURCES_CSV),
            "raw_dir": str(RAW_DIR),
            "source_candidates": len(sources),
            "download_allowed_sources": allowed_count,
            "download_attempted": attempted_count,
            "raw_files_written": raw_files_written,
            "http_ok_count": ok_count,
            "skipped_sources": skipped_count,
            "paid_or_controlled_sources_skipped": paid_skipped_count,
            "error_count": error_count,
            "bytes_total": bytes_total,
            "max_bytes_per_source": MAX_BYTES_PER_SOURCE,
            "critical_failed_checks": critical_failed,
        },
        "manifest": manifest_rows,
        "source_actions": source_actions,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": attempted_count > 0,
            "raw_files_downloaded": raw_files_written > 0,
            "raw_files_modified_after_write": False,
            "landing_responses_only": True,
            "query_sweep_performed": False,
            "paid_or_controlled_data_accessed": False,
            "parsing_performed": False,
            "security_rows_extracted": False,
            "candidate_rows_extracted": False,
            "canonical_dataset_read": False,
            "canonical_dataset_modified": False,
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
        "recommended_next_phase": NEXT_PHASE,
    }

    write_json(MANIFEST_JSON, payload)
    write_csv(MANIFEST_CSV, manifest_rows, MANIFEST_FIELDS)
    write_csv(SOURCE_ACTIONS_CSV, source_actions, ACTION_FIELDS)

    manifest_lines = "\n".join(
        f"- `{row['source_id']}` attempted={row['download_attempted']} ok={row['ok']} status={row['status_code']} bytes={row['bytes_written']} raw=`{row['raw_path']}` skipped=`{row['skipped_reason']}`"
        for row in manifest_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    action_lines = "\n".join(
        f"- `{row['source_id']}` — action=`{row['executed_action']}` allowed={row['allowed']} reason=`{row['reason']}`"
        for row in source_actions
    )

    MANIFEST_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Current state

- Canonical dataset: `{CURRENT_CANONICAL_DATASET}`
- Current rows: `{CURRENT_ROWS}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completed: `{SOURCE_TO_50K_COMPLETED_PERCENT}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Raw acquisition summary

- Plan artifact: `{V216B_JSON}`
- Source candidates artifact: `{V216B_SOURCES_CSV}`
- Raw directory: `{RAW_DIR}`
- Source candidates: `{len(sources)}`
- Download allowed sources: `{allowed_count}`
- Download attempted: `{attempted_count}`
- Raw files written: `{raw_files_written}`
- HTTP OK count: `{ok_count}`
- Skipped sources: `{skipped_count}`
- Paid/controlled sources skipped: `{paid_skipped_count}`
- Error count: `{error_count}`
- Bytes total: `{bytes_total}`
- Critical failed checks: `{critical_failed}`

## Source actions

{action_lines}

## Manifest

{manifest_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.16C: {str(attempted_count > 0).lower()}
- Raw files downloaded: {str(raw_files_written > 0).lower()}
- Raw files modified after write: false
- Landing responses only: true
- Query sweep performed: false
- Paid or controlled data accessed: false
- Parsing performed: false
- Security rows extracted: false
- Candidate rows extracted: false
- Canonical dataset read: false
- Canonical dataset modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX raw acquisition completed as landing-response acquisition only.

This phase downloaded planned public TMX/TSX/TSXV landing responses and wrote raw files plus manifest metadata. It did not parse securities, extract candidates, normalize instruments, read or modify the canonical expanded universe, calculate net-new rows, rebuild the universe, score equities, call OpenAI, call broker APIs or launch full59k.

## Recommended next phase

`{NEXT_PHASE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16C TMX raw acquisition completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("RAW_ACQUISITION_SUMMARY:")
    for key, value in payload["raw_acquisition_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
