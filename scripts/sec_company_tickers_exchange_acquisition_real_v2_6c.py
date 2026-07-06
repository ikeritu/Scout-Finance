from __future__ import annotations

import csv
import hashlib
import json
import os
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.6C"
METHOD = "sec_company_tickers_exchange_acquisition_real_v1"

PROVIDER_ID = "sec_company_tickers_exchange"
PROVIDER_NAME = "SEC company_tickers_exchange.json"
SEC_SOURCE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"

PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID
RAW_JSON = PROVIDER_DIR / "company_tickers_exchange.json"
NORMALIZED_CSV = PROVIDER_DIR / "sec_company_tickers_exchange.csv"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "sec_company_tickers_exchange_acquisition_real_v2_6c.json"
OUT_MD = OUT_DIR / "sec_company_tickers_exchange_acquisition_real_v2_6c.md"
OUT_SAMPLE_CSV = OUT_DIR / "sec_company_tickers_exchange_sample_v2_6c.csv"
OUT_ISSUES_CSV = OUT_DIR / "sec_company_tickers_exchange_issues_v2_6c.csv"
OUT_DUPLICATES_CSV = OUT_DIR / "sec_company_tickers_exchange_duplicates_v2_6c.csv"

PLAN_JSON = OUT_DIR / "sec_company_tickers_exchange_acquisition_plan_v2_6b.json"

USER_AGENT_ENV = "SCOUT_FINANCE_SEC_USER_AGENT"
TIMEOUT_SECONDS = 30

EXPECTED_FIELDS = ["cik", "name", "ticker", "exchange"]

CURRENT_INCLUDED_ROWS = 5648
TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def fetch_sec_json(url: str, user_agent: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept-Encoding": "identity",
            "Accept": "application/json,text/plain,*/*",
            "Host": "www.sec.gov",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            headers = dict(response.headers.items())
            text = raw.decode("utf-8", errors="replace")

            return {
                "ok": True,
                "status_code": getattr(response, "status", None),
                "reason": getattr(response, "reason", None),
                "headers": headers,
                "content_type": headers.get("Content-Type", ""),
                "raw": raw,
                "text": text,
                "size_bytes": len(raw),
                "sha256": sha256_bytes(raw),
                "error": None,
            }

    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read()
        except Exception:
            raw = b""

        return {
            "ok": False,
            "status_code": exc.code,
            "reason": exc.reason,
            "headers": dict(exc.headers.items()) if exc.headers else {},
            "content_type": exc.headers.get("Content-Type", "") if exc.headers else "",
            "raw": raw,
            "text": raw.decode("utf-8", errors="replace") if raw else "",
            "size_bytes": len(raw),
            "sha256": sha256_bytes(raw) if raw else None,
            "error": f"HTTPError {exc.code}: {exc.reason}",
        }

    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "reason": None,
            "headers": {},
            "content_type": "",
            "raw": b"",
            "text": "",
            "size_bytes": 0,
            "sha256": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def parse_sec_payload(text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = json.loads(text)
    except Exception as exc:
        return None, f"JSON parse failed: {type(exc).__name__}: {exc}"

    if not isinstance(parsed, dict):
        return None, f"Unexpected JSON root type: {type(parsed).__name__}"

    return parsed, None


def normalize_exchange(value: str) -> str:
    value = (value or "").strip()

    aliases = {
        "Nasdaq": "NASDAQ",
        "NASDAQ": "NASDAQ",
        "NYSE": "NYSE",
        "NYSE American": "NYSE American",
        "NYSE Arca": "NYSE Arca",
        "Cboe BZX": "Cboe BZX",
    }

    return aliases.get(value, value)


def normalize_rows(payload: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []

    fields = payload.get("fields")
    data = payload.get("data")

    if not isinstance(fields, list):
        errors.append("Missing or invalid top-level fields list.")
        return [], errors

    if not isinstance(data, list):
        errors.append("Missing or invalid top-level data list.")
        return [], errors

    field_names = [str(field).strip() for field in fields]
    missing = [field for field in EXPECTED_FIELDS if field not in field_names]

    if missing:
        errors.append(f"Missing expected SEC fields: {missing}")
        return [], errors

    indexes = {field: field_names.index(field) for field in EXPECTED_FIELDS}

    normalized: list[dict[str, str]] = []

    for row in data:
        if not isinstance(row, list):
            continue

        try:
            raw_cik = str(row[indexes["cik"]]).strip()
            company_name = str(row[indexes["name"]]).strip()
            ticker = str(row[indexes["ticker"]]).strip().upper()
            raw_exchange = str(row[indexes["exchange"]]).strip()
        except Exception:
            continue

        exchange = normalize_exchange(raw_exchange)

        normalized.append(
            {
                "ticker": ticker,
                "company_name": company_name,
                "exchange": exchange,
                "country": "USA",
                "source_provider": PROVIDER_ID,
                "source_file": rel(RAW_JSON),
                "instrument_type": "UNKNOWN_PENDING_CLASSIFICATION",
                "instrument_scope": "UNKNOWN_PENDING_CLASSIFICATION",
                "classification_confidence": "LOW",
                "classification_reason": "SEC company_tickers_exchange provides ticker/exchange/CIK mapping; instrument type requires downstream classification.",
                "sector": "",
                "industry": "",
                "market_cap": "",
                "raw_cik": raw_cik,
                "raw_exchange": raw_exchange,
            }
        )

    return normalized, errors


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    plan = read_json(PLAN_JSON)

    if not plan.get("_exists"):
        blockers.append(f"Missing v2.6B plan artifact: {rel(PLAN_JSON)}")
    else:
        positives.append(f"v2.6B plan artifact found: {rel(PLAN_JSON)}")

    plan_status = plan.get("plan_status")
    if plan_status == "SEC_COMPANY_TICKERS_EXCHANGE_PLAN_READY":
        positives.append(f"v2.6B plan status accepted: {plan_status}")
    else:
        blockers.append(f"Unexpected v2.6B plan status: {plan_status}")

    user_agent = os.environ.get(USER_AGENT_ENV, "").strip()

    if not user_agent:
        blockers.append(f"Missing required environment variable: {USER_AGENT_ENV}")
    elif "@" not in user_agent:
        warnings.append(f"SEC User-Agent does not appear to include contact email: {user_agent}")
    else:
        positives.append(f"SEC User-Agent configured via {USER_AGENT_ENV}")

    response: dict[str, Any] = {
        "ok": False,
        "status_code": None,
        "reason": None,
        "headers": {},
        "content_type": "",
        "raw": b"",
        "text": "",
        "size_bytes": 0,
        "sha256": None,
        "error": "Skipped because blockers exist before network request.",
    }

    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    normalized_rows: list[dict[str, str]] = []
    normalization_errors: list[str] = []

    if not blockers:
        response = fetch_sec_json(SEC_SOURCE_URL, user_agent)

        if response.get("raw"):
            RAW_JSON.write_bytes(response["raw"])
            positives.append(f"Raw SEC JSON response written: {rel(RAW_JSON)}")

        if response.get("ok"):
            positives.append(f"SEC download succeeded: {SEC_SOURCE_URL}")
        else:
            blockers.append(f"SEC download failed: {response.get('error')}")

        if response.get("text"):
            parsed, parse_error = parse_sec_payload(str(response["text"]))
            if parse_error:
                blockers.append(parse_error)
            elif parsed is not None:
                positives.append("SEC JSON parsed successfully.")

        if parsed is not None:
            normalized_rows, normalization_errors = normalize_rows(parsed)

            if normalization_errors:
                blockers.extend(normalization_errors)

            if normalized_rows:
                canonical_columns = [
                    "ticker",
                    "company_name",
                    "exchange",
                    "country",
                    "source_provider",
                    "source_file",
                    "instrument_type",
                    "instrument_scope",
                    "classification_confidence",
                    "classification_reason",
                    "sector",
                    "industry",
                    "market_cap",
                    "raw_cik",
                    "raw_exchange",
                ]
                write_csv(NORMALIZED_CSV, normalized_rows, canonical_columns)
                write_csv(OUT_SAMPLE_CSV, normalized_rows[:50], canonical_columns)
                positives.append(f"Normalized SEC CSV written: {rel(NORMALIZED_CSV)}")
                positives.append(f"SEC sample CSV written: {rel(OUT_SAMPLE_CSV)}")
            else:
                warnings.append("No normalized SEC rows produced.")

    fields = parsed.get("fields", []) if isinstance(parsed, dict) else []
    data = parsed.get("data", []) if isinstance(parsed, dict) else []

    field_names = [str(field) for field in fields] if isinstance(fields, list) else []
    row_count = len(normalized_rows)

    empty_ticker = 0
    empty_name = 0
    empty_exchange = 0
    empty_cik = 0

    issues: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    key_counter: Counter[tuple[str, str]] = Counter()

    exchange_counts: Counter[str] = Counter()
    raw_exchange_counts: Counter[str] = Counter()

    for index, row in enumerate(normalized_rows, start=1):
        ticker = row.get("ticker", "").strip()
        name = row.get("company_name", "").strip()
        exchange = row.get("exchange", "").strip()
        raw_exchange = row.get("raw_exchange", "").strip()
        cik = row.get("raw_cik", "").strip()

        exchange_counts[exchange] += 1
        raw_exchange_counts[raw_exchange] += 1

        if not ticker:
            empty_ticker += 1
            issues.append({"row_number": index, "issue_type": "EMPTY_TICKER", "ticker": ticker, "exchange": exchange})
        if not name:
            empty_name += 1
            issues.append({"row_number": index, "issue_type": "EMPTY_NAME", "ticker": ticker, "exchange": exchange})
        if not exchange:
            empty_exchange += 1
            issues.append({"row_number": index, "issue_type": "EMPTY_EXCHANGE", "ticker": ticker, "exchange": exchange})
        if not cik:
            empty_cik += 1
            issues.append({"row_number": index, "issue_type": "EMPTY_CIK", "ticker": ticker, "exchange": exchange})

        if ticker and exchange:
            key_counter[(exchange, ticker)] += 1

    duplicate_keys = {key: count for key, count in key_counter.items() if count > 1}

    for (exchange, ticker), count in duplicate_keys.items():
        duplicate_rows.append(
            {
                "exchange": exchange,
                "ticker": ticker,
                "duplicate_count": count,
            }
        )

    write_csv(
        OUT_ISSUES_CSV,
        issues,
        ["row_number", "issue_type", "ticker", "exchange"],
    )

    write_csv(
        OUT_DUPLICATES_CSV,
        duplicate_rows,
        ["exchange", "ticker", "duplicate_count"],
    )

    if empty_ticker:
        warnings.append(f"Empty ticker values detected: {empty_ticker}")
    if empty_name:
        warnings.append(f"Empty company names detected: {empty_name}")
    if empty_exchange:
        warnings.append(f"Empty exchange values detected: {empty_exchange}")
    if empty_cik:
        warnings.append(f"Empty CIK values detected: {empty_cik}")

    if duplicate_keys:
        warnings.append(f"Duplicate exchange+ticker keys detected: {len(duplicate_keys)}")
    elif normalized_rows:
        positives.append("No duplicate exchange+ticker keys detected in SEC normalized rows.")

    if row_count:
        positives.append(f"SEC normalized row count: {row_count}")

    rows_needed_first_expansion_before = max(TARGET_FIRST_EXPANSION_ROWS - CURRENT_INCLUDED_ROWS, 0)
    rows_needed_full_source_before = max(MIN_FULL_SOURCE_ROWS - CURRENT_INCLUDED_ROWS, 0)

    if blockers:
        acquisition_status = "SEC_COMPANY_TICKERS_EXCHANGE_ACQUISITION_BLOCKED"
        readiness_score = 0
    elif row_count > 0:
        acquisition_status = "SEC_COMPANY_TICKERS_EXCHANGE_ACQUISITION_COMPLETED"
        readiness_score = 85
        warnings.append("SEC source is acquired and normalized, but must be validated before rebuild or merge.")
    else:
        acquisition_status = "SEC_COMPANY_TICKERS_EXCHANGE_ACQUISITION_NO_ROWS"
        readiness_score = 40
        warnings.append("SEC acquisition produced no rows.")

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "acquisition_status": acquisition_status,
        "readiness_score": readiness_score,
        "provider": {
            "provider_id": PROVIDER_ID,
            "provider_name": PROVIDER_NAME,
            "source_url": SEC_SOURCE_URL,
            "provider_dir": rel(PROVIDER_DIR),
            "raw_json": rel(RAW_JSON) if RAW_JSON.exists() else None,
            "normalized_csv": rel(NORMALIZED_CSV) if NORMALIZED_CSV.exists() else None,
            "sample_csv": rel(OUT_SAMPLE_CSV) if OUT_SAMPLE_CSV.exists() else None,
        },
        "network": {
            "network_download_performed": not bool(blockers and response.get("error") == "Skipped because blockers exist before network request."),
            "status_ok": bool(response.get("ok")),
            "status_code": response.get("status_code"),
            "reason": response.get("reason"),
            "content_type": response.get("content_type"),
            "size_bytes": response.get("size_bytes"),
            "sha256": response.get("sha256"),
            "timeout_seconds": TIMEOUT_SECONDS,
            "user_agent_env": USER_AGENT_ENV,
            "user_agent_present": bool(user_agent),
            "error": response.get("error"),
        },
        "schema": {
            "expected_fields": EXPECTED_FIELDS,
            "detected_fields": field_names,
            "missing_expected_fields": [field for field in EXPECTED_FIELDS if field not in field_names],
            "raw_data_records": len(data) if isinstance(data, list) else 0,
        },
        "summary": {
            "normalized_rows": row_count,
            "empty_tickers": empty_ticker,
            "empty_company_names": empty_name,
            "empty_exchanges": empty_exchange,
            "empty_ciks": empty_cik,
            "duplicate_exchange_ticker_keys": len(duplicate_keys),
            "exchange_counts": dict(exchange_counts),
            "raw_exchange_counts": dict(raw_exchange_counts),
            "rows_needed_first_expansion_before_sec": rows_needed_first_expansion_before,
            "rows_needed_full_source_before_sec": rows_needed_full_source_before,
        },
        "outputs": {
            "issues_csv": rel(OUT_ISSUES_CSV),
            "duplicates_csv": rel(OUT_DUPLICATES_CSV),
        },
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
        },
        "recommendation": (
            "Proceed to v2.6D SEC validation before any rebuild or merge."
            if not blockers and row_count > 0
            else "Resolve blockers before SEC validation."
            if blockers
            else "Inspect SEC payload because no rows were produced."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.6C SEC Company Tickers Exchange Acquisition Real")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Acquisition status: **{acquisition_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Provider: **{PROVIDER_NAME}**")
    md.append(f"- Source URL: `{SEC_SOURCE_URL}`")
    md.append(f"- Network status OK: {bool(response.get('ok'))}")
    md.append(f"- HTTP status code: {response.get('status_code')}")
    md.append(f"- Content type: `{response.get('content_type')}`")
    md.append(f"- Size bytes: {response.get('size_bytes')}")
    md.append(f"- SHA256: `{response.get('sha256')}`")
    md.append(f"- Raw JSON: `{rel(RAW_JSON) if RAW_JSON.exists() else None}`")
    md.append(f"- Normalized CSV: `{rel(NORMALIZED_CSV) if NORMALIZED_CSV.exists() else None}`")
    md.append(f"- Normalized rows: {row_count}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("")
    md.append("## Schema")
    md.append("")
    md.append(f"- Expected fields: {EXPECTED_FIELDS}")
    md.append(f"- Detected fields: {field_names}")
    md.append(f"- Raw data records: {len(data) if isinstance(data, list) else 0}")
    md.append("")
    md.append("## Data quality summary")
    md.append("")
    md.append(f"- Empty tickers: {empty_ticker}")
    md.append(f"- Empty company names: {empty_name}")
    md.append(f"- Empty exchanges: {empty_exchange}")
    md.append(f"- Empty CIKs: {empty_cik}")
    md.append(f"- Duplicate exchange+ticker keys: {len(duplicate_keys)}")
    md.append("")
    md.append("## Exchange counts")
    md.append("")
    if exchange_counts:
        for exchange, count in exchange_counts.most_common():
            md.append(f"- {exchange}: {count}")
    else:
        md.append("- No exchange counts available.")
    md.append("")
    md.append("## Positives")
    md.append("")
    if positives:
        for item in positives:
            md.append(f"- {item}")
    else:
        md.append("- No positives detected.")
    md.append("")
    md.append("## Blockers")
    md.append("")
    if blockers:
        for item in blockers:
            md.append(f"- {item}")
    else:
        md.append("- No blockers detected.")
    md.append("")
    md.append("## Warnings")
    md.append("")
    if warnings:
        for item in warnings:
            md.append(f"- {item}")
    else:
        md.append("- No warnings detected.")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.6C is an isolated SEC provider acquisition step. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.6C SEC Company Tickers Exchange Acquisition Real")
    print("=" * 92)
    print(f"OK   Acquisition status: {acquisition_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Network status OK: {bool(response.get('ok'))}")
    print(f"OK   HTTP status code: {response.get('status_code')}")
    print(f"OK   Source URL: {SEC_SOURCE_URL}")
    print(f"OK   Raw JSON: {RAW_JSON if RAW_JSON.exists() else None}")
    print(f"OK   Normalized CSV: {NORMALIZED_CSV if NORMALIZED_CSV.exists() else None}")
    print(f"OK   Normalized rows: {row_count}")
    print(f"OK   Duplicate exchange+ticker keys: {len(duplicate_keys)}")
    print(f"OK   Empty tickers: {empty_ticker}")
    print(f"OK   Empty exchanges: {empty_exchange}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Issues CSV written: {OUT_ISSUES_CSV}")
    print(f"OK   Duplicates CSV written: {OUT_DUPLICATES_CSV}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
