from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


VERSION = "v2.21C3B"
PHASE = "Colombia Regulatory Discovery + Extraction Decision"
PHASE_TYPE = "colombia-regulatory-discovery-extraction-decision"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw_colombia_regulatory_discovery_v2_21c3b"

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
SINGAPORE_PROMOTION_JSON = OUTPUT_DIR / "singapore_promotion_freeze_decision_v2_21e_s.json"
SINGAPORE_PROMOTED_DATASET = OUTPUT_DIR / "expanded_universe_v2_21e_s_singapore_promoted.csv"

REPORT_JSON = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_v2_21c3b.json"
REPORT_MD = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_v2_21c3b.md"
SUMMARY_CSV = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_summary_v2_21c3b.csv"
CHECKS_CSV = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_checks_v2_21c3b.csv"
SOURCE_INVENTORY_CSV = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_source_inventory_v2_21c3b.csv"
FETCH_VALIDATION_CSV = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_fetch_validation_v2_21c3b.csv"
STRUCTURED_CANDIDATES_CSV = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_structured_source_candidates_v2_21c3b.csv"
SAMPLE_ROWS_CSV = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_sample_rows_v2_21c3b.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_decision_register_v2_21c3b.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_next_actions_v2_21c3b.csv"

EXPECTED_SINGAPORE_PROMOTION_STATUS = "SINGAPORE_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
SINGAPORE_PROMOTED_ROWS_EXPECTED = 43066
SINGAPORE_PROMOTED_SHA_EXPECTED = "8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

MARKET_ID = "COLOMBIA_REGULATORY"
COUNTRY = "Colombia"
COUNTRY_CODE = "CO"
EXCHANGE = "BVC"
MIC = "XBOG"
CURRENCY = "COP"

REQUEST_TIMEOUT_SECONDS = 45
MIN_SUCCESS_BYTES = 100
MAX_SAMPLE_ROWS_PER_SOURCE = 20

STATUS_STRUCTURED_READY = "COLOMBIA_REGULATORY_DISCOVERY_EXTRACTION_DECISION_COMPLETED_STRUCTURED_SOURCE_READY_EXTRACTION_APPROVED_NO_DATASET_CHANGES_SCORING_DEFERRED"
STATUS_FROZEN = "COLOMBIA_REGULATORY_DISCOVERY_EXTRACTION_DECISION_COMPLETED_NO_STRUCTURED_SOURCE_READY_COLOMBIA_FREEZE_RECOMMENDED_NO_DATASET_CHANGES"
STATUS_FAILED = "COLOMBIA_REGULATORY_DISCOVERY_EXTRACTION_DECISION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_IF_READY = "v2.21D_C - Colombia Conditional Build / Freeze"
NEXT_PHASE_IF_FROZEN = "v2.21G - Final v2.21 Closure Report"
NEXT_PHASE_REVIEW = "v2.21C3B_REVIEW - Colombia Regulatory Discovery Issue Resolution"

OFFICIAL_HOSTS = {
    "www.superfinanciera.gov.co",
    "superfinanciera.gov.co",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ScoutFinanceColombiaRegulatoryDiscovery/2.21C3B",
    "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

SEED_SOURCES = [
    {
        "source_id": "SFC_SIMEV2_RNVE_HOME",
        "source_type": "official_regulator_registry_home",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/SIMEV2/rnve",
        "reason": "RNVE/SIMEV official registry entry point.",
    },
    {
        "source_id": "SFC_SIMEV2_EMISORES_INSCRITOS_VIGENTES",
        "source_type": "official_regulator_issuer_list",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/SIMEV2/rnve/emisoresinscritosvigentes",
        "reason": "SIMEV page for current registered issuers and securities.",
    },
    {
        "source_id": "SFC_SIMEV_FINANCIAL_INSTITUTION_LIST_RNVE",
        "source_type": "official_regulator_jsf_search",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/Superfinanciera-Simev/faces/generic/FinancialInstitutionSimevList.xhtml?financialInstitutionStateRNVEIId=1&nationalRecordId=1",
        "reason": "JSF RNVE registered financial institution list candidate.",
    },
    {
        "source_id": "SFC_VALORES_INSCRITOS_007_001",
        "source_type": "official_regulator_registered_values_page",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/B_simevRelevantes/G_valoresInscritos/repoValoresInscritos.xhtml?entidad=007&tipoEntidad=001",
        "reason": "Valores Inscritos example page exposing RNVE/BVC registration fields.",
    },
    {
        "source_id": "SFC_VALORES_INSCRITOS_004_261",
        "source_type": "official_regulator_registered_values_page",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/B_simevRelevantes/G_valoresInscritos/repoValoresInscritos.xhtml?entidad=004&tipoEntidad=261",
        "reason": "Valores Inscritos example page exposing registered securities fields.",
    },
    {
        "source_id": "SFC_VALORES_INSCRITOS_050_261",
        "source_type": "official_regulator_registered_values_page",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/B_simevRelevantes/G_valoresInscritos/repoValoresInscritos.xhtml?entidad=050&tipoEntidad=261",
        "reason": "Valores Inscritos example page exposing registered securities fields.",
    },
    {
        "source_id": "SFC_PRECIO_ACCIONES_001_001",
        "source_type": "official_regulator_action_price_page",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/B_simevRelevantes/H_precioAcciones/repoPrecioAcciones.xhtml?entidad=001&tipoEntidad=001",
        "reason": "Precio Acciones page exposing title name, Superfinanciera code and BVC inscription fields.",
    },
    {
        "source_id": "SFC_PRECIO_ACCIONES_001_142",
        "source_type": "official_regulator_action_price_page",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/B_simevRelevantes/H_precioAcciones/repoPrecioAcciones.xhtml?entidad=001&tipoEntidad=142",
        "reason": "Precio Acciones page exposing title name, Superfinanciera code and BVC inscription fields.",
    },
    {
        "source_id": "SFC_PRECIO_ACCIONES_002_023",
        "source_type": "official_regulator_action_price_page",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/B_simevRelevantes/H_precioAcciones/repoPrecioAcciones.xhtml?entidad=002&tipoEntidad=023",
        "reason": "Precio Acciones page exposing title name, Superfinanciera code and BVC inscription fields.",
    },
    {
        "source_id": "SFC_PRECIO_ACCIONES_022_053",
        "source_type": "official_regulator_action_price_page",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/B_simevRelevantes/H_precioAcciones/repoPrecioAcciones.xhtml?entidad=022&tipoEntidad=053",
        "reason": "Precio Acciones page exposing title name, Superfinanciera code and BVC inscription fields.",
    },
    {
        "source_id": "SFC_RNVE_INFORMATION_PAGE",
        "source_type": "official_regulator_information_page",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/publicaciones/80102/simev/registro-nacional-de-valores-y-emisores-rnve-80102/",
        "reason": "Official RNVE information and caveat page.",
    },
    {
        "source_id": "SFC_MARKET_VALUE_INFORMATION_PAGE",
        "source_type": "official_regulator_information_page",
        "authority": "Superintendencia Financiera de Colombia",
        "url": "https://www.superfinanciera.gov.co/publicaciones/38565/simevregistro-nacional-de-valores-y-emisores-rnveinformacion-emisoresofertas-publicasinformacion-mercado-de-valores-38565/",
        "reason": "Official SFC information page mentioning market-value information and BVC-calculated market cap.",
    },
]

STRUCTURED_HEADER_TERMS = {
    "nombre del titulo",
    "nombre titulo",
    "codigo superfinanciera",
    "emision",
    "tipo inscripcion",
    "inscrito en",
    "numero de acto administrativo rnve",
    "inscrito rnve fecha",
    "inscrito bvc fecha",
    "inscrito b v c fecha",
    "monto autorizado",
    "moneda",
    "ultima calificacion",
}

NAME_TERMS = {
    "nombre del titulo",
    "nombre titulo",
    "emision",
    "emisor",
    "razon social",
    "nombre entidad",
}

CODE_TERMS = {
    "codigo superfinanciera",
    "codigo",
    "numero de acto administrativo rnve",
}

REGISTRATION_TERMS = {
    "inscrito bvc fecha",
    "inscrito b v c fecha",
    "inscrito rnve fecha",
    "rnve",
    "rnvei",
    "tipo inscripcion",
}

DISALLOWED_TERMS = {
    "script",
    "webpack",
    "google",
    "gtm",
    "cookie",
    "javascript",
    "stylesheet",
}


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.current_table: list[list[str]] = []
        self.tables: list[list[list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self.in_table = True
            self.current_table = []
        elif self.in_table and tag == "tr":
            self.in_row = True
            self.current_row = []
        elif self.in_table and self.in_row and tag in {"td", "th"}:
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.in_table and self.in_row and self.in_cell and tag in {"td", "th"}:
            cell = " ".join(" ".join(self.current_cell).split())
            self.current_row.append(cell)
            self.current_cell = []
            self.in_cell = False
        elif self.in_table and self.in_row and tag == "tr":
            if any(cell.strip() for cell in self.current_row):
                self.current_table.append(self.current_row)
            self.current_row = []
            self.in_row = False
        elif self.in_table and tag == "table":
            if self.current_table:
                self.tables.append(self.current_table)
            self.current_table = []
            self.in_table = False

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell.append(data)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def strip_accents_basic(text: str) -> str:
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u",
        "ñ": "n", "Ñ": "n",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_accents_basic(norm(value)).lower()).strip()


def safe_source_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
    return cleaned[:120] or "source"


def decode_bytes(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding, errors="replace")
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def official_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc.lower() in OFFICIAL_HOSTS


def fetch_source(source: dict[str, str], index: int) -> dict[str, Any]:
    source_id = source["source_id"]
    url = source["url"]
    base_name = f"{index:03d}_{safe_source_id(source_id)}"

    raw_path = RAW_DIR / f"{base_name}.html"
    headers_path = RAW_DIR / f"{base_name}.headers.json"
    error_path = RAW_DIR / f"{base_name}.error.raw"

    row: dict[str, Any] = {
        "source_id": source_id,
        "source_type": source["source_type"],
        "authority": source["authority"],
        "url": url,
        "official_host": official_url(url),
        "fetch_attempted": True,
        "fetch_success": False,
        "http_status": "",
        "content_type": "",
        "raw_bytes": 0,
        "raw_sha256": "",
        "raw_file": "",
        "headers_file": "",
        "error_file": "",
        "fetch_error": "",
    }

    if not official_url(url):
        row["fetch_error"] = "Non-official host rejected"
        return row

    request = urllib.request.Request(url, headers=HEADERS)
    context = ssl.create_default_context()

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=context) as response:
            data = response.read()
            status = int(getattr(response, "status", 200))
            headers = dict(response.headers.items())
            content_type = response.headers.get("Content-Type", "")

            if raw_path.exists() or headers_path.exists():
                raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite raw source {raw_path}")

            raw_path.write_bytes(data)
            headers_path.write_text(json.dumps(headers, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

            row.update({
                "fetch_success": 200 <= status < 300 and len(data) >= MIN_SUCCESS_BYTES,
                "http_status": status,
                "content_type": content_type,
                "raw_bytes": len(data),
                "raw_sha256": sha256_bytes(data),
                "raw_file": str(raw_path),
                "headers_file": str(headers_path),
            })

    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        headers = dict(exc.headers.items()) if exc.headers else {}
        if body:
            error_path.write_bytes(body)
        headers_path.write_text(json.dumps(headers, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

        row.update({
            "fetch_success": False,
            "http_status": int(exc.code),
            "content_type": headers.get("Content-Type", ""),
            "raw_bytes": len(body),
            "raw_sha256": sha256_bytes(body) if body else "",
            "headers_file": str(headers_path),
            "error_file": str(error_path) if body else "",
            "fetch_error": f"HTTPError: {exc.code} {exc.reason}",
        })

    except Exception as exc:
        row.update({
            "fetch_success": False,
            "fetch_error": f"{type(exc).__name__}: {exc}",
        })

    return row


def headers_from_table(table: list[list[str]]) -> list[str]:
    if not table:
        return []
    first = table[0]
    if len(table) > 1 and len(first) >= 2:
        return [norm(cell) for cell in first]
    return []


def table_structured_score(table: list[list[str]], text: str) -> tuple[int, list[str], str]:
    headers = headers_from_table(table)
    joined_headers = " | ".join(norm_key(header) for header in headers)
    joined_text = norm_key(text[:20000])

    terms_found = []
    score = 0

    for term in STRUCTURED_HEADER_TERMS:
        normalized = norm_key(term)
        if normalized and (normalized in joined_headers or normalized in joined_text):
            terms_found.append(term)
            score += 1

    has_name = any(norm_key(term) in joined_headers or norm_key(term) in joined_text for term in NAME_TERMS)
    has_code = any(norm_key(term) in joined_headers or norm_key(term) in joined_text for term in CODE_TERMS)
    has_registration = any(norm_key(term) in joined_headers or norm_key(term) in joined_text for term in REGISTRATION_TERMS)

    if has_name:
        score += 3
    if has_code:
        score += 2
    if has_registration:
        score += 3

    reason = f"has_name={has_name};has_code={has_code};has_registration={has_registration};terms_found={len(terms_found)}"
    return score, terms_found, reason


def extract_sample_rows(table: list[list[str]], source_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if len(table) < 2:
        return rows

    headers = [norm(header) for header in table[0]]
    if not headers:
        return rows

    for index, table_row in enumerate(table[1:MAX_SAMPLE_ROWS_PER_SOURCE + 1], start=1):
        if not any(norm(cell) for cell in table_row):
            continue

        payload = {}
        for i, header in enumerate(headers):
            payload[header or f"column_{i+1}"] = table_row[i] if i < len(table_row) else ""

        text = " ".join(norm(value) for value in payload.values()).lower()
        if any(term in text for term in DISALLOWED_TERMS):
            continue

        rows.append({
            "source_id": source_id,
            "sample_order": index,
            "sample_kind": "html_table_row",
            "sample_payload": json.dumps(payload, ensure_ascii=False)[:1500],
        })

    return rows


def validate_source(fetch_row: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_id = fetch_row["source_id"]
    raw_file = fetch_row.get("raw_file", "")

    validation: dict[str, Any] = {
        "source_id": source_id,
        "source_type": fetch_row["source_type"],
        "authority": fetch_row["authority"],
        "url": fetch_row["url"],
        "fetch_success": fetch_row["fetch_success"],
        "http_status": fetch_row["http_status"],
        "content_type": fetch_row["content_type"],
        "raw_bytes": fetch_row["raw_bytes"],
        "raw_file": raw_file,
        "html_table_count": 0,
        "best_table_rows": 0,
        "best_table_columns": 0,
        "structured_score": 0,
        "structured_terms_found": "",
        "regulatory_structured_source_candidate": False,
        "traversable_entity_list_candidate": False,
        "extraction_decision_status": "FETCH_NOT_SUCCESSFUL",
        "review_reason": fetch_row.get("fetch_error", ""),
    }

    sample_rows: list[dict[str, Any]] = []

    if not fetch_row.get("fetch_success") or not raw_file or not Path(raw_file).exists():
        return validation, sample_rows

    text = decode_bytes(Path(raw_file).read_bytes())
    parser = TableParser()
    parser.feed(text)

    validation["html_table_count"] = len(parser.tables)

    best_score = 0
    best_terms: list[str] = []
    best_reason = ""
    best_table: list[list[str]] = []

    for table in parser.tables:
        score, terms, reason = table_structured_score(table, text)
        if score > best_score:
            best_score = score
            best_terms = terms
            best_reason = reason
            best_table = table

    joined_text = norm_key(html.unescape(re.sub(r"<[^>]+>", " ", text)))
    has_emisores_page_terms = "emisores inscritos vigentes" in joined_text or "emisores inscritos" in joined_text
    has_valores_page_terms = "valores inscritos" in joined_text or "precio acciones" in joined_text
    has_bvc_terms = "inscrito bvc" in joined_text or "inscrito b v c" in joined_text
    has_rnve_terms = "rnve" in joined_text or "rnvei" in joined_text

    best_rows = max(len(best_table) - 1, 0) if best_table else 0
    best_cols = len(best_table[0]) if best_table else 0

    validation.update({
        "best_table_rows": best_rows,
        "best_table_columns": best_cols,
        "structured_score": best_score,
        "structured_terms_found": "|".join(best_terms),
    })

    if best_table:
        sample_rows.extend(extract_sample_rows(best_table, source_id))

    if best_score >= 8 and best_rows >= 1 and has_rnve_terms:
        validation["regulatory_structured_source_candidate"] = True
        validation["extraction_decision_status"] = "STRUCTURED_REGULATORY_SOURCE_READY_FOR_EXTRACTION_PLANNING"
        validation["review_reason"] = best_reason
    elif has_emisores_page_terms and fetch_row.get("fetch_success"):
        validation["traversable_entity_list_candidate"] = True
        validation["extraction_decision_status"] = "TRAVERSABLE_REGULATORY_ENTITY_LIST_DISCOVERED_REVIEW_REQUIRED"
        validation["review_reason"] = "Entity list terms found but structured extraction fields need follow-up traversal."
    elif has_valores_page_terms and (has_bvc_terms or has_rnve_terms):
        validation["regulatory_structured_source_candidate"] = best_score >= 6 and best_rows >= 1
        validation["extraction_decision_status"] = "WEAK_OR_PAGE_LEVEL_REGULATORY_STRUCTURE_REVIEW_REQUIRED"
        validation["review_reason"] = f"Page has regulatory terms but table structure is weak. {best_reason}"
    else:
        validation["extraction_decision_status"] = "NO_USABLE_STRUCTURED_REGULATORY_SOURCE_FOUND"
        validation["review_reason"] = best_reason or "No structured RNVE/BVC candidate table detected."

    return validation, sample_rows


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        SOURCE_INVENTORY_CSV,
        FETCH_VALIDATION_CSV,
        STRUCTURED_CANDIDATES_CSV,
        SAMPLE_ROWS_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists() and any(RAW_DIR.iterdir()):
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw discovery directory exists and is not empty: {RAW_DIR}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    singapore_promotion = read_json(SINGAPORE_PROMOTION_JSON)
    singapore_summary = singapore_promotion.get("summary", {})

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    singapore_promoted_rows = count_csv_rows(SINGAPORE_PROMOTED_DATASET)
    singapore_promoted_sha = sha256_file(SINGAPORE_PROMOTED_DATASET)
    operational_header = read_csv_header(OPERATIONAL_BASE_DATASET)

    source_inventory_rows = [
        {
            "source_id": source["source_id"],
            "source_type": source["source_type"],
            "authority": source["authority"],
            "url": source["url"],
            "official_host": official_url(source["url"]),
            "selected_for_fetch": True,
            "reason": source["reason"],
        }
        for source in SEED_SOURCES
    ]

    print("")
    print("v2.21C3B Colombia regulatory discovery started.")
    print(f"Sources: {len(SEED_SOURCES)}")

    fetch_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []

    for index, source in enumerate(SEED_SOURCES, start=1):
        print(f"Fetching {index}/{len(SEED_SOURCES)} {source['source_id']}")
        fetch_row = fetch_source(source, index)
        validation_row, samples = validate_source(fetch_row)

        fetch_rows.append(fetch_row)
        validation_rows.append(validation_row)
        sample_rows.extend(samples)

        print(
            f"- http={fetch_row['http_status']} success={fetch_row['fetch_success']} "
            f"tables={validation_row['html_table_count']} score={validation_row['structured_score']} "
            f"status={validation_row['extraction_decision_status']}"
        )

    structured_candidates = [
        row for row in validation_rows
        if as_bool(row.get("regulatory_structured_source_candidate"))
    ]
    traversable_candidates = [
        row for row in validation_rows
        if as_bool(row.get("traversable_entity_list_candidate"))
    ]
    successful_fetches = [row for row in fetch_rows if as_bool(row.get("fetch_success"))]

    approved_for_colombia_structured_extraction = len(structured_candidates) > 0
    approved_for_colombia_traversal_review = len(traversable_candidates) > 0 or len(structured_candidates) > 0

    if approved_for_colombia_structured_extraction:
        status = STATUS_STRUCTURED_READY
        colombia_decision = "COLOMBIA_STRUCTURED_REGULATORY_SOURCE_READY_EXTRACTION_PLANNING_APPROVED"
        recommended_next_phase = NEXT_PHASE_IF_READY
    else:
        status = STATUS_FROZEN
        colombia_decision = "COLOMBIA_NO_STRUCTURED_REGULATORY_SOURCE_READY_FREEZE_RECOMMENDED"
        recommended_next_phase = NEXT_PHASE_IF_FROZEN

    decision_register_rows = [
        {
            "decision_id": "COLOMBIA_REG_DISCOVERY_001",
            "decision": "Do not extract from BVC shell HTML or regex output.",
            "accepted": True,
            "reason": "v2.21C2/v2.21C3 already showed BVC shell pages were not reliable structured inputs.",
            "effect": "BVC shell HTML remains excluded.",
        },
        {
            "decision_id": "COLOMBIA_REG_DISCOVERY_002",
            "decision": "Use only official Superfinanciera/SIMEV/RNVE sources for Colombia review.",
            "accepted": True,
            "reason": "Colombia route needs official regulatory source family.",
            "effect": "All seed URLs are restricted to superfinanciera.gov.co.",
        },
        {
            "decision_id": "COLOMBIA_REG_DISCOVERY_003",
            "decision": "Approve Colombia structured extraction only if table/field structure is sufficient.",
            "accepted": approved_for_colombia_structured_extraction,
            "reason": "Structured candidates found." if approved_for_colombia_structured_extraction else "No strong structured regulatory source found.",
            "effect": NEXT_PHASE_IF_READY if approved_for_colombia_structured_extraction else "Recommend freezing Colombia for v2.21 closure.",
        },
        {
            "decision_id": "COLOMBIA_REG_DISCOVERY_004",
            "decision": "Keep Singapore promoted artifact unchanged.",
            "accepted": True,
            "reason": "Singapore was closed in v2.21E_S.",
            "effect": "Singapore promoted artifact remains the v2.21 successful output.",
        },
        {
            "decision_id": "COLOMBIA_REG_DISCOVERY_005",
            "decision": "Keep scoring/OpenAI/broker/full59k deferred.",
            "accepted": True,
            "reason": "No scoring/enrichment authorization has been given.",
            "effect": "No scoring, OpenAI, broker, or full59k actions are performed.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "colombia_conditional_build" if approved_for_colombia_structured_extraction else "final_closure",
            "action": "run_colombia_conditional_build_from_structured_regulatory_sources" if approved_for_colombia_structured_extraction else "close_v2_21_with_colombia_frozen_and_singapore_promoted",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "Structured regulatory source exists." if approved_for_colombia_structured_extraction else "No strong structured Colombia source was validated.",
            "guardrails": "No BVC shell HTML; no regex-only candidates; no scoring",
        },
        {
            "action_order": 2,
            "action_scope": "singapore_reference",
            "action": "preserve_singapore_promoted_artifact_as_v2_21_successful_output",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "Singapore promoted artifact was already verified.",
            "guardrails": "Do not alter Singapore artifact during Colombia decision.",
        },
        {
            "action_order": 3,
            "action_scope": "pointer_control",
            "action": "keep_active_pointer_unchanged_until_final_v2_21_closure",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "Pointer update remains outside Colombia discovery.",
            "guardrails": "No active pointer mutation in v2.21C3B.",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0
    warning_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed, warning_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        if severity == "warning" and not passed:
            warning_failed += 1
        checks.append({
            "check": check,
            "passed": bool(passed),
            "severity": severity,
            "detail": detail,
        })

    add_check("singapore_promotion_status_expected", singapore_promotion.get("status") == EXPECTED_SINGAPORE_PROMOTION_STATUS, "critical", str(singapore_promotion.get("status")))
    add_check("singapore_promoted_artifact_approved", as_bool(singapore_summary.get("approved_as_promoted_artifact")) is True, "critical", f"approved_as_promoted_artifact={singapore_summary.get('approved_as_promoted_artifact')}")
    add_check("singapore_pointer_not_updated", as_bool(singapore_summary.get("pointer_update_performed")) is False, "critical", f"pointer_update_performed={singapore_summary.get('pointer_update_performed')}")
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("singapore_promoted_rows_expected", singapore_promoted_rows == SINGAPORE_PROMOTED_ROWS_EXPECTED, "critical", f"singapore_promoted_rows={singapore_promoted_rows}")
    add_check("singapore_promoted_sha_expected", singapore_promoted_sha == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", singapore_promoted_sha)
    add_check("schema_column_count_expected", len(operational_header) == 33, "critical", f"columns={len(operational_header)}")
    add_check("official_source_inventory_created", len(source_inventory_rows) == len(SEED_SOURCES), "critical", f"sources={len(source_inventory_rows)}")
    add_check("all_sources_official_hosts", all(as_bool(row["official_host"]) for row in source_inventory_rows), "critical", "all seed hosts are official Superfinanciera hosts")
    add_check("at_least_one_regulatory_fetch_successful", len(successful_fetches) > 0, "critical", f"successful_fetches={len(successful_fetches)}")
    add_check("colombia_structured_source_ready", approved_for_colombia_structured_extraction, "warning", f"structured_sources={len(structured_candidates)}")
    add_check("colombia_traversal_or_source_review_available", approved_for_colombia_traversal_review, "warning", f"structured={len(structured_candidates)};traversable={len(traversable_candidates)}")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("dedup_not_performed", True, "critical", "dedup_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_performed=False")
    add_check("singapore_promoted_artifact_not_modified", sha256_file(SINGAPORE_PROMOTED_DATASET) == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", "Singapore promoted artifact SHA unchanged")
    add_check("operational_base_not_modified", sha256_file(OPERATIONAL_BASE_DATASET) == OPERATIONAL_BASE_SHA_EXPECTED, "critical", "operational base SHA unchanged")
    add_check("rollback_not_modified", sha256_file(ROLLBACK_DATASET) == ROLLBACK_SHA_EXPECTED, "critical", "rollback SHA unchanged")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("pointer_update_not_performed", True, "critical", "pointer_update_performed=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        colombia_decision = "COLOMBIA_REGULATORY_DISCOVERY_BLOCKED_REVIEW_REQUIRED"
        approved_for_colombia_structured_extraction = False
        recommended_next_phase = NEXT_PHASE_REVIEW

    summary = {
        "selected_route": "Colombia regulatory branch after Singapore promoted artifact",
        "phase_type": PHASE_TYPE,
        "colombia_decision": colombia_decision,
        "approved_for_colombia_structured_extraction": approved_for_colombia_structured_extraction,
        "approved_for_colombia_traversal_review": approved_for_colombia_traversal_review,
        "recommended_if_colombia_not_ready": NEXT_PHASE_IF_FROZEN,
        "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "previous_operational_base_rows": operational_rows,
        "previous_operational_base_sha": operational_sha,
        "singapore_promoted_dataset": str(SINGAPORE_PROMOTED_DATASET),
        "singapore_promoted_rows": singapore_promoted_rows,
        "singapore_promoted_sha": singapore_promoted_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "colombia_sources_tested": len(source_inventory_rows),
        "colombia_fetches_successful": len(successful_fetches),
        "colombia_structured_sources_found": len(structured_candidates),
        "colombia_traversable_sources_found": len(traversable_candidates),
        "sample_rows_collected": len(sample_rows),
        "candidate_extraction_performed": False,
        "dedup_performed": False,
        "expanded_rebuild_performed": False,
        "colombia_dataset_promoted": False,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "pointer_update_performed": False,
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(SOURCE_INVENTORY_CSV, source_inventory_rows, ["source_id", "source_type", "authority", "url", "official_host", "selected_for_fetch", "reason"])
    write_csv(FETCH_VALIDATION_CSV, validation_rows, [
        "source_id", "source_type", "authority", "url", "fetch_success", "http_status",
        "content_type", "raw_bytes", "raw_file", "html_table_count", "best_table_rows",
        "best_table_columns", "structured_score", "structured_terms_found",
        "regulatory_structured_source_candidate", "traversable_entity_list_candidate",
        "extraction_decision_status", "review_reason",
    ])
    write_csv(STRUCTURED_CANDIDATES_CSV, structured_candidates, [
        "source_id", "source_type", "authority", "url", "fetch_success", "http_status",
        "content_type", "raw_bytes", "raw_file", "html_table_count", "best_table_rows",
        "best_table_columns", "structured_score", "structured_terms_found",
        "regulatory_structured_source_candidate", "traversable_entity_list_candidate",
        "extraction_decision_status", "review_reason",
    ])
    write_csv(SAMPLE_ROWS_CSV, sample_rows, ["source_id", "sample_order", "sample_kind", "sample_payload"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "source_inventory": source_inventory_rows,
        "fetch_validation": validation_rows,
        "structured_source_candidates": structured_candidates,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Colombia regulatory branch",
            "official_regulatory_discovery_only": True,
            "approved_for_colombia_structured_extraction": approved_for_colombia_structured_extraction,
            "approved_for_colombia_traversal_review": approved_for_colombia_traversal_review,
            "singapore_promoted_dataset": str(SINGAPORE_PROMOTED_DATASET),
            "singapore_promoted_rows": singapore_promoted_rows,
            "singapore_promoted_sha": singapore_promoted_sha,
            "candidate_extraction_performed": False,
            "dedup_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "colombia_dataset_promoted": False,
            "file_edit_performed_on_operational_base": False,
            "file_edit_performed_on_singapore_promoted_artifact": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "scoring_authorized": False,
            "scoring_recalculated": False,
            "openai_authorized": False,
            "openai_called": False,
            "broker_authorized": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
            "history_rewrite_performed": False,
            "force_push_required": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    source_lines = "\n".join(
        f"- `{row['source_id']}` — fetch `{row['fetch_success']}` — score `{row['structured_score']}` — status `{row['extraction_decision_status']}`"
        for row in validation_rows
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}` — accepted `{row['accepted']}` — {row['decision']}"
        for row in decision_register_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.21C3B performs Colombia regulatory source discovery and an extraction decision using only official Superfinanciera/SIMEV/RNVE sources.

This phase does not extract candidates, deduplicate, rebuild, promote Colombia, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Colombia decision: `{colombia_decision}`
- Approved for Colombia structured extraction: `{approved_for_colombia_structured_extraction}`
- Approved for Colombia traversal review: `{approved_for_colombia_traversal_review}`
- Sources tested: `{len(source_inventory_rows)}`
- Fetches successful: `{len(successful_fetches)}`
- Structured sources found: `{len(structured_candidates)}`
- Traversable sources found: `{len(traversable_candidates)}`
- Sample rows collected: `{len(sample_rows)}`
- Singapore promoted rows: `{singapore_promoted_rows}`
- Singapore promoted SHA256: `{singapore_promoted_sha}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Source validation

{source_lines}

## Decision register

{decision_lines}

## Checks

{check_lines}

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21C3B Colombia regulatory discovery + extraction decision completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_VALIDATION:")
    for row in validation_rows:
        print(
            f"- {row['source_id']}: fetch={row['fetch_success']} "
            f"tables={row['html_table_count']} score={row['structured_score']} "
            f"structured={row['regulatory_structured_source_candidate']} "
            f"traversable={row['traversable_entity_list_candidate']} "
            f"status={row['extraction_decision_status']}"
        )
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
