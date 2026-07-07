from __future__ import annotations

import csv
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.9C"
METHOD = "otc_markets_acquisition_real_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
PROVIDER_ID = "otc_markets_stock_screener"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID

PLAN_JSON = OUT_DIR / "otc_markets_acquisition_plan_v2_9b.json"

PAGE_URL = "https://www.otcmarkets.com/research/stock-screener"
CSV_URL = "https://www.otcmarkets.com/research/stock-screener/api/downloadCSV?ce=true&sortField=volume&sortOrder=desc"

RAW_PAGE_HTML = PROVIDER_DIR / "otc_markets_stock_screener_page.html"
RAW_CSV = PROVIDER_DIR / "otc_markets_stock_screener_raw.csv"

OUT_JSON = OUT_DIR / "otc_markets_acquisition_real_v2_9c.json"
OUT_MD = OUT_DIR / "otc_markets_acquisition_real_v2_9c.md"
SCHEMA_PROBE_CSV = OUT_DIR / "otc_markets_schema_probe_v2_9c.csv"
SAMPLE_CSV = OUT_DIR / "otc_markets_sample_v2_9c.csv"

CURRENT_EXPANDED_ROWS = 9200
ROWS_NEEDED_FIRST_EXPANSION = 5800
ROWS_NEEDED_FULL_SOURCE = 40800

REQUEST_TIMEOUT_SECONDS = 45


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def fetch(url: str, out_path: Path, accept: str) -> dict[str, Any]:
    headers = {
        "User-Agent": "ScoutFinanceSourceAcquisition/2.9C (+controlled research use)",
        "Accept": accept,
    }
    request = urllib.request.Request(url, headers=headers, method="GET")

    result: dict[str, Any] = {
        "url": url,
        "target_path": rel(out_path),
        "ok": False,
        "status_code": None,
        "content_type": "",
        "size_bytes": 0,
        "sha256": "",
        "error": "",
    }

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data = response.read()
            result["status_code"] = getattr(response, "status", None)
            result["content_type"] = response.headers.get("Content-Type", "")
            result["size_bytes"] = len(data)
            result["sha256"] = sha256_bytes(data)

            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(data)

            result["ok"] = 200 <= int(result["status_code"] or 0) < 300
            return result

    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        result["status_code"] = exc.code
        result["content_type"] = exc.headers.get("Content-Type", "") if exc.headers else ""
        result["size_bytes"] = len(body)
        result["sha256"] = sha256_bytes(body) if body else ""
        result["error"] = f"HTTPError: {exc}"
        if body:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.with_suffix(out_path.suffix + ".error_body").write_bytes(body)
        return result

    except Exception as exc:
        result["error"] = repr(exc)
        return result


def sniff_csv(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "exists": path.exists(),
        "is_probable_csv": False,
        "row_count": 0,
        "field_count": 0,
        "fields": [],
        "sample_rows_written": 0,
        "schema_probe_written": False,
        "error": "",
    }

    if not path.exists():
        result["error"] = "CSV file does not exist"
        return result

    raw = path.read_bytes()
    if not raw:
        result["error"] = "CSV file is empty"
        return result

    text = raw.decode("utf-8-sig", errors="replace")

    if "<html" in text[:500].lower() or "<!doctype html" in text[:500].lower():
        result["error"] = "Downloaded CSV appears to be HTML"
        return result

    try:
        rows = list(csv.DictReader(text.splitlines()))
        fields = list(rows[0].keys()) if rows else []
        result["row_count"] = len(rows)
        result["field_count"] = len(fields)
        result["fields"] = fields
        result["is_probable_csv"] = bool(fields)
    except Exception as exc:
        result["error"] = repr(exc)
        return result

    with SCHEMA_PROBE_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["field_index", "field_name"])
        for idx, field in enumerate(result["fields"], start=1):
            writer.writerow([idx, field])
    result["schema_probe_written"] = True

    sample_rows = rows[:25]
    if sample_rows and result["fields"]:
        with SAMPLE_CSV.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=result["fields"])
            writer.writeheader()
            writer.writerows(sample_rows)
        result["sample_rows_written"] = len(sample_rows)

    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    plan = read_json(PLAN_JSON)

    if not plan.get("_exists"):
        blockers.append(f"Missing v2.9B plan artifact: {rel(PLAN_JSON)}")
    else:
        positives.append(f"v2.9B plan artifact found: {rel(PLAN_JSON)}")

    plan_status = plan.get("plan_status")
    plan_decision = plan.get("plan_decision")

    if plan_status == "OTC_MARKETS_ACQUISITION_PLAN_READY":
        positives.append(f"v2.9B plan status accepted: {plan_status}")
    else:
        blockers.append(f"Unexpected v2.9B plan status: {plan_status}")

    if plan_decision == "OTC_MARKETS_CONTROLLED_ACQUISITION_APPROVED":
        positives.append(f"v2.9B plan decision accepted: {plan_decision}")
    else:
        blockers.append(f"Unexpected v2.9B plan decision: {plan_decision}")

    request_results: list[dict[str, Any]] = []

    if not blockers:
        page_result = fetch(PAGE_URL, RAW_PAGE_HTML, "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        request_results.append({"route_id": "otc_markets_stock_screener_page_probe", **page_result})

        csv_result = fetch(CSV_URL, RAW_CSV, "text/csv,application/csv,application/octet-stream,*/*;q=0.8")
        request_results.append({"route_id": "otc_markets_stock_screener_download_csv", **csv_result})

        if page_result["ok"]:
            positives.append(f"HTML page downloaded: {rel(RAW_PAGE_HTML)}")
        else:
            warnings.append(f"HTML page download failed or non-2xx: {page_result.get('status_code')} {page_result.get('error')}")

        if csv_result["ok"]:
            positives.append(f"CSV candidate downloaded: {rel(RAW_CSV)}")
        else:
            blockers.append(f"CSV download failed or non-2xx: {csv_result.get('status_code')} {csv_result.get('error')}")

    csv_probe = sniff_csv(RAW_CSV) if RAW_CSV.exists() else {
        "exists": False,
        "is_probable_csv": False,
        "row_count": 0,
        "field_count": 0,
        "fields": [],
        "sample_rows_written": 0,
        "schema_probe_written": False,
        "error": "CSV not available",
    }

    if csv_probe.get("is_probable_csv"):
        positives.append(f"CSV schema detected with {csv_probe['field_count']} fields and {csv_probe['row_count']} rows.")
    else:
        blockers.append(f"CSV schema probe failed: {csv_probe.get('error')}")

    if csv_probe.get("row_count", 0) < ROWS_NEEDED_FIRST_EXPANSION:
        warnings.append(
            f"Raw OTC row count may be insufficient to unlock first expansion before net-new validation: "
            f"{csv_probe.get('row_count', 0)} < {ROWS_NEEDED_FIRST_EXPANSION}"
        )

    warnings.append("v2.9C is acquisition-only. Net-new coverage is not computed until v2.9D.")
    warnings.append("Do not rebuild expanded_universe from v2.9C outputs.")
    warnings.append("Do not use OTC rows downstream until v2.9D validation.")

    if blockers:
        acquisition_status = "OTC_MARKETS_ACQUISITION_COMPLETED_WITH_BLOCKERS"
        readiness_score = 40 if csv_probe.get("exists") else 0
        acquisition_decision = "OTC_MARKETS_ACQUISITION_REQUIRES_REVIEW"
        recommended_next_phase = "Review blockers before v2.9D"
    else:
        acquisition_status = "OTC_MARKETS_ACQUISITION_COMPLETED"
        readiness_score = 85
        acquisition_decision = "OTC_MARKETS_RAW_SOURCE_READY_FOR_VALIDATION"
        recommended_next_phase = "v2.9D ? OTC Markets Validation"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "acquisition_status": acquisition_status,
        "readiness_score": readiness_score,
        "acquisition_decision": acquisition_decision,
        "recommended_next_phase": recommended_next_phase,
        "provider": {
            "provider_id": PROVIDER_ID,
            "provider_dir": rel(PROVIDER_DIR),
            "raw_page_html": rel(RAW_PAGE_HTML),
            "raw_csv": rel(RAW_CSV),
        },
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "rows_needed_first_expansion": ROWS_NEEDED_FIRST_EXPANSION,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
        },
        "request_results": request_results,
        "csv_probe": csv_probe,
        "outputs": {
            "schema_probe_csv": rel(SCHEMA_PROBE_CSV),
            "sample_csv": rel(SAMPLE_CSV),
            "acquisition_json": rel(OUT_JSON),
            "acquisition_md": rel(OUT_MD),
        },
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "network_download_performed": True,
            "network_download_scope": "OTC_MARKETS_APPROVED_ROUTES_ONLY",
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
            "acquisition_only": True,
        },
        "recommendation": (
            "Proceed to v2.9D OTC Markets Validation. Do not rebuild until v2.9D confirms schema, duplicate control and net-new coverage."
            if not blockers
            else "Review acquisition blockers before validation or rebuild."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.9C OTC Markets Acquisition Real")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Acquisition status: **{acquisition_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Acquisition decision: **{acquisition_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Provider")
    md.append("")
    md.append(f"- Provider ID: `{PROVIDER_ID}`")
    md.append(f"- Provider dir: `{rel(PROVIDER_DIR)}`")
    md.append(f"- Raw page HTML: `{rel(RAW_PAGE_HTML)}`")
    md.append(f"- Raw CSV: `{rel(RAW_CSV)}`")
    md.append("")
    md.append("## Request results")
    md.append("")
    for item in request_results:
        md.append(f"### {item.get('route_id')}")
        md.append("")
        md.append(f"- URL: `{item.get('url')}`")
        md.append(f"- Target: `{item.get('target_path')}`")
        md.append(f"- OK: {item.get('ok')}")
        md.append(f"- Status code: {item.get('status_code')}")
        md.append(f"- Content type: `{item.get('content_type')}`")
        md.append(f"- Size bytes: {item.get('size_bytes')}")
        md.append(f"- SHA256: `{item.get('sha256')}`")
        md.append(f"- Error: `{item.get('error')}`")
        md.append("")
    md.append("## CSV probe")
    md.append("")
    md.append(f"- Exists: {csv_probe.get('exists')}")
    md.append(f"- Is probable CSV: {csv_probe.get('is_probable_csv')}")
    md.append(f"- Row count: {csv_probe.get('row_count')}")
    md.append(f"- Field count: {csv_probe.get('field_count')}")
    md.append(f"- Fields: {', '.join(csv_probe.get('fields') or [])}")
    md.append(f"- Schema probe CSV: `{rel(SCHEMA_PROBE_CSV)}`")
    md.append(f"- Sample CSV: `{rel(SAMPLE_CSV)}`")
    md.append(f"- Sample rows written: {csv_probe.get('sample_rows_written')}")
    md.append(f"- Error: `{csv_probe.get('error')}`")
    md.append("")
    md.append("## Current threshold context")
    md.append("")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}")
    md.append(f"- Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}")
    md.append("- Net-new coverage: not computed in v2.9C")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- Network download performed: true")
    md.append("- Network download scope: OTC_MARKETS_APPROVED_ROUTES_ONLY")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("- Acquisition only: true")
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
    md.append("Important: v2.9C is acquisition-only. It downloads only the OTC Markets routes approved by v2.9B. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.9C OTC Markets Acquisition Real")
    print("=" * 92)
    print(f"OK   Acquisition status: {acquisition_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Acquisition decision: {acquisition_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Provider: {PROVIDER_ID}")
    print(f"OK   CSV rows: {csv_probe.get('row_count')}")
    print(f"OK   CSV fields: {csv_probe.get('field_count')}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Raw page written: {RAW_PAGE_HTML}")
    print(f"OK   Raw CSV written: {RAW_CSV}")
    print(f"OK   Schema probe written: {SCHEMA_PROBE_CSV}")
    print(f"OK   Sample written: {SAMPLE_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: True")
    print("OK   Network download scope: OTC_MARKETS_APPROVED_ROUTES_ONLY")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
