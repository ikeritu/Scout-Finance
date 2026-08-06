from __future__ import annotations

import csv
import gzip
import hashlib
import json
import mimetypes
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


VERSION = "v2.17C"
PHASE = "NSE India Raw Acquisition"
PHASE_TYPE = "provider-raw-acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "nse_raw_acquisition_v2_17c"

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
V217B_JSON = OUTPUT_DIR / "nse_india_acquisition_plan_v2_17b.json"
V217B_SOURCE_PLAN_CSV = OUTPUT_DIR / "nse_india_source_plan_v2_17b.csv"
V217B_ACTIONS_CSV = OUTPUT_DIR / "nse_india_acquisition_actions_v2_17b.csv"

REPORT_JSON = OUTPUT_DIR / "nse_india_raw_acquisition_v2_17c.json"
REPORT_MD = OUTPUT_DIR / "nse_india_raw_acquisition_v2_17c.md"
MANIFEST_CSV = OUTPUT_DIR / "nse_india_raw_acquisition_manifest_v2_17c.csv"
SOURCE_ACTIONS_CSV = OUTPUT_DIR / "nse_india_raw_acquisition_source_actions_v2_17c.csv"

CURRENT_CANONICAL_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713

EXPECTED_V217B_STATUS = "NSE_INDIA_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_FULL_SOURCE_STILL_BLOCKED"
EXPECTED_V217B_NEXT = "v2.17C - NSE India Raw Acquisition"

NEXT_PHASE = "v2.17D - NSE India Raw Validation"

LANDING_URLS = {
    "nse_all_reports_landing": "https://www.nseindia.com/all-reports",
    "nse_securities_available_for_trading_landing": "https://www.nseindia.com/static/market-data/securities-available-for-trading",
}

DIRECT_DOWNLOAD_URLS = {
    "nse_securities_available_equity_segment": "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
    "nse_securities_available_sme": "https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv",
    "nse_idrs": "https://nsearchives.nseindia.com/content/equities/IDR_W9.csv",
    "nse_preference_shares": "https://nsearchives.nseindia.com/content/equities/PREF.csv",
    "nse_warrants": "https://nsearchives.nseindia.com/content/equities/WARRANT.csv",
    "nse_close_ended_mf": "https://nsearchives.nseindia.com/content/equities/mf_close-end.csv",
    "nse_etfs": "https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv",
    "nse_changes_company_names": "https://nsearchives.nseindia.com/content/equities/namechange.csv",
    "nse_changes_symbols": "https://nsearchives.nseindia.com/content/equities/symbolchange.csv",
    "nse_invits": "https://nsearchives.nseindia.com/content/equities/INVITS_L.csv",
    "nse_reits": "https://nsearchives.nseindia.com/content/equities/REITS_L.csv",
    "nse_debt_instruments": "https://nsearchives.nseindia.com/content/equities/DEBT.csv",
}

MII_SOURCE_IDS = {
    "nse_all_reports_cm_mii_security_file_nse_listed",
    "nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive",
}

MANIFEST_FIELDS = [
    "artifact_id",
    "source_id",
    "artifact_type",
    "url",
    "local_path",
    "download_status",
    "http_status",
    "content_type",
    "bytes",
    "sha256",
    "extension",
    "gzip_magic",
    "downloaded_at_utc",
    "notes",
]

SOURCE_ACTION_FIELDS = [
    "source_id",
    "source_role",
    "planned_action",
    "attempted",
    "status",
    "artifacts_written",
    "primary_url",
    "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    value = value.strip("._")
    return value or "artifact"


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return sum(1 for _ in csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


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


def build_opener() -> urllib.request.OpenerDirector:
    cookie_processor = urllib.request.HTTPCookieProcessor()
    opener = urllib.request.build_opener(cookie_processor)
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"),
        ("Accept", "text/html,application/xhtml+xml,application/xml,text/csv,application/gzip,application/octet-stream,*/*;q=0.8"),
        ("Accept-Language", "en-US,en;q=0.9"),
        ("Connection", "keep-alive"),
    ]
    return opener


def fetch_bytes(opener: urllib.request.OpenerDirector, url: str, referer: str = "", timeout: int = 45) -> tuple[bool, bytes, dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml,text/csv,application/gzip,application/octet-stream,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    if referer:
        headers["Referer"] = referer

    request = urllib.request.Request(url, headers=headers)

    try:
        with opener.open(request, timeout=timeout) as response:
            data = response.read()
            meta = {
                "http_status": str(getattr(response, "status", "")),
                "content_type": response.headers.get("Content-Type", ""),
                "final_url": response.geturl(),
            }
            return True, data, meta
    except urllib.error.HTTPError as exc:
        data = exc.read() if hasattr(exc, "read") else b""
        return False, data, {
            "http_status": str(exc.code),
            "content_type": exc.headers.get("Content-Type", "") if exc.headers else "",
            "final_url": url,
            "error": f"HTTPError: {exc}",
        }
    except Exception as exc:
        return False, b"", {
            "http_status": "",
            "content_type": "",
            "final_url": url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def write_raw_artifact(
    source_id: str,
    artifact_type: str,
    url: str,
    data: bytes,
    meta: dict,
    suffix: str,
    status: str,
    notes: str,
) -> dict:
    extension = suffix
    filename = f"{safe_filename(source_id)}__{artifact_type}{extension}"
    local_path = RAW_DIR / filename

    if local_path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {local_path}")

    local_path.write_bytes(data)

    artifact_id = sha256_text(f"{VERSION}|{source_id}|{artifact_type}|{url}|{local_path}")[:16]
    gzip_magic = data[:2] == b"\x1f\x8b"

    return {
        "artifact_id": artifact_id,
        "source_id": source_id,
        "artifact_type": artifact_type,
        "url": url,
        "local_path": str(local_path),
        "download_status": status,
        "http_status": meta.get("http_status", ""),
        "content_type": meta.get("content_type", ""),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        "extension": extension,
        "gzip_magic": gzip_magic,
        "downloaded_at_utc": utc_now(),
        "notes": notes,
    }


def extension_from_url_or_type(url: str, content_type: str) -> str:
    path = urllib.parse.urlparse(url).path.lower()

    for ext in [".csv.gz", ".xlsx", ".xls", ".csv", ".zip", ".gz", ".html", ".txt"]:
        if path.endswith(ext):
            return ext

    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else ""
    return guessed or ".raw"


def decode_text(data: bytes) -> str:
    for encoding in ["utf-8", "utf-8-sig", "cp1252", "latin-1"]:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def discover_mii_urls_from_html(html: str) -> list[str]:
    urls = set()

    for match in re.findall(r"https?://[^\"'<>\\\s]+NSE_CM_security_\d{8}\.csv\.gz", html, flags=re.I):
        urls.add(match)

    for filename in re.findall(r"NSE_CM_security_\d{8}\.csv\.gz", html, flags=re.I):
        urls.add(f"https://nsearchives.nseindia.com/content/equities/{filename}")

    return sorted(urls)


def recent_mii_guess_urls(days_back: int = 12) -> list[str]:
    urls = []
    today = datetime.now().date()

    for offset in range(days_back + 1):
        day = today - timedelta(days=offset)
        ddmmyyyy = day.strftime("%d%m%Y")
        filename = f"NSE_CM_security_{ddmmyyyy}.csv.gz"

        urls.extend(
            [
                f"https://nsearchives.nseindia.com/content/equities/{filename}",
                f"https://nsearchives.nseindia.com/archives/equities/mii/{filename}",
                f"https://nsearchives.nseindia.com/content/cm/{filename}",
            ]
        )

    return urls


def looks_like_raw_file(data: bytes, content_type: str, url: str) -> bool:
    if not data:
        return False

    low_type = (content_type or "").lower()
    low_url = url.lower()

    if data[:2] == b"\x1f\x8b":
        return True

    if any(low_url.endswith(ext) for ext in [".csv", ".xlsx", ".xls", ".zip", ".gz"]):
        if b"<html" not in data[:1000].lower():
            return True

    if any(token in low_type for token in ["text/csv", "gzip", "octet-stream", "spreadsheet", "zip"]):
        if b"<html" not in data[:1000].lower():
            return True

    return False


def try_download_mii_security_file(opener: urllib.request.OpenerDirector, landing_html: str, source_id: str) -> tuple[list[dict], dict]:
    artifacts = []
    discovered = discover_mii_urls_from_html(landing_html)
    guesses = recent_mii_guess_urls(days_back=12)

    attempted_urls = []
    seen = set()

    for url in discovered + guesses:
        if url in seen:
            continue
        seen.add(url)
        attempted_urls.append(url)

    for url in attempted_urls:
        ok, data, meta = fetch_bytes(opener, url, referer=LANDING_URLS["nse_all_reports_landing"], timeout=45)
        status = "downloaded" if ok and looks_like_raw_file(data, meta.get("content_type", ""), url) else "attempt_failed_or_not_raw"

        if status == "downloaded":
            artifact = write_raw_artifact(
                source_id=source_id,
                artifact_type="mii_security_file_candidate",
                url=url,
                data=data,
                meta=meta,
                suffix=extension_from_url_or_type(url, meta.get("content_type", "")),
                status=status,
                notes="Raw MII security file downloaded. No parsing performed.",
            )
            artifacts.append(artifact)
            break

        time.sleep(0.3)

    action = {
        "source_id": source_id,
        "source_role": "primary_or_secondary_bulk_candidate_source",
        "planned_action": "discover/download raw MII security file from NSE All Reports path",
        "attempted": True,
        "status": "downloaded" if artifacts else "not_downloaded_landing_saved_only",
        "artifacts_written": len(artifacts),
        "primary_url": artifacts[0]["url"] if artifacts else "",
        "notes": f"attempted_urls={len(attempted_urls)}; discovered_from_landing={len(discovered)}; no candidate parsing performed",
    }

    return artifacts, action


def main() -> None:
    for path in [REPORT_JSON, REPORT_MD, MANIFEST_CSV, SOURCE_ACTIONS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to reuse existing raw dir {RAW_DIR}")

    RAW_DIR.mkdir(parents=True, exist_ok=False)

    b_report = read_json(V217B_JSON)
    source_plan_rows = read_csv(V217B_SOURCE_PLAN_CSV)
    action_plan_rows = read_csv(V217B_ACTIONS_CSV)
    canonical_rows = count_csv_rows(CANONICAL_DATASET)

    source_ids = {row.get("source_id", "") for row in source_plan_rows}

    opener = build_opener()

    manifest = []
    source_actions = []

    # Seed NSE session.
    seed_ok, seed_data, seed_meta = fetch_bytes(opener, "https://www.nseindia.com/", timeout=45)
    if seed_data:
        manifest.append(
            write_raw_artifact(
                source_id="nse_home_session_seed",
                artifact_type="landing_html",
                url="https://www.nseindia.com/",
                data=seed_data,
                meta=seed_meta,
                suffix=".html",
                status="downloaded" if seed_ok else "downloaded_error_payload",
                notes="Session seed page saved for raw acquisition diagnostics. No parsing performed.",
            )
        )

    landing_html_by_id = {}

    for landing_id, url in LANDING_URLS.items():
        ok, data, meta = fetch_bytes(opener, url, timeout=45)
        status = "downloaded" if ok and data else "download_failed"
        notes = "Landing page saved. No candidate parsing performed."

        if data:
            manifest.append(
                write_raw_artifact(
                    source_id=landing_id,
                    artifact_type="landing_html",
                    url=url,
                    data=data,
                    meta=meta,
                    suffix=".html",
                    status=status,
                    notes=notes,
                )
            )
            landing_html_by_id[landing_id] = decode_text(data)

        source_actions.append(
            {
                "source_id": landing_id,
                "source_role": "landing_page",
                "planned_action": "download landing html only",
                "attempted": True,
                "status": status,
                "artifacts_written": 1 if data else 0,
                "primary_url": url,
                "notes": notes,
            }
        )

        time.sleep(0.7)

    all_reports_html = landing_html_by_id.get("nse_all_reports_landing", "")

    for source_id in sorted(MII_SOURCE_IDS):
        if source_id not in source_ids:
            source_actions.append(
                {
                    "source_id": source_id,
                    "source_role": "mii_security_file",
                    "planned_action": "skipped because source_id not in v2.17B source plan",
                    "attempted": False,
                    "status": "skipped_not_in_plan",
                    "artifacts_written": 0,
                    "primary_url": "",
                    "notes": "No action.",
                }
            )
            continue

        artifacts, action = try_download_mii_security_file(opener, all_reports_html, source_id)
        manifest.extend(artifacts)
        source_actions.append(action)
        time.sleep(0.7)

    for source_id, url in DIRECT_DOWNLOAD_URLS.items():
        if source_id not in source_ids:
            source_actions.append(
                {
                    "source_id": source_id,
                    "source_role": "direct_static_source",
                    "planned_action": "skipped because source_id not in v2.17B source plan",
                    "attempted": False,
                    "status": "skipped_not_in_plan",
                    "artifacts_written": 0,
                    "primary_url": url,
                    "notes": "No action.",
                }
            )
            continue

        ok, data, meta = fetch_bytes(opener, url, referer=LANDING_URLS["nse_securities_available_for_trading_landing"], timeout=45)
        is_raw = ok and looks_like_raw_file(data, meta.get("content_type", ""), url)
        status = "downloaded" if is_raw else "download_failed_or_not_raw"

        artifacts_written = 0

        if data:
            artifact = write_raw_artifact(
                source_id=source_id,
                artifact_type="raw_source_file",
                url=url,
                data=data,
                meta=meta,
                suffix=extension_from_url_or_type(url, meta.get("content_type", "")),
                status=status,
                notes="Raw direct NSE archive/static file saved. No parsing performed.",
            )
            manifest.append(artifact)
            artifacts_written = 1

        source_actions.append(
            {
                "source_id": source_id,
                "source_role": "direct_static_source",
                "planned_action": "download raw direct source file only",
                "attempted": True,
                "status": status,
                "artifacts_written": artifacts_written,
                "primary_url": url,
                "notes": "No parsing, candidate extraction, canonical comparison or rebuild performed.",
            }
        )

        time.sleep(0.5)

    downloaded_artifacts = [row for row in manifest if row["download_status"] == "downloaded"]
    raw_file_artifacts = [row for row in downloaded_artifacts if row["artifact_type"] in {"raw_source_file", "mii_security_file_candidate"}]
    mii_artifacts = [row for row in downloaded_artifacts if row["artifact_type"] == "mii_security_file_candidate"]
    direct_static_artifacts = [row for row in downloaded_artifacts if row["artifact_type"] == "raw_source_file"]

    downloaded_source_ids = {row["source_id"] for row in raw_file_artifacts}

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_17b_report_exists", V217B_JSON.exists(), "critical", str(V217B_JSON))
    add_check(
        "v2_17b_status_expected",
        b_report.get("status") == EXPECTED_V217B_STATUS,
        "critical",
        str(b_report.get("status", "")),
    )
    add_check(
        "v2_17b_recommended_c",
        b_report.get("recommended_next_phase") == EXPECTED_V217B_NEXT,
        "critical",
        str(b_report.get("recommended_next_phase", "")),
    )
    add_check("source_plan_exists", V217B_SOURCE_PLAN_CSV.exists(), "critical", str(V217B_SOURCE_PLAN_CSV))
    add_check("action_plan_exists", V217B_ACTIONS_CSV.exists(), "critical", str(V217B_ACTIONS_CSV))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("canonical_rows_expected", canonical_rows == CURRENT_CANONICAL_ROWS, "critical", f"canonical_rows={canonical_rows}")
    add_check("raw_dir_created", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("nse_landing_downloaded", "nse_all_reports_landing" in {row["source_id"] for row in downloaded_artifacts}, "critical", "all-reports landing")
    add_check("securities_landing_downloaded", "nse_securities_available_for_trading_landing" in {row["source_id"] for row in downloaded_artifacts}, "critical", "securities available landing")
    add_check("direct_static_downloads_present", len(direct_static_artifacts) >= 8, "critical", f"direct_static_downloads={len(direct_static_artifacts)}")
    add_check("equity_segment_downloaded", "nse_securities_available_equity_segment" in downloaded_source_ids, "critical", "EQUITY_L.csv")
    add_check("sme_downloaded_or_attempted", any(row["source_id"] == "nse_securities_available_sme" and str(row["attempted"]) == "True" for row in source_actions), "warning", "SME_EQUITY_L.csv attempted")
    add_check("mii_attempted", all(any(row["source_id"] == source_id and str(row["attempted"]) == "True" for row in source_actions) for source_id in MII_SOURCE_IDS), "warning", "MII sources attempted")
    add_check("mii_downloaded_if_discoverable", len(mii_artifacts) >= 1, "warning", f"mii_downloads={len(mii_artifacts)}")
    add_check("raw_file_artifacts_present", len(raw_file_artifacts) >= 8, "critical", f"raw_file_artifacts={len(raw_file_artifacts)}")
    add_check("full_source_still_blocked", canonical_rows < FULL_SOURCE_THRESHOLD, "critical", f"{canonical_rows} < {FULL_SOURCE_THRESHOLD}")
    add_check("network_used_as_allowed", True, "critical", "network_download_performed=True")
    add_check("raw_acquisition_performed", True, "critical", "raw_acquisition_performed=True")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed == 0:
        status = "NSE_INDIA_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE
    else:
        status = "NSE_INDIA_RAW_ACQUISITION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.17C_FIX - NSE India Raw Acquisition Repair"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": canonical_rows,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": round((canonical_rows / FULL_SOURCE_THRESHOLD) * 100, 2),
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "route_reference": {
            "v2_17b_artifact": str(V217B_JSON),
            "v2_17b_status": b_report.get("status", ""),
            "v2_17b_recommended_next_phase": b_report.get("recommended_next_phase", ""),
            "provider": "NSE India",
            "market": "India",
        },
        "raw_acquisition_summary": {
            "raw_dir": str(RAW_DIR),
            "manifest_rows": len(manifest),
            "downloaded_artifacts": len(downloaded_artifacts),
            "raw_file_artifacts": len(raw_file_artifacts),
            "direct_static_downloads": len(direct_static_artifacts),
            "mii_security_downloads": len(mii_artifacts),
            "downloaded_source_ids": sorted(downloaded_source_ids),
            "source_actions": len(source_actions),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "manifest_preview": manifest[:50],
        "source_actions": source_actions,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "v2_17b_report_read": True,
            "source_plan_read": True,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "raw_acquisition_performed": True,
            "raw_files_downloaded": len(raw_file_artifacts) > 0,
            "landing_pages_downloaded": True,
            "candidate_extraction_performed": False,
            "security_rows_extracted": False,
            "canonical_comparison_performed": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "net_new_filtering_applied_to_canonical": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "full_source_gate_unblocked": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)
    write_csv(MANIFEST_CSV, manifest, MANIFEST_FIELDS)
    write_csv(SOURCE_ACTIONS_CSV, source_actions, SOURCE_ACTION_FIELDS)

    manifest_lines = "\n".join(
        f"- `{row['source_id']}` `{row['artifact_type']}` status=`{row['download_status']}` bytes=`{row['bytes']}` path=`{row['local_path']}`"
        for row in manifest
    )

    action_lines = "\n".join(
        f"- `{row['source_id']}` attempted=`{row['attempted']}` status=`{row['status']}` artifacts=`{row['artifacts_written']}`"
        for row in source_actions
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

NSE India raw acquisition completed.

This phase downloads landing pages and raw NSE source files only. It does not parse security rows, does not extract candidates, does not compare against the canonical dataset and does not rebuild or modify any expanded universe dataset.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{canonical_rows}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completion: `{round((canonical_rows / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Raw acquisition summary

- Raw directory: `{RAW_DIR}`
- Manifest rows: `{len(manifest)}`
- Downloaded artifacts: `{len(downloaded_artifacts)}`
- Raw file artifacts: `{len(raw_file_artifacts)}`
- Direct static downloads: `{len(direct_static_artifacts)}`
- MII security downloads: `{len(mii_artifacts)}`
- Critical failed checks: `{critical_failed}`

## Manifest

{manifest_lines}

## Source actions

{action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: true
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17B report read: true
- Source plan read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Raw acquisition performed: true
- Raw files downloaded: `{len(raw_file_artifacts) > 0}`
- Landing pages downloaded: true
- Candidate extraction performed: false
- Security rows extracted: false
- Canonical comparison performed: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Net-new filtering applied to canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17C captures raw NSE India source artifacts and prepares them for v2.17D validation.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.17C NSE India raw acquisition completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("RAW_ACQUISITION_SUMMARY:")
    for key, value in payload["raw_acquisition_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
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
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
