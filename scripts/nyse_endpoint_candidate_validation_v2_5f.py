from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.5F"
METHOD = "nyse_endpoint_candidate_validation_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "nyse_endpoint_candidate_validation_v2_5f.json"
OUT_MD = OUT_DIR / "nyse_endpoint_candidate_validation_v2_5f.md"
OUT_ENDPOINT_RESPONSE = OUT_DIR / "nyse_endpoint_candidate_validation_proxy_response_v2_5f.txt"
OUT_JS_FINDINGS_CSV = OUT_DIR / "nyse_endpoint_candidate_validation_js_findings_v2_5f.csv"

RAW_JS_DIR = ROOT / "data" / "raw" / "source_providers" / "nyse_listed_directory" / "endpoint_validation_js"

DISCOVERY_JSON = OUT_DIR / "nyse_endpoint_discovery_review_v2_5e.json"
CANDIDATES_CSV = OUT_DIR / "nyse_endpoint_discovery_candidates_v2_5e.csv"

NYSE_PROXY_URL = "https://www.nyse.com/api/sites/nyse/proxy"
NYSE_LISTINGS_URL = "https://www.nyse.com/listings_directory/stock"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)

TIMEOUT_SECONDS = 30
MAX_JS_ASSETS_TO_FETCH = 8

INTERESTING_PATTERNS = [
    "api/sites/nyse/proxy",
    "/api/sites/nyse/proxy",
    "listings_directory",
    "listings-directory",
    "listingsDirectory",
    "ListingsDirectory",
    "instrument",
    "instruments",
    "symbol",
    "ticker",
    "exchange",
    "quote",
    "equity",
    "stock",
    "payload",
    "query",
    "url:",
    "method:",
    "POST",
    "GET",
    "proxy",
    "nyse",
]

CURRENT_INCLUDED_ROWS_EXPECTED = 5648
TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_filename_from_url(url: str, index: int) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name or f"asset_{index}.js"
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    if not name.endswith(".js"):
        name += ".js"
    return f"{index:02d}_{name}"


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def read_candidates(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fetch_url(url: str, *, method: str = "GET", body: bytes | None = None, headers_extra: dict[str, str] | None = None) -> dict[str, object]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/plain,*/*",
        "Referer": NYSE_LISTINGS_URL,
        "Origin": "https://www.nyse.com",
    }

    if headers_extra:
        headers.update(headers_extra)

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            response_headers = dict(response.headers.items())
            content_type = response_headers.get("Content-Type", "")

            return {
                "ok": True,
                "status_code": getattr(response, "status", None),
                "reason": getattr(response, "reason", None),
                "headers": response_headers,
                "content_type": content_type,
                "raw": raw,
                "text": raw.decode("utf-8", errors="replace"),
                "sha256": sha256_bytes(raw),
                "size_bytes": len(raw),
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
            "sha256": sha256_bytes(raw) if raw else None,
            "size_bytes": len(raw),
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
            "sha256": None,
            "size_bytes": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }


def extract_context(text: str, pattern: str, window: int = 180) -> list[str]:
    contexts: list[str] = []
    lower = text.lower()
    needle = pattern.lower()

    start = 0
    while True:
        index = lower.find(needle, start)
        if index < 0:
            break

        left = max(index - window, 0)
        right = min(index + len(pattern) + window, len(text))
        snippet = " ".join(text[left:right].split())
        contexts.append(snippet[:500])
        start = index + len(pattern)

        if len(contexts) >= 10:
            break

    return contexts


def classify_endpoint_response(response: dict[str, object]) -> tuple[str, list[str]]:
    warnings: list[str] = []

    ok = bool(response.get("ok"))
    status_code = response.get("status_code")
    text = str(response.get("text") or "")
    content_type = str(response.get("content_type") or "")
    size_bytes = int(response.get("size_bytes") or 0)

    if not ok:
        return "ENDPOINT_HTTP_FAILED", [f"Endpoint request failed: {response.get('error')}"]

    if status_code in {401, 403}:
        return "ENDPOINT_REQUIRES_AUTH_OR_FORBIDDEN", [f"Endpoint returned restricted status: {status_code}"]

    if size_bytes == 0:
        return "ENDPOINT_EMPTY_RESPONSE", ["Endpoint returned empty response."]

    if "application/json" in content_type.lower():
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list) and parsed:
                return "ENDPOINT_RETURNS_JSON_LIST_REQUIRES_SCHEMA_REVIEW", warnings
            if isinstance(parsed, dict) and parsed:
                return "ENDPOINT_RETURNS_JSON_OBJECT_REQUIRES_SCHEMA_REVIEW", warnings
            return "ENDPOINT_RETURNS_EMPTY_JSON", ["Endpoint returned JSON but empty payload."]
        except Exception:
            return "ENDPOINT_JSON_CONTENT_TYPE_PARSE_FAILED", ["Endpoint content-type is JSON but parsing failed."]

    lower = text.lower()
    if "<html" in lower or "<!doctype html" in lower:
        return "ENDPOINT_RETURNS_HTML_NOT_DIRECT_DATA", ["Endpoint returned HTML, not direct listing data."]

    if "symbol" in lower or "ticker" in lower or "instrument" in lower:
        return "ENDPOINT_RETURNS_TEXT_WITH_MARKET_HINTS", warnings

    return "ENDPOINT_RESPONSE_NOT_DIRECTLY_USABLE", ["Endpoint responded but no obvious listing data markers were found."]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_JS_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    discovery = read_json(DISCOVERY_JSON)
    candidates = read_candidates(CANDIDATES_CSV)

    if not discovery.get("_exists"):
        blockers.append(f"Missing v2.5E discovery artifact: {rel(DISCOVERY_JSON)}")
    else:
        positives.append(f"v2.5E discovery artifact found: {rel(DISCOVERY_JSON)}")

    discovery_status = discovery.get("discovery_status")
    if discovery_status == "NYSE_ENDPOINT_DISCOVERY_API_CANDIDATE_FOUND":
        positives.append(f"v2.5E discovery status accepted: {discovery_status}")
    else:
        warnings.append(f"Unexpected or different v2.5E discovery status: {discovery_status}")

    if not candidates:
        blockers.append(f"No candidates found in {rel(CANDIDATES_CSV)}")
    else:
        positives.append(f"Candidate CSV loaded: {len(candidates)} candidates")

    api_candidates = [row for row in candidates if row.get("candidate_type") == "api_candidate"]
    js_candidates = [row for row in candidates if row.get("candidate_type") == "javascript_asset"]

    if not api_candidates:
        blockers.append("No API candidate available to validate.")
    else:
        positives.append(f"API candidates available: {len(api_candidates)}")

    if not js_candidates:
        warnings.append("No JavaScript candidates available for inspection.")
    else:
        positives.append(f"JavaScript candidates available: {len(js_candidates)}")

    proxy_response = fetch_url(NYSE_PROXY_URL)
    endpoint_status, endpoint_warnings = classify_endpoint_response(proxy_response)
    warnings.extend(endpoint_warnings)

    OUT_ENDPOINT_RESPONSE.write_text(str(proxy_response.get("text") or ""), encoding="utf-8", errors="replace")

    if proxy_response.get("ok"):
        positives.append(f"Endpoint candidate responded: {NYSE_PROXY_URL}")
    else:
        warnings.append(f"Endpoint candidate did not return OK: {proxy_response.get('error')}")

    js_findings: list[dict[str, object]] = []
    downloaded_js_assets: list[dict[str, object]] = []

    for index, row in enumerate(js_candidates[:MAX_JS_ASSETS_TO_FETCH], start=1):
        url = row.get("candidate") or ""
        if not url:
            continue

        response = fetch_url(url)
        asset_path = RAW_JS_DIR / safe_filename_from_url(url, index)

        if response.get("raw"):
            asset_path.write_bytes(response["raw"])  # type: ignore[index]

        text = str(response.get("text") or "")
        matched_patterns = []

        for pattern in INTERESTING_PATTERNS:
            contexts = extract_context(text, pattern)
            if contexts:
                matched_patterns.append(pattern)
                for snippet_index, snippet in enumerate(contexts[:3], start=1):
                    js_findings.append(
                        {
                            "asset_url": url,
                            "asset_path": rel(asset_path) if asset_path.exists() else "",
                            "pattern": pattern,
                            "snippet_index": snippet_index,
                            "snippet": snippet,
                        }
                    )

        downloaded_js_assets.append(
            {
                "url": url,
                "ok": bool(response.get("ok")),
                "status_code": response.get("status_code"),
                "content_type": response.get("content_type"),
                "size_bytes": response.get("size_bytes"),
                "sha256": response.get("sha256"),
                "local_path": rel(asset_path) if asset_path.exists() else None,
                "matched_patterns": matched_patterns,
                "matched_pattern_count": len(matched_patterns),
                "error": response.get("error"),
            }
        )

    write_csv(
        OUT_JS_FINDINGS_CSV,
        js_findings,
        ["asset_url", "asset_path", "pattern", "snippet_index", "snippet"],
    )

    if js_findings:
        positives.append(f"JS findings detected: {len(js_findings)}")
    else:
        warnings.append("No useful JS findings detected from inspected assets.")

    endpoint_size = int(proxy_response.get("size_bytes") or 0)
    endpoint_content_type = str(proxy_response.get("content_type") or "")
    endpoint_status_code = proxy_response.get("status_code")

    if blockers:
        validation_status = "NYSE_ENDPOINT_VALIDATION_BLOCKED"
        readiness_score = 0
        usability_decision = "BLOCKED"
    elif endpoint_status in {
        "ENDPOINT_RETURNS_JSON_LIST_REQUIRES_SCHEMA_REVIEW",
        "ENDPOINT_RETURNS_JSON_OBJECT_REQUIRES_SCHEMA_REVIEW",
        "ENDPOINT_RETURNS_TEXT_WITH_MARKET_HINTS",
    }:
        validation_status = "NYSE_ENDPOINT_CANDIDATE_VALIDATION_REQUIRES_SCHEMA_REVIEW"
        readiness_score = 80
        usability_decision = "POTENTIALLY_USABLE_REQUIRES_SCHEMA_REVIEW"
    elif js_findings:
        validation_status = "NYSE_ENDPOINT_CANDIDATE_VALIDATION_JS_HINTS_FOUND"
        readiness_score = 70
        usability_decision = "REQUIRES_DEEP_JS_PAYLOAD_REVIEW"
    elif endpoint_status == "ENDPOINT_RETURNS_HTML_NOT_DIRECT_DATA":
        validation_status = "NYSE_ENDPOINT_CANDIDATE_VALIDATION_NOT_DIRECT_DATA"
        readiness_score = 55
        usability_decision = "RAW_ONLY_OR_PROXY_PAYLOAD_REQUIRED"
    else:
        validation_status = "NYSE_ENDPOINT_CANDIDATE_VALIDATION_NO_USABLE_ROUTE_FOUND"
        readiness_score = 50
        usability_decision = "RAW_ONLY_NOT_USABLE_YET"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "usability_decision": usability_decision,
        "inputs": {
            "discovery_json": {
                "path": rel(DISCOVERY_JSON),
                "exists": discovery.get("_exists"),
                "discovery_status": discovery_status,
            },
            "candidates_csv": {
                "path": rel(CANDIDATES_CSV),
                "candidate_count": len(candidates),
                "api_candidate_count": len(api_candidates),
                "javascript_candidate_count": len(js_candidates),
            },
        },
        "endpoint_validation": {
            "url": NYSE_PROXY_URL,
            "status": endpoint_status,
            "http_ok": bool(proxy_response.get("ok")),
            "status_code": endpoint_status_code,
            "content_type": endpoint_content_type,
            "size_bytes": endpoint_size,
            "sha256": proxy_response.get("sha256"),
            "response_sample_path": rel(OUT_ENDPOINT_RESPONSE),
            "error": proxy_response.get("error"),
        },
        "javascript_asset_validation": {
            "max_assets_to_fetch": MAX_JS_ASSETS_TO_FETCH,
            "downloaded_assets": downloaded_js_assets,
            "finding_count": len(js_findings),
            "findings_csv": rel(OUT_JS_FINDINGS_CSV),
            "raw_js_dir": rel(RAW_JS_DIR),
        },
        "targets": {
            "current_included_rows_before_nyse": CURRENT_INCLUDED_ROWS_EXPECTED,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
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
            "network_download_performed": True,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
        },
        "recommendation": (
            "Proceed to v2.5G to decide whether NYSE remains raw-only, requires deeper JS payload review, or can become a provider after schema review."
            if not blockers
            else "Resolve blockers before NYSE usability decision."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.5F NYSE Endpoint Candidate Validation")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Usability decision: **{usability_decision}**")
    md.append(f"- Endpoint candidate: `{NYSE_PROXY_URL}`")
    md.append(f"- Endpoint status: **{endpoint_status}**")
    md.append(f"- Endpoint HTTP OK: {bool(proxy_response.get('ok'))}")
    md.append(f"- Endpoint status code: {endpoint_status_code}")
    md.append(f"- Endpoint content type: `{endpoint_content_type}`")
    md.append(f"- Endpoint response size bytes: {endpoint_size}")
    md.append(f"- JS candidates available: {len(js_candidates)}")
    md.append(f"- JS assets inspected: {len(downloaded_js_assets)}")
    md.append(f"- JS findings: {len(js_findings)}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Network download performed: true")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("")
    md.append("## Endpoint validation")
    md.append("")
    md.append(f"- URL: `{NYSE_PROXY_URL}`")
    md.append(f"- Status: **{endpoint_status}**")
    md.append(f"- Response sample: `{rel(OUT_ENDPOINT_RESPONSE)}`")
    md.append("")
    md.append("## JavaScript assets inspected")
    md.append("")
    if downloaded_js_assets:
        for asset in downloaded_js_assets:
            md.append(f"- `{asset['local_path']}` ? ok: {asset['ok']} ? status: {asset['status_code']} ? matches: {asset['matched_pattern_count']}")
    else:
        md.append("- No JS assets inspected.")
    md.append("")
    md.append("## JS findings")
    md.append("")
    if js_findings:
        for item in js_findings[:30]:
            md.append(f"- `{item['pattern']}` in `{item['asset_path']}` ? {item['snippet']}")
    else:
        md.append("- No JS findings detected.")
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
    md.append("Important: v2.5F validates endpoint and JS candidates only. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.5F NYSE Endpoint Candidate Validation")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Usability decision: {usability_decision}")
    print(f"OK   Endpoint status: {endpoint_status}")
    print(f"OK   Endpoint HTTP OK: {bool(proxy_response.get('ok'))}")
    print(f"OK   Endpoint status code: {endpoint_status_code}")
    print(f"OK   Endpoint response size bytes: {endpoint_size}")
    print(f"OK   JS candidates available: {len(js_candidates)}")
    print(f"OK   JS assets inspected: {len(downloaded_js_assets)}")
    print(f"OK   JS findings: {len(js_findings)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   JS findings CSV written: {OUT_JS_FINDINGS_CSV}")
    print(f"OK   Endpoint response written: {OUT_ENDPOINT_RESPONSE}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
