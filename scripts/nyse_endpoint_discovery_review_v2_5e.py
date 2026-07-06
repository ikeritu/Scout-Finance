from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.5E"
METHOD = "nyse_endpoint_discovery_review_v1"

PROVIDER_ID = "nyse_listed_directory"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID
RAW_HTML = PROVIDER_DIR / "nyse_listings_directory_stock.html"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "nyse_endpoint_discovery_review_v2_5e.json"
OUT_MD = OUT_DIR / "nyse_endpoint_discovery_review_v2_5e.md"
OUT_CANDIDATES_CSV = OUT_DIR / "nyse_endpoint_discovery_candidates_v2_5e.csv"

ACQUISITION_JSON = OUT_DIR / "controlled_nyse_provider_acquisition_real_v2_5d.json"

NYSE_BASE_URL = "https://www.nyse.com"
NYSE_LISTINGS_URL = "https://www.nyse.com/listings_directory/stock"

API_HINT_PATTERNS = [
    r"https?://[^\"'\s<>]+",
    r"/api/[^\"'\s<>]+",
    r"/api[^\"'\s<>]+",
    r"/data/[^\"'\s<>]+",
    r"/public/[^\"'\s<>]+",
    r"/listings[^\"'\s<>]+",
    r"/listings_directory[^\"'\s<>]+",
    r"/quote[^\"'\s<>]+",
    r"/_next/static/[^\"'\s<>]+",
    r"/static/[^\"'\s<>]+",
]

INTERESTING_KEYWORDS = [
    "listings",
    "directory",
    "instrument",
    "symbol",
    "ticker",
    "quote",
    "equity",
    "stock",
    "nyse",
    "api",
    "graphql",
    "apollo",
    "next_data",
    "__next_data__",
    "application/json",
    "csv",
    "download",
    "mft",
]

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
CURRENT_INCLUDED_ROWS_EXPECTED = 5648


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_candidate(candidate: str) -> str:
    candidate = candidate.strip().strip("\\").strip()
    candidate = candidate.replace("\\u002F", "/")
    candidate = candidate.replace("\\/", "/")
    candidate = candidate.replace("&amp;", "&")

    if candidate.startswith("//"):
        return "https:" + candidate

    if candidate.startswith("/"):
        return urljoin(NYSE_BASE_URL, candidate)

    return candidate


def candidate_type(url: str) -> str:
    lower = url.lower()

    if "/api" in lower:
        return "api_candidate"
    if "graphql" in lower:
        return "graphql_candidate"
    if lower.endswith(".csv") or "csv" in lower:
        return "csv_candidate"
    if "/_next/static/" in lower or lower.endswith(".js"):
        return "javascript_asset"
    if lower.endswith(".json") or "json" in lower:
        return "json_candidate"
    if "listing" in lower or "directory" in lower:
        return "listing_related"
    return "other"


def score_candidate(url: str) -> int:
    lower = url.lower()
    score = 0

    for keyword in INTERESTING_KEYWORDS:
        if keyword in lower:
            score += 5

    if "/api" in lower:
        score += 20
    if "graphql" in lower:
        score += 20
    if "listing" in lower or "directory" in lower:
        score += 15
    if "symbol" in lower or "ticker" in lower:
        score += 10
    if lower.endswith(".csv"):
        score += 30
    if lower.endswith(".json"):
        score += 15
    if lower.endswith(".js"):
        score += 5

    return score


def extract_candidates(html: str) -> list[dict[str, object]]:
    raw_candidates: list[str] = []

    for pattern in API_HINT_PATTERNS:
        raw_candidates.extend(re.findall(pattern, html, flags=re.IGNORECASE))

    # Also catch quoted relative assets and endpoints that may not start at word boundary.
    raw_candidates.extend(
        re.findall(
            r'["\'](?P<path>/(?:api|_next|static|listings|listings_directory|data|public|quote)[^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )
    )

    cleaned: dict[str, dict[str, object]] = {}

    for raw in raw_candidates:
        url = normalize_candidate(raw)

        # Remove obvious noise from malformed captures.
        url = url.split("\\n")[0].split("\\t")[0].strip()
        url = url.rstrip(".,);]}")
        url = url.strip('"').strip("'")

        if not url:
            continue

        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc and "nyse.com" not in parsed.netloc.lower():
            # Keep external script/CDN only if it looks very relevant.
            if not any(k in url.lower() for k in ["nyse", "listing", "ticker", "symbol", "api"]):
                continue

        ctype = candidate_type(url)
        score = score_candidate(url)

        if score <= 0 and ctype == "other":
            continue

        cleaned[url] = {
            "candidate": url,
            "candidate_type": ctype,
            "score": score,
            "host": parsed.netloc or "nyse.com",
            "path": parsed.path or url,
        }

    return sorted(cleaned.values(), key=lambda item: (-int(item["score"]), str(item["candidate"])))


def count_keywords(html: str) -> dict[str, int]:
    lower = html.lower()
    return {keyword: lower.count(keyword.lower()) for keyword in INTERESTING_KEYWORDS}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    import csv

    fieldnames = ["candidate", "candidate_type", "score", "host", "path"]
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    acquisition = read_json(ACQUISITION_JSON)

    if not acquisition.get("_exists"):
        blockers.append(f"Missing v2.5D acquisition artifact: {rel(ACQUISITION_JSON)}")
    else:
        positives.append(f"v2.5D acquisition artifact found: {rel(ACQUISITION_JSON)}")

    acquisition_status = acquisition.get("acquisition_status")
    if acquisition_status == "NYSE_PROVIDER_ACQUISITION_RAW_ONLY_REVIEW_REQUIRED":
        positives.append(f"v2.5D acquisition status accepted: {acquisition_status}")
    else:
        warnings.append(f"Unexpected or different v2.5D acquisition status: {acquisition_status}")

    if not RAW_HTML.exists():
        blockers.append(f"Missing raw NYSE HTML: {rel(RAW_HTML)}")
        html = ""
    else:
        html = read_text(RAW_HTML)
        positives.append(f"Raw NYSE HTML found: {rel(RAW_HTML)}")

    html_size = len(html.encode("utf-8")) if html else 0
    candidates = extract_candidates(html) if html else []
    keyword_counts = count_keywords(html) if html else {}

    type_counts = Counter(str(item["candidate_type"]) for item in candidates)

    api_candidates = [item for item in candidates if item["candidate_type"] == "api_candidate"]
    graphql_candidates = [item for item in candidates if item["candidate_type"] == "graphql_candidate"]
    csv_candidates = [item for item in candidates if item["candidate_type"] == "csv_candidate"]
    json_candidates = [item for item in candidates if item["candidate_type"] == "json_candidate"]
    listing_related = [item for item in candidates if item["candidate_type"] == "listing_related"]
    js_assets = [item for item in candidates if item["candidate_type"] == "javascript_asset"]

    write_csv(OUT_CANDIDATES_CSV, candidates)

    if candidates:
        positives.append(f"Endpoint/asset candidates detected: {len(candidates)}")
    else:
        warnings.append("No endpoint/asset candidates detected in raw NYSE HTML.")

    if csv_candidates:
        positives.append(f"CSV candidates detected: {len(csv_candidates)}")
    else:
        warnings.append("No direct CSV candidate detected.")

    if api_candidates or graphql_candidates or json_candidates:
        positives.append(
            f"Potential API/JSON candidates detected: api={len(api_candidates)}, graphql={len(graphql_candidates)}, json={len(json_candidates)}"
        )
    else:
        warnings.append("No direct API/GraphQL/JSON candidate detected in raw HTML.")

    if js_assets:
        positives.append(f"JavaScript assets detected for possible follow-up inspection: {len(js_assets)}")
    else:
        warnings.append("No JavaScript assets detected for follow-up inspection.")

    if blockers:
        discovery_status = "NYSE_ENDPOINT_DISCOVERY_BLOCKED"
        readiness_score = 0
        usability_decision = "BLOCKED"
    elif csv_candidates:
        discovery_status = "NYSE_ENDPOINT_DISCOVERY_CSV_CANDIDATE_FOUND"
        readiness_score = 85
        usability_decision = "POTENTIALLY_USABLE_AFTER_ENDPOINT_VALIDATION"
    elif api_candidates or graphql_candidates or json_candidates:
        discovery_status = "NYSE_ENDPOINT_DISCOVERY_API_CANDIDATE_FOUND"
        readiness_score = 75
        usability_decision = "POTENTIALLY_USABLE_AFTER_ENDPOINT_VALIDATION"
    elif js_assets:
        discovery_status = "NYSE_ENDPOINT_DISCOVERY_JS_REVIEW_REQUIRED"
        readiness_score = 65
        usability_decision = "REQUIRES_SCRIPT_ASSET_REVIEW"
    else:
        discovery_status = "NYSE_ENDPOINT_DISCOVERY_NO_STABLE_ENDPOINT_FOUND"
        readiness_score = 50
        usability_decision = "RAW_ONLY_NOT_USABLE_YET"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "discovery_status": discovery_status,
        "readiness_score": readiness_score,
        "usability_decision": usability_decision,
        "inputs": {
            "v2_5d_acquisition_json": {
                "path": rel(ACQUISITION_JSON),
                "exists": acquisition.get("_exists"),
                "acquisition_status": acquisition_status,
            },
            "raw_html": {
                "path": rel(RAW_HTML),
                "exists": RAW_HTML.exists(),
                "size_bytes_utf8": html_size,
            },
        },
        "summary": {
            "candidate_count": len(candidates),
            "candidate_type_counts": dict(type_counts),
            "api_candidates": len(api_candidates),
            "graphql_candidates": len(graphql_candidates),
            "csv_candidates": len(csv_candidates),
            "json_candidates": len(json_candidates),
            "listing_related_candidates": len(listing_related),
            "javascript_assets": len(js_assets),
            "keyword_counts": keyword_counts,
            "current_included_rows_before_nyse": CURRENT_INCLUDED_ROWS_EXPECTED,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
        },
        "top_candidates": candidates[:30],
        "outputs": {
            "candidates_csv": rel(OUT_CANDIDATES_CSV),
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
            "network_download_performed": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
        },
        "recommendation": (
            "Proceed to v2.5F to inspect candidate endpoints/assets before deciding whether NYSE is usable."
            if usability_decision in {"POTENTIALLY_USABLE_AFTER_ENDPOINT_VALIDATION", "REQUIRES_SCRIPT_ASSET_REVIEW"}
            else "Close NYSE as raw-only unless a stable public endpoint is identified manually."
            if usability_decision == "RAW_ONLY_NOT_USABLE_YET"
            else "Resolve blockers before continuing NYSE endpoint review."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.5E NYSE Endpoint Discovery Review")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Discovery status: **{discovery_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Usability decision: **{usability_decision}**")
    md.append(f"- Raw HTML: `{rel(RAW_HTML)}`")
    md.append(f"- Candidate count: {len(candidates)}")
    md.append(f"- API candidates: {len(api_candidates)}")
    md.append(f"- GraphQL candidates: {len(graphql_candidates)}")
    md.append(f"- CSV candidates: {len(csv_candidates)}")
    md.append(f"- JSON candidates: {len(json_candidates)}")
    md.append(f"- JavaScript assets: {len(js_assets)}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Network download performed: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("")
    md.append("## Candidate type counts")
    md.append("")
    if type_counts:
        for ctype, count in type_counts.most_common():
            md.append(f"- {ctype}: {count}")
    else:
        md.append("- No candidates detected.")
    md.append("")
    md.append("## Top candidates")
    md.append("")
    if candidates:
        for item in candidates[:30]:
            md.append(f"- score {item['score']} ? {item['candidate_type']} ? `{item['candidate']}`")
    else:
        md.append("- No candidates detected.")
    md.append("")
    md.append("## Keyword counts")
    md.append("")
    for keyword, count in sorted(keyword_counts.items(), key=lambda item: (-item[1], item[0])):
        md.append(f"- {keyword}: {count}")
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
    md.append("Important: v2.5E is an endpoint discovery review only. It does not download new data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.5E NYSE Endpoint Discovery Review")
    print("=" * 92)
    print(f"OK   Discovery status: {discovery_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Usability decision: {usability_decision}")
    print(f"OK   Candidate count: {len(candidates)}")
    print(f"OK   API candidates: {len(api_candidates)}")
    print(f"OK   GraphQL candidates: {len(graphql_candidates)}")
    print(f"OK   CSV candidates: {len(csv_candidates)}")
    print(f"OK   JSON candidates: {len(json_candidates)}")
    print(f"OK   JavaScript assets: {len(js_assets)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Candidates CSV written: {OUT_CANDIDATES_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
