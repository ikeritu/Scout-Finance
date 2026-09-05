"""Block 9W, part 2: parse the real iXBRL/ESEF report(s) fetched by
fetch_europe_accounts_documents_v2_38w.py into structured fundamental
records for a fixed, small set of standard ifrs-full:* concepts.

This is a targeted extractor, not a general XBRL engine: it reads
ix:nonFraction facts by name, resolves each fact's contextRef to a real
period (duration or instant) via the document's own xbrli:context
definitions, and its unitRef to a real currency via xbrli:unit -- it does
not attempt dimensional/segment breakdowns, prior-year restatement
handling beyond picking the latest period, or any concept outside the
fixed target list in the contract. Only tagged facts for the single most
recent reporting period (latest duration for flow concepts, latest
instant for stock concepts) are extracted; comparative prior-year facts
that share the same concept name are intentionally left unextracted in
this pass.

Real parsing details confirmed against Softcat's actual 2025 filing
before writing this, not assumed:
  - Root element parses cleanly with the stdlib xml.etree.ElementTree
    (real namespaces: xbrli=http://www.xbrl.org/2003/instance,
    ix=http://www.xbrl.org/2013/inlineXBRL).
  - A fact's numeric text can have literal spaces interspersed inside the
    digits for visual layout (e.g. "1 ,45 8,4 1 1") and can be split
    across nested child elements -- read via itertext(), not .text, and
    all whitespace is stripped before removing thousand-separator commas.
  - format="ixt4:num-dot-decimal" means "." is the decimal separator and
    "," is a thousands separator to discard, not a decimal comma.
  - scale (power-of-ten multiplier) and sign="-" (value negation) are
    both real, both must be applied, and are recorded on the output row
    alongside the already-scaled value so the transformation is
    traceable, not hidden.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_ixbrl_fundamentals_contract_v1.json"

NS = {
    "xhtml": "http://www.w3.org/1999/xhtml",
    "ix": "http://www.xbrl.org/2013/inlineXBRL",
    "xbrli": "http://www.xbrl.org/2003/instance",
}
WHITESPACE_RE = re.compile(r"\s+")


def load_contexts(root) -> dict[str, dict[str, str]]:
    contexts: dict[str, dict[str, str]] = {}
    for ctx in root.iter(f"{{{NS['xbrli']}}}context"):
        ctx_id = ctx.get("id")
        period = ctx.find(f"{{{NS['xbrli']}}}period")
        if period is None:
            continue
        # A context with a <xbrli:scenario> (or a <xbrli:segment> under
        # entity) carries a dimensional qualifier -- e.g. one component of
        # equity (share capital, retained earnings, ...) rather than the
        # undimensioned "total" line item real filings also tag for the
        # same date. Confirmed against Softcat's real filing: c-3 (plain,
        # Assets/total-Equity) has no scenario; c-26 (a single equity
        # component) does. Only the plain context is the total we want.
        is_dimensional = ctx.find(f"{{{NS['xbrli']}}}scenario") is not None or ctx.find(f"{{{NS['xbrli']}}}entity/{{{NS['xbrli']}}}segment") is not None
        instant = period.find(f"{{{NS['xbrli']}}}instant")
        if instant is not None:
            contexts[ctx_id] = {"kind": "instant", "date": instant.text.strip(), "dimensional": is_dimensional}
            continue
        start = period.find(f"{{{NS['xbrli']}}}startDate")
        end = period.find(f"{{{NS['xbrli']}}}endDate")
        if start is not None and end is not None:
            contexts[ctx_id] = {"kind": "duration", "start": start.text.strip(), "end": end.text.strip(), "dimensional": is_dimensional}
    return contexts


def load_units(root) -> dict[str, str]:
    units: dict[str, str] = {}
    for unit in root.iter(f"{{{NS['xbrli']}}}unit"):
        unit_id = unit.get("id")
        measure = unit.find(f"{{{NS['xbrli']}}}measure")
        if measure is not None and measure.text and ":" in measure.text:
            units[unit_id] = measure.text.split(":", 1)[1]
    return units


def clean_number_text(raw_text: str) -> float | None:
    text = WHITESPACE_RE.sub("", raw_text)
    text = text.replace(",", "")
    if not text or text in {"-", "—"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def load_facts(root, target_concepts: set[str]) -> list[dict[str, Any]]:
    facts = []
    for elem in root.iter(f"{{{NS['ix']}}}nonFraction"):
        name = elem.get("name")
        if name not in target_concepts:
            continue
        raw_text = "".join(elem.itertext())
        value = clean_number_text(raw_text)
        if value is None:
            continue
        scale = int(elem.get("scale", "0"))
        sign = elem.get("sign", "")
        value = value * (10 ** scale)
        if sign == "-":
            value = -value
        facts.append({
            "concept": name, "context_ref": elem.get("contextRef"), "unit_ref": elem.get("unitRef"),
            "raw_text": raw_text, "scale": scale, "sign": sign, "value": value,
            "decimals": elem.get("decimals", ""), "format": elem.get("format", ""),
        })
    return facts


def latest_period_key(contexts: dict[str, dict[str, str]], context_refs: set[str], kind: str) -> str | None:
    """The most recent period (by end date / instant date) among the given
    contexts, considering ONLY non-dimensional ("total") contexts of the
    requested kind -- never a dimensional breakdown (see load_contexts)."""
    key = "end" if kind == "duration" else "date"
    candidates = [contexts[ctx_id][key] for ctx_id in context_refs if ctx_id in contexts and contexts[ctx_id]["kind"] == kind and not contexts[ctx_id]["dimensional"]]
    return max(candidates) if candidates else None


def extract_company(xhtml_path: Path, company_row: dict[str, str], contract: dict[str, Any]) -> list[dict[str, Any]]:
    import xml.etree.ElementTree as ET

    tree = ET.parse(xhtml_path)
    root = tree.getroot()
    contexts = load_contexts(root)
    units = load_units(root)
    target_concepts = set(contract["target_ifrs_concepts"])
    flow_concepts = set(contract["flow_concepts"])
    stock_concepts = set(contract["stock_concepts"])
    facts = load_facts(root, target_concepts)

    duration_refs = {f["context_ref"] for f in facts if f["concept"] in flow_concepts}
    instant_refs = {f["context_ref"] for f in facts if f["concept"] in stock_concepts}
    latest_duration_end = latest_period_key(contexts, duration_refs, "duration")
    latest_instant_date = latest_period_key(contexts, instant_refs, "instant")

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    records = []
    seen_concepts = set()
    for fact in facts:
        is_flow = fact["concept"] in flow_concepts
        ctx = contexts.get(fact["context_ref"], {})
        if not ctx or ctx["dimensional"]:
            continue  # only the undimensioned "total" tagging is a canonical figure
        period_matches = (is_flow and ctx.get("end") == latest_duration_end) or (not is_flow and ctx.get("date") == latest_instant_date)
        if not period_matches:
            continue
        if fact["concept"] in seen_concepts:
            continue  # first (and only) non-dimensional match per concept for the target period
        seen_concepts.add(fact["concept"])
        records.append({
            "asset_id": company_row["asset_id"], "ticker": company_row["ticker"],
            "company_number": company_row["company_number"], "company_name": company_row["resolved_company_name"],
            "concept": fact["concept"], "statement_kind": "flow" if is_flow else "stock",
            "period_type": ctx.get("kind", ""), "period_start": ctx.get("start", ""), "period_end": ctx.get("end") or ctx.get("date", ""),
            "value": fact["value"], "raw_value_text": fact["raw_text"], "scale": fact["scale"], "sign": fact["sign"],
            "currency": units.get(fact["unit_ref"], ""), "source_document": xhtml_path.name,
            "extraction_method": "targeted_ifrs_full_concept_ix_nonFraction", "normalized_fundamentals_present": True,
            "phase": "v2.38W-europe-ixbrl-fundamentals", "created_at_utc": created_at,
        })

    missing = target_concepts - seen_concepts
    for concept in sorted(missing):
        records.append({
            "asset_id": company_row["asset_id"], "ticker": company_row["ticker"],
            "company_number": company_row["company_number"], "company_name": company_row["resolved_company_name"],
            "concept": concept, "statement_kind": "flow" if concept in flow_concepts else "stock",
            "period_type": "", "period_start": "", "period_end": "", "value": None, "raw_value_text": "",
            "scale": None, "sign": "", "currency": "", "source_document": xhtml_path.name,
            "extraction_method": "not_tagged_in_document", "normalized_fundamentals_present": False,
            "phase": "v2.38W-europe-ixbrl-fundamentals", "created_at_utc": created_at,
        })
    return records


def build(fetch_matrix: Path, output_dir: Path, records_output: Path) -> dict[str, Any]:
    import csv

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    with fetch_matrix.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("fetch_status") == "fetched"]

    all_records: list[dict[str, Any]] = []
    per_company_coverage = []
    for row in rows:
        xhtml_path = ROOT / row["raw_xhtml_path"]
        if not xhtml_path.exists():
            per_company_coverage.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "status": "raw_document_missing_rerun_fetch"})
            continue
        records = extract_company(xhtml_path, row, contract)
        all_records.extend(records)
        extracted = sum(1 for r in records if r["value"] is not None)
        per_company_coverage.append({
            "asset_id": row["asset_id"], "ticker": row["ticker"], "status": "normalized",
            "concepts_extracted": extracted, "concepts_expected": len(contract["target_ifrs_concepts"]),
        })

    records_output.parent.mkdir(parents=True, exist_ok=True)
    tmp = records_output.with_suffix(records_output.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(records_output)

    report = {
        "phase": "v2.38W-europe-ixbrl-fundamentals", "companies_with_fetched_document": len(rows),
        "total_records": len(all_records), "extracted_records": sum(1 for r in all_records if r["value"] is not None),
        "not_tagged_records": sum(1 for r in all_records if r["value"] is None),
        "per_company_coverage": per_company_coverage, "normalized_fundamentals_created": len(all_records) > 0,
        "network_used": False, "scoring_created": False, "ranking_created": False, "recommendations_created": False,
        "phase9c_authorized": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp2 = (output_dir / "europe_ixbrl_fundamentals_coverage_report_v2_38w.json").with_suffix(".json.tmp")
    tmp2.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp2.replace(output_dir / "europe_ixbrl_fundamentals_coverage_report_v2_38w.json")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-matrix", type=Path, default=ROOT / "outputs/full_universe_source_acquisition/v2_38w_europe_ixbrl_fundamentals/europe_accounts_document_fetch_matrix_v2_38w.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / contract["output_directory"])
    parser.add_argument("--records-output", type=Path, default=ROOT / contract["records_output"])
    args = parser.parse_args()
    print(json.dumps(build(args.fetch_matrix, args.output_dir, args.records_output), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
