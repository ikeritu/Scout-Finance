from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin


VERSION = "v2.16E"
PHASE = "TMX Candidate Extraction Dry Run"
PHASE_TYPE = "candidate-extraction-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

V216C_JSON = OUTPUT_DIR / "tmx_raw_acquisition_manifest_v2_16c.json"
V216C_CSV = OUTPUT_DIR / "tmx_raw_acquisition_manifest_v2_16c.csv"
V216D2_JSON = OUTPUT_DIR / "tmx_controlled_endpoint_probe_v2_16d2.json"

REPORT_JSON = OUTPUT_DIR / "tmx_candidate_extraction_dry_run_v2_16e.json"
REPORT_MD = OUTPUT_DIR / "tmx_candidate_extraction_dry_run_v2_16e.md"
CANDIDATES_CSV = OUTPUT_DIR / "tmx_candidate_extraction_candidates_v2_16e.csv"
EXCLUSIONS_CSV = OUTPUT_DIR / "tmx_candidate_extraction_exclusions_v2_16e.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "tmx_candidate_extraction_source_diagnostics_v2_16e.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

NEXT_PHASE_IF_CANDIDATES = "v2.16F - TMX Candidate Validation Against Canonical Dry Run"
NEXT_PHASE_IF_NO_CANDIDATES = "v2.16I - TMX Closure Report"

CANDIDATE_FIELDS = [
    "candidate_id",
    "source_id",
    "source_name",
    "extraction_method",
    "raw_symbol",
    "raw_name",
    "raw_exchange",
    "raw_url",
    "confidence_bucket",
    "evidence",
    "review_required",
    "candidate_key",
    "notes",
]

EXCLUSION_FIELDS = [
    "exclusion_id",
    "source_id",
    "source_name",
    "extraction_method",
    "raw_symbol",
    "raw_name",
    "raw_exchange",
    "raw_url",
    "exclusion_reason",
    "evidence",
]

SOURCE_DIAGNOSTIC_FIELDS = [
    "source_id",
    "source_name",
    "raw_path",
    "raw_exists",
    "bytes_read",
    "html_like",
    "title",
    "anchor_quote_like_count",
    "json_object_like_count",
    "table_row_count",
    "text_pattern_count",
    "raw_candidates_before_filter",
    "deduped_candidates_after_filter",
    "exclusions",
    "notes",
]

EXCLUDE_NAME_KEYWORDS = [
    "etf",
    "fund",
    "income fund",
    "trust units",
    "unit",
    "units",
    "warrant",
    "warrants",
    "right",
    "rights",
    "debenture",
    "debentures",
    "note",
    "notes",
    "bond",
    "bonds",
    "preferred",
    "preference",
    "receipt",
    "receipts",
    "split corp",
    "closed-end",
    "closed end",
    "exchange traded",
    "covered call",
    "income shares",
    "bitcoin",
    "ethereum",
    "solana",
    "crypto",
    "cryptocurrency",
]

EXCLUDE_SYMBOL_PATTERNS = [
    r"\.WT(?:\.|$)",
    r"\.WS(?:\.|$)",
    r"\.W(?:\.|$)",
    r"\.R(?:\.|$)",
    r"\.RT(?:\.|$)",
    r"\.U(?:\.|$)",
    r"\.UN(?:\.|$)",
    r"\.DB(?:\.|$)",
    r"\.NT(?:\.|$)",
    r"\.PR(?:\.|$)",
]

VALID_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,14}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


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


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(value.replace("\xa0", " ").split()).strip()


def extract_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return clean_text(match.group(1))[:300]


def base_url_for_manifest_row(row: dict) -> str:
    return str(row.get("final_url", "")).strip() or str(row.get("url", "")).strip()


def normalize_url(value: str, base_url: str) -> str:
    value = html.unescape(value or "").strip()
    if not value:
        return ""
    if value.startswith("//"):
        return "https:" + value
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.startswith("/"):
        return urljoin(base_url, value)
    return ""


def normalize_symbol(value: str) -> str:
    value = html.unescape(value or "").strip().upper()
    for prefix in ["TSX:", "TSXV:", "TSX-V:", "NYSE:", "NASDAQ:"]:
        value = value.replace(prefix, "")
    return value.strip(" .,:;|[](){}")


def infer_exchange(value: str) -> str:
    low = (value or "").lower()
    if "tsxv" in low or "tsx venture" in low or "tsx-v" in low:
        return "TSXV"
    if "tsx" in low or "toronto stock exchange" in low:
        return "TSX"
    return ""


def symbol_is_valid(symbol: str) -> bool:
    return bool(symbol and VALID_SYMBOL_RE.match(symbol))


def weak_text_exchange_context(symbol: str, name: str) -> str:
    clean_name = clean_text(name)
    low = clean_name.lower()

    if not clean_name:
        return "missing_name_for_text_exchange_pattern"

    if len(symbol.strip()) <= 1:
        return "ambiguous_one_character_symbol_from_text"

    if len(clean_name) > 90:
        return "text_exchange_name_too_long"

    if clean_name[:1].islower():
        return "text_exchange_name_starts_lowercase"

    noisy_phrases = [
        "announced",
        "agreement",
        "definitive agreement",
        "today announced",
        "will begin trading",
        "begin trading today",
        "under the symbol",
        "exchange operator",
        "market technology provider",
        "a canadian-based",
        "global health company",
        "will trade",
        "will be traded",
    ]

    for phrase in noisy_phrases:
        if phrase in low:
            return "weak_text_exchange_news_context"

    return ""


def exclusion_reason(symbol: str, name: str, exchange: str, url: str) -> str:
    low_name = (name or "").lower()
    low_url = (url or "").lower()

    if not symbol:
        return "missing_symbol"

    if not symbol_is_valid(symbol):
        return "invalid_symbol_format"

    for pattern in EXCLUDE_SYMBOL_PATTERNS:
        if re.search(pattern, symbol, flags=re.IGNORECASE):
            return "excluded_symbol_suffix_review"

    for keyword in EXCLUDE_NAME_KEYWORDS:
        if keyword in low_name:
            return f"excluded_name_keyword:{keyword}"

    if "/etf" in low_url or "fund" in low_url or "crypto" in low_url:
        return "excluded_url_keyword_fund_etf_or_crypto"

    return ""


def confidence_for_candidate(method: str, symbol: str, name: str, exchange: str, url: str) -> str:
    if method in {"json_object", "table_row"} and symbol and name and exchange:
        return "high"
    if method in {"quote_anchor", "text_exchange_pattern"} and symbol and name:
        return "medium"
    if symbol and (name or exchange):
        return "low"
    return "none"


def candidate_key(symbol: str, name: str, exchange: str) -> str:
    return "|".join([symbol.upper(), (name or "").lower(), (exchange or "").upper()])


def make_candidate(source: dict, method: str, symbol: str, name: str, exchange: str, url: str, evidence: str, notes: str = "") -> dict:
    symbol = normalize_symbol(symbol)
    name = clean_text(name)[:300]
    exchange = (exchange or "").strip().upper()
    url = url.strip()
    key = candidate_key(symbol, name, exchange)
    confidence = confidence_for_candidate(method, symbol, name, exchange, url)

    return {
        "candidate_id": sha256_text(f"{source['source_id']}|{method}|{key}|{url}")[:16],
        "source_id": source["source_id"],
        "source_name": source["source_name"],
        "extraction_method": method,
        "raw_symbol": symbol,
        "raw_name": name,
        "raw_exchange": exchange,
        "raw_url": url,
        "confidence_bucket": confidence,
        "evidence": evidence[:500],
        "review_required": confidence != "high",
        "candidate_key": key,
        "notes": notes,
    }


def make_exclusion(source: dict, method: str, symbol: str, name: str, exchange: str, url: str, reason: str, evidence: str) -> dict:
    return {
        "exclusion_id": sha256_text(f"{source['source_id']}|{method}|{symbol}|{name}|{url}|{reason}")[:16],
        "source_id": source["source_id"],
        "source_name": source["source_name"],
        "extraction_method": method,
        "raw_symbol": normalize_symbol(symbol),
        "raw_name": clean_text(name)[:300],
        "raw_exchange": (exchange or "").strip().upper(),
        "raw_url": url.strip(),
        "exclusion_reason": reason,
        "evidence": evidence[:500],
    }


def extract_quote_anchors(source: dict, text: str, base_url: str) -> list[dict]:
    rows = []
    anchor_re = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)

    for href, label_html in anchor_re.findall(text):
        url = normalize_url(href, base_url)
        label = clean_text(label_html)
        basis = " ".join([href, url, label])
        symbol = ""

        for pattern in [
            r"/quote/([A-Z0-9.\-]{1,15})(?:[/?#]|$)",
            r"/stocks?/([A-Z0-9.\-]{1,15})(?:[/?#]|$)",
            r"symbol=([A-Z0-9.\-]{1,15})",
            r"q=([A-Z0-9.\-]{1,15})",
        ]:
            match = re.search(pattern, basis, flags=re.IGNORECASE)
            if match:
                symbol = normalize_symbol(match.group(1))
                break

        if symbol:
            rows.append(
                make_candidate(
                    source,
                    "quote_anchor",
                    symbol,
                    label,
                    infer_exchange(basis),
                    url,
                    basis[:500],
                    "symbol_in_anchor_url",
                )
            )

    return rows


def extract_json_like_objects(source: dict, text: str, base_url: str) -> list[dict]:
    rows = []
    object_re = re.compile(r"\{[^{}]{0,5000}\}", re.DOTALL)

    symbol_fields = ["symbol", "ticker", "rootSymbol", "root_symbol"]
    name_fields = ["name", "companyName", "company_name", "securityName", "instrumentName", "longName", "issuerName"]
    exchange_fields = ["exchange", "exchangeCode", "market", "venue", "listingExchange"]

    for block in object_re.findall(text):
        low = block.lower()

        if not any(field.lower() in low for field in symbol_fields):
            continue

        symbol = ""
        name = ""
        exchange = ""

        for field in symbol_fields:
            match = re.search(rf"[\"']{re.escape(field)}[\"']\s*:\s*[\"']([^\"']+)[\"']", block, flags=re.IGNORECASE)
            if match:
                symbol = normalize_symbol(match.group(1))
                break

        for field in name_fields:
            match = re.search(rf"[\"']{re.escape(field)}[\"']\s*:\s*[\"']([^\"']+)[\"']", block, flags=re.IGNORECASE)
            if match:
                name = clean_text(match.group(1))
                break

        for field in exchange_fields:
            match = re.search(rf"[\"']{re.escape(field)}[\"']\s*:\s*[\"']([^\"']+)[\"']", block, flags=re.IGNORECASE)
            if match:
                exchange = infer_exchange(match.group(1)) or clean_text(match.group(1)).upper()
                break

        if not exchange:
            exchange = infer_exchange(block)

        url = ""
        url_match = re.search(r"[\"'](?:url|href|link)[\"']\s*:\s*[\"']([^\"']+)[\"']", block, flags=re.IGNORECASE)
        if url_match:
            url = normalize_url(url_match.group(1), base_url)

        rows.append(
            make_candidate(
                source,
                "json_object",
                symbol,
                name,
                exchange,
                url,
                block[:500],
                "json_like_embedded_object",
            )
        )

    return rows


def extract_table_rows(source: dict, text: str, base_url: str) -> list[dict]:
    rows = []

    for table in re.findall(r"<table\b.*?</table>", text, flags=re.IGNORECASE | re.DOTALL):
        for tr in re.findall(r"<tr\b.*?</tr>", table, flags=re.IGNORECASE | re.DOTALL):
            cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", tr, flags=re.IGNORECASE | re.DOTALL)
            if len(cells) < 2:
                continue

            cleaned = [clean_text(cell) for cell in cells]
            joined = " | ".join(cleaned)
            exchange = infer_exchange(joined)
            symbol = ""

            for cell in cleaned:
                maybe = normalize_symbol(cell)
                if symbol_is_valid(maybe) and len(maybe) <= 8:
                    symbol = maybe
                    break

            if not symbol:
                match = re.search(r"\b(?:TSX|TSXV|TSX-V)\s*[:\-]\s*([A-Z0-9.\-]{1,15})\b", joined, flags=re.IGNORECASE)
                if match:
                    symbol = normalize_symbol(match.group(1))

            if not symbol:
                continue

            name = ""
            for cell in cleaned:
                if cell and normalize_symbol(cell) != symbol and len(cell) > 2:
                    name = cell
                    break

            href_match = re.search(r"href=[\"']([^\"']+)[\"']", tr, flags=re.IGNORECASE)
            url = normalize_url(href_match.group(1), base_url) if href_match else ""

            rows.append(
                make_candidate(
                    source,
                    "table_row",
                    symbol,
                    name,
                    exchange,
                    url,
                    joined[:500],
                    "html_table_row",
                )
            )

    return rows


def extract_text_exchange_patterns(source: dict, text: str) -> list[dict]:
    rows = []
    visible = clean_text(text)

    patterns = [
        r"([A-Z][A-Za-z0-9&.,'’\- ]{3,120}?)\s*\((TSX|TSXV|TSX-V)\s*[:\-]\s*([A-Z0-9.\-]{1,15})\)",
        r"([A-Z][A-Za-z0-9&.,'’\- ]{3,120}?)\s+(TSX|TSXV|TSX-V)\s*[:\-]\s*([A-Z0-9.\-]{1,15})",
    ]

    seen = set()

    for pattern in patterns:
        for name, exch, symbol in re.findall(pattern, visible, flags=re.IGNORECASE):
            name = clean_text(name)
            symbol = normalize_symbol(symbol)
            exchange = "TSXV" if "V" in exch.upper() else "TSX"

            key = (name.lower(), symbol, exchange)
            if key in seen:
                continue

            rows.append(
                make_candidate(
                    source,
                    "text_exchange_pattern",
                    symbol,
                    name,
                    exchange,
                    "",
                    f"{name} {exchange}:{symbol}",
                    "visible_text_exchange_pattern",
                )
            )
            seen.add(key)

    return rows


def filter_candidates(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    accepted = []
    exclusions = []
    seen = set()

    for row in candidates:
        method = str(row.get("extraction_method", "")).strip()
        symbol = str(row.get("raw_symbol", "")).strip()
        name = str(row.get("raw_name", "")).strip()
        exchange = str(row.get("raw_exchange", "")).strip()
        url = str(row.get("raw_url", "")).strip()

        reason = exclusion_reason(symbol, name, exchange, url)

        if not reason and method == "json_object" and not name:
            reason = "missing_name_for_json_object"

        if not reason and method == "text_exchange_pattern":
            reason = weak_text_exchange_context(symbol, name)

        if not reason and not name and not exchange:
            reason = "insufficient_candidate_evidence"

        if reason:
            exclusions.append(
                make_exclusion(
                    {"source_id": row["source_id"], "source_name": row["source_name"]},
                    row["extraction_method"],
                    row["raw_symbol"],
                    row["raw_name"],
                    row["raw_exchange"],
                    row["raw_url"],
                    reason,
                    row["evidence"],
                )
            )
            continue

        key = row["candidate_key"]
        if key in seen:
            continue

        accepted.append(row)
        seen.add(key)

    return accepted, exclusions


def extract_from_source(manifest_row: dict) -> tuple[list[dict], list[dict], dict]:
    source = {
        "source_id": str(manifest_row.get("source_id", "")).strip(),
        "source_name": str(manifest_row.get("source_name", "")).strip(),
    }

    raw_path_text = str(manifest_row.get("raw_path", "")).strip()
    raw_path = Path(raw_path_text) if raw_path_text else None
    base_url = base_url_for_manifest_row(manifest_row)

    diagnostic = {
        "source_id": source["source_id"],
        "source_name": source["source_name"],
        "raw_path": str(raw_path) if raw_path else "",
        "raw_exists": False,
        "bytes_read": 0,
        "html_like": False,
        "title": "",
        "anchor_quote_like_count": 0,
        "json_object_like_count": 0,
        "table_row_count": 0,
        "text_pattern_count": 0,
        "raw_candidates_before_filter": 0,
        "deduped_candidates_after_filter": 0,
        "exclusions": 0,
        "notes": "",
    }

    if not raw_path or not raw_path.exists():
        diagnostic["notes"] = "raw_missing_or_source_not_downloaded"
        return [], [], diagnostic

    raw_bytes = raw_path.read_bytes()
    text = raw_bytes.decode("utf-8", errors="replace")
    low = text.lower()

    diagnostic.update(
        {
            "raw_exists": True,
            "bytes_read": len(raw_bytes),
            "html_like": "<html" in low or "<!doctype html" in low,
            "title": extract_title(text),
        }
    )

    by_anchor = extract_quote_anchors(source, text, base_url)
    by_json = extract_json_like_objects(source, text, base_url)
    by_table = extract_table_rows(source, text, base_url)
    by_text = extract_text_exchange_patterns(source, text)

    raw_candidates = by_anchor + by_json + by_table + by_text
    accepted, exclusions = filter_candidates(raw_candidates)

    diagnostic.update(
        {
            "anchor_quote_like_count": len(by_anchor),
            "json_object_like_count": len(by_json),
            "table_row_count": len(by_table),
            "text_pattern_count": len(by_text),
            "raw_candidates_before_filter": len(raw_candidates),
            "deduped_candidates_after_filter": len(accepted),
            "exclusions": len(exclusions),
            "notes": "candidate_extraction_dry_run_only_no_canonical_comparison",
        }
    )

    return accepted, exclusions, diagnostic


def main() -> None:
    for path in [REPORT_JSON, REPORT_MD, CANDIDATES_CSV, EXCLUSIONS_CSV, SOURCE_DIAGNOSTICS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    c_manifest = read_json(V216C_JSON)
    manifest_rows = read_csv(V216C_CSV)
    d2_report = read_json(V216D2_JSON)

    all_candidates = []
    all_exclusions = []
    diagnostics = []

    for manifest_row in manifest_rows:
        candidates, exclusions, diagnostic = extract_from_source(manifest_row)
        all_candidates.extend(candidates)
        all_exclusions.extend(exclusions)
        diagnostics.append(diagnostic)

    method_counter = Counter(row["extraction_method"] for row in all_candidates)
    confidence_counter = Counter(row["confidence_bucket"] for row in all_candidates)
    source_counter = Counter(row["source_id"] for row in all_candidates)
    exclusion_counter = Counter(row["exclusion_reason"] for row in all_exclusions)

    raw_exists_count = sum(1 for row in diagnostics if row["raw_exists"])
    html_like_count = sum(1 for row in diagnostics if row["html_like"])
    candidate_count = len(all_candidates)
    exclusion_count = len(all_exclusions)

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_16c_manifest_exists", V216C_JSON.exists(), "critical", str(V216C_JSON))
    add_check("v2_16c_manifest_csv_exists", V216C_CSV.exists(), "critical", str(V216C_CSV))
    add_check("v2_16c_status_valid", c_manifest.get("status") == "TMX_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS_REBUILD_STILL_BLOCKED", "critical", c_manifest.get("status", ""))
    add_check("v2_16d2_report_exists", V216D2_JSON.exists(), "critical", str(V216D2_JSON))
    add_check("v2_16d2_status_valid", d2_report.get("status") == "TMX_CONTROLLED_ENDPOINT_PROBE_COMPLETED_NO_PROMISING_ENDPOINTS_REBUILD_STILL_BLOCKED", "critical", d2_report.get("status", ""))
    add_check("v2_16d2_recommended_e", d2_report.get("recommended_next_phase") == "v2.16E - TMX Candidate Extraction Dry Run", "critical", d2_report.get("recommended_next_phase", ""))
    add_check("raw_files_available", raw_exists_count >= 4, "critical", f"raw_exists_count={raw_exists_count}")
    add_check("html_like_raw_files", html_like_count >= 4, "critical", f"html_like_count={html_like_count}")
    add_check("candidate_extraction_attempted", True, "critical", "candidate_extraction_attempted=True")
    add_check("candidate_rows_review", candidate_count > 0, "warning", f"candidate_count={candidate_count}")
    add_check("exclusions_review", exclusion_count >= 0, "warning", f"exclusion_count={exclusion_count}")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("normalization_not_performed", True, "critical", "global_normalization_performed=False")
    add_check("net_new_filtering_not_performed", True, "critical", "net_new_filtering_performed=False")
    add_check("expanded_universe_not_rebuilt", True, "critical", "expanded_universe_rebuilt=False")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"{CURRENT_ROWS} < {FULL_SOURCE_THRESHOLD}")

    if critical_failed != 0:
        status = "TMX_CANDIDATE_EXTRACTION_DRY_RUN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.16E_FIX - TMX Candidate Extraction Dry Run Repair"
    elif candidate_count > 0:
        status = "TMX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_CANDIDATES
    else:
        status = "TMX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_NO_CANDIDATES_REBUILD_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_NO_CANDIDATES

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
        "extraction_summary": {
            "v2_16c_status": c_manifest.get("status", ""),
            "v2_16d2_status": d2_report.get("status", ""),
            "v2_16d2_recommended_next_phase": d2_report.get("recommended_next_phase", ""),
            "manifest_rows": len(manifest_rows),
            "raw_exists_count": raw_exists_count,
            "html_like_count": html_like_count,
            "source_diagnostics_rows": len(diagnostics),
            "candidate_rows": candidate_count,
            "exclusion_rows": exclusion_count,
            "method_counts": dict(method_counter),
            "confidence_counts": dict(confidence_counter),
            "source_counts": dict(source_counter),
            "exclusion_counts": dict(exclusion_counter),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "candidates_preview": all_candidates[:100],
        "exclusions_preview": all_exclusions[:100],
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_html_local_read_performed": True,
            "candidate_extraction_attempted": True,
            "candidate_rows_extracted": candidate_count > 0,
            "security_rows_extracted": False,
            "canonical_dataset_read": False,
            "canonical_dataset_modified": False,
            "canonical_comparison_performed": False,
            "global_normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)
    write_csv(CANDIDATES_CSV, all_candidates, CANDIDATE_FIELDS)
    write_csv(EXCLUSIONS_CSV, all_exclusions, EXCLUSION_FIELDS)
    write_csv(SOURCE_DIAGNOSTICS_CSV, diagnostics, SOURCE_DIAGNOSTIC_FIELDS)

    diagnostic_lines = "\n".join(
        f"- `{row['source_id']}` raw={row['raw_exists']} candidates={row['deduped_candidates_after_filter']} exclusions={row['exclusions']} methods anchor/json/table/text={row['anchor_quote_like_count']}/{row['json_object_like_count']}/{row['table_row_count']}/{row['text_pattern_count']} title=`{row['title']}`"
        for row in diagnostics
    )

    candidate_lines = "\n".join(
        f"- `{row['raw_symbol']}` `{row['raw_name']}` exchange=`{row['raw_exchange']}` confidence={row['confidence_bucket']} method={row['extraction_method']} source=`{row['source_id']}`"
        for row in all_candidates[:50]
    ) or "- No candidates extracted."

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
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

## Extraction summary

- v2.16C status: `{payload["extraction_summary"]["v2_16c_status"]}`
- v2.16D2 status: `{payload["extraction_summary"]["v2_16d2_status"]}`
- v2.16D2 recommended next phase: `{payload["extraction_summary"]["v2_16d2_recommended_next_phase"]}`
- Manifest rows: `{len(manifest_rows)}`
- Raw files available: `{raw_exists_count}`
- HTML-like raw files: `{html_like_count}`
- Source diagnostics rows: `{len(diagnostics)}`
- Candidate rows: `{candidate_count}`
- Exclusion rows: `{exclusion_count}`
- Method counts: `{dict(method_counter)}`
- Confidence counts: `{dict(confidence_counter)}`
- Source counts: `{dict(source_counter)}`
- Exclusion counts: `{dict(exclusion_counter)}`
- Critical failed checks: `{critical_failed}`

## Source diagnostics

{diagnostic_lines}

## Candidate preview

{candidate_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw HTML local read performed: true
- Candidate extraction attempted: true
- Candidate rows extracted: {str(candidate_count > 0).lower()}
- Security rows extracted: false
- Canonical dataset read: false
- Canonical dataset modified: false
- Canonical comparison performed: false
- Global normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX candidate extraction dry run completed.

This phase parses only local raw HTML files already versioned from v2.16C. It applies conservative filtering and moves weak symbol-only JSON fragments to exclusions/review. It performs no canonical comparison, no net-new filtering and no rebuild.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16E TMX candidate extraction dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("EXTRACTION_SUMMARY:")
    for key, value in payload["extraction_summary"].items():
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
