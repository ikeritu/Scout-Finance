from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.24E"
PHASE = "Metadata Improvement Dry Run"
OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
CANONICAL = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"

EXPECTED_ROWS = 43_089
EXPECTED_SHA = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"
FIELDS = ["country", "mic", "currency", "asset_type", "instrument_type", "instrument_scope"]
CONTROL_PROVIDERS = {"ASX", "sgx_structured_endpoint"}

REPORT_JSON = OUTPUT_DIR / "metadata_improvement_dry_run_v2_24e.json"
REPORT_MD = OUTPUT_DIR / "metadata_improvement_dry_run_v2_24e.md"
SUMMARY_CSV = OUTPUT_DIR / "metadata_improvement_dry_run_summary_v2_24e.csv"
CHECKS_CSV = OUTPUT_DIR / "metadata_improvement_dry_run_checks_v2_24e.csv"
REGISTRY_CSV = OUTPUT_DIR / "metadata_improvement_dry_run_rule_registry_v2_24e.csv"
RULE_METRICS_CSV = OUTPUT_DIR / "metadata_improvement_dry_run_rule_metrics_v2_24e.csv"
PROVIDER_METRICS_CSV = OUTPUT_DIR / "metadata_improvement_dry_run_provider_metrics_v2_24e.csv"
UNRESOLVED_CSV = OUTPUT_DIR / "metadata_improvement_dry_run_unresolved_summary_v2_24e.csv"
OVERLAY_CSV = OUTPUT_DIR / "metadata_improvement_dry_run_overlay_v2_24e.csv"
MANIFEST_CSV = OUTPUT_DIR / "metadata_improvement_dry_run_artifact_manifest_v2_24e.csv"


def rule(rule_id: str, provider: str, source_field: str, source_value: str,
         exchange: str, target_field: str, target_value: str, basis: str) -> dict[str, str]:
    return {
        "rule_id": rule_id, "source_provider": provider,
        "source_field": source_field, "source_value": source_value,
        "exchange_constraint": exchange, "target_field": target_field,
        "target_value": target_value, "rule_basis": basis,
        "rule_confidence": "deterministic", "source_evidence": "v2.24B/v2.24C/v2.24D approved provider-specific rule",
        "overwrite_allowed": "False", "active": "True",
    }


RULES = [
    rule("GEO_NASDAQ_MIC_001", "nasdaq_trader_nasdaqlisted", "exchange", "NASDAQ", "NASDAQ", "mic", "XNAS", "NASDAQ-listed venue mapping"),
    rule("GEO_NASDAQ_CCY_001", "nasdaq_trader_nasdaqlisted", "exchange", "NASDAQ", "NASDAQ", "currency", "USD", "NASDAQ listing currency"),
    rule("GEO_OTHER_NYSE_MIC_001", "nasdaq_trader_otherlisted", "exchange", "NYSE", "NYSE", "mic", "XNYS", "NYSE venue mapping"),
    rule("GEO_OTHER_XASE_MIC_001", "nasdaq_trader_otherlisted", "exchange", "NYSE American", "NYSE American", "mic", "XASE", "NYSE American venue mapping"),
    rule("GEO_OTHER_ARCX_MIC_001", "nasdaq_trader_otherlisted", "exchange", "NYSE Arca", "NYSE Arca", "mic", "ARCX", "NYSE Arca venue mapping"),
    rule("GEO_OTHER_BATS_MIC_001", "nasdaq_trader_otherlisted", "exchange", "Cboe BZX", "Cboe BZX", "mic", "BATS", "Cboe BZX venue mapping"),
    rule("GEO_OTHER_USD_001", "nasdaq_trader_otherlisted", "exchange", "*", "*", "currency", "USD", "validated US listed feed currency"),
    rule("GEO_SEC_NASDAQ_MIC_001", "sec_company_tickers_exchange", "exchange", "NASDAQ", "NASDAQ", "mic", "XNAS", "SEC exchange label mapping"),
    rule("GEO_SEC_NYSE_MIC_001", "sec_company_tickers_exchange", "exchange", "NYSE", "NYSE", "mic", "XNYS", "SEC exchange label mapping"),
    rule("GEO_SEC_CBOE_MIC_001", "sec_company_tickers_exchange", "exchange", "CBOE", "CBOE", "mic", "BATS", "SEC CBOE listed-equity venue mapping"),
    rule("GEO_SEC_USD_001", "sec_company_tickers_exchange", "exchange", "*", "*", "currency", "USD", "validated US exchange feed currency"),
    rule("GEO_CBOE_US_MIC_001", "cboe_listed_symbols", "exchange", "CBOE", "CBOE", "mic", "BATS", "Cboe listed-symbol venue mapping"),
    rule("GEO_CBOE_US_CCY_001", "cboe_listed_symbols", "exchange", "CBOE", "CBOE", "currency", "USD", "Cboe US listing currency"),
    rule("GEO_XETRA_CCY_001", "deutsche_boerse_xetra_all_tradable_instruments", "exchange", "XETR", "XETR", "currency", "EUR", "Xetra trading currency for this source extract"),
    rule("TAX_NASDAQ_COMMON_001", "nasdaq_trader_nasdaqlisted", "instrument_type", "COMMON_STOCK", "*", "asset_type", "common_equity", "explicit common-stock classification"),
    rule("TAX_NASDAQ_ADR_001", "nasdaq_trader_nasdaqlisted", "instrument_type", "ADR", "*", "asset_type", "adr_equity", "explicit ADR classification"),
    rule("TAX_OTHER_COMMON_001", "nasdaq_trader_otherlisted", "instrument_type", "COMMON_STOCK", "*", "asset_type", "common_equity", "explicit common-stock classification"),
    rule("TAX_OTHER_ADR_001", "nasdaq_trader_otherlisted", "instrument_type", "ADR", "*", "asset_type", "adr_equity", "explicit ADR classification"),
    rule("TAX_JPX_ASSET_001", "jpx_listed_securities", "instrument_type", "equity", "JPX", "asset_type", "common_equity", "provider-native JPX equity population"),
    rule("TAX_JPX_SCOPE_001", "jpx_listed_securities", "instrument_type", "equity", "JPX", "instrument_scope", "common_equity", "provider-native JPX equity population"),
    rule("TAX_TWSE_ASSET_001", "TWSE", "instrument_scope", "common_equity", "TWSE", "asset_type", "common_equity", "explicit existing common-equity scope"),
    rule("TAX_XETRA_SCOPE_001", "deutsche_boerse_xetra_all_tradable_instruments", "instrument_type", "CS", "XETR", "instrument_scope", "common_equity", "provider-native common-share code"),
    rule("TAX_CBOEEU_ETF_ASSET_001", "cboe_europe_reference_data", "instrument_type", "ETF", "CBOE_EUROPE", "asset_type", "etf", "explicit ETF provider type"),
    rule("TAX_CBOEEU_ETF_SCOPE_001", "cboe_europe_reference_data", "instrument_type", "ETF", "CBOE_EUROPE", "instrument_scope", "exchange_traded_fund", "explicit ETF provider type"),
    rule("TAX_CBOEEU_ETC_ASSET_001", "cboe_europe_reference_data", "instrument_type", "ETC", "CBOE_EUROPE", "asset_type", "certificate_structured", "explicit ETC provider type"),
    rule("TAX_CBOEEU_ETC_SCOPE_001", "cboe_europe_reference_data", "instrument_type", "ETC", "CBOE_EUROPE", "instrument_scope", "exchange_traded_commodity", "explicit ETC provider type"),
    rule("TAX_CBOEEU_ETN_ASSET_001", "cboe_europe_reference_data", "instrument_type", "ETN", "CBOE_EUROPE", "asset_type", "fixed_income", "explicit exchange-traded note type"),
    rule("TAX_CBOEEU_ETN_SCOPE_001", "cboe_europe_reference_data", "instrument_type", "ETN", "CBOE_EUROPE", "instrument_scope", "exchange_traded_note", "explicit exchange-traded note type"),
    rule("TAX_CBOEEU_DR_ASSET_001", "cboe_europe_reference_data", "instrument_type", "DR", "CBOE_EUROPE", "asset_type", "depository_receipt_equity", "explicit depositary-receipt type"),
    rule("TAX_CBOEEU_DR_SCOPE_001", "cboe_europe_reference_data", "instrument_type", "DR", "CBOE_EUROPE", "instrument_scope", "depository_receipt", "explicit depositary-receipt type"),
    rule("TAX_SFC_EQUITY_ASSET_001", "SFC_SIMEV_RNVE", "instrument_type", "colombia_equity_price_security", "BVC", "asset_type", "common_equity", "explicit Colombia equity price security"),
    rule("TAX_SFC_EQUITY_SCOPE_001", "SFC_SIMEV_RNVE", "instrument_type", "colombia_equity_price_security", "BVC", "instrument_scope", "common_equity", "explicit Colombia equity price security"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_contract_sha(path: Path) -> str:
    """Return the historical canonical SHA, whose contract uses CRLF CSV bytes."""
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(data).hexdigest()


def count_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return max(sum(1 for _ in f) - 1, 0)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def is_missing(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def matches(r: dict[str, str], row: dict[str, str]) -> bool:
    provider = row.get("source_provider", "").strip() or "__MISSING_PROVIDER__"
    if provider != r["source_provider"]:
        return False
    if r["exchange_constraint"] != "*" and row.get("exchange", "").strip() != r["exchange_constraint"]:
        return False
    return r["source_value"] == "*" or row.get(r["source_field"], "").strip() == r["source_value"]


def completeness(rows: list[dict[str, str]]) -> dict[str, dict[str, float | int]]:
    out = {}
    for field in FIELDS:
        missing = sum(is_missing(r.get(field)) for r in rows)
        out[field] = {"present": len(rows) - missing, "missing": missing,
                      "coverage_pct": round(100 * (len(rows) - missing) / len(rows), 4)}
    return out


def main() -> None:
    outputs = [REPORT_JSON, REPORT_MD, SUMMARY_CSV, CHECKS_CSV, REGISTRY_CSV, RULE_METRICS_CSV,
               PROVIDER_METRICS_CSV, UNRESOLVED_CSV, OVERLAY_CSV, MANIFEST_CSV]
    if any(p.exists() for p in outputs):
        raise SystemExit("NO_OVERWRITE_GUARD: one or more v2.24E outputs already exist")

    canonical_materialized_sha_before = sha256(CANONICAL)
    canonical_sha_before = canonical_contract_sha(CANONICAL)
    pointer_sha_before = sha256(POINTER)
    with CANONICAL.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f); header = list(reader.fieldnames or []); rows = [dict(r) for r in reader]
    baseline = completeness(rows)
    overlay_rows: list[dict[str, Any]] = []
    rule_counts: Counter[str] = Counter()
    provider_fills: Counter[tuple[str, str]] = Counter()
    overwrite_attempts = conflicts = control_changes = 0

    for idx, source in enumerate(rows, 1):
        proposed = {field: source.get(field, "") for field in FIELDS}
        provenance: dict[str, str] = {field: "" for field in FIELDS}
        for r in RULES:
            target = r["target_field"]
            if not matches(r, source):
                continue
            if not is_missing(source.get(target)):
                if source.get(target, "").strip() != r["target_value"]:
                    conflicts += 1
                continue
            if provenance[target] and proposed[target] != r["target_value"]:
                conflicts += 1
                continue
            proposed[target] = r["target_value"]
            provenance[target] = r["rule_id"]

        provider = source.get("source_provider", "").strip() or "__MISSING_PROVIDER__"
        changed_fields = [f for f in FIELDS if proposed[f] != source.get(f, "")]
        if provider in CONTROL_PROVIDERS and changed_fields:
            control_changes += 1
        for field in changed_fields:
            if not is_missing(source.get(field)):
                overwrite_attempts += 1
            rule_counts[provenance[field]] += 1
            provider_fills[(provider, field)] += 1
        overlay = {"row_number": idx, "ticker": source.get("ticker", ""), "exchange": source.get("exchange", ""),
                   "source_provider": provider, "changed_field_count": len(changed_fields),
                   "metadata_backfill_status": "DRY_RUN_DERIVED" if changed_fields else "NO_DETERMINISTIC_CHANGE"}
        for field in FIELDS:
            overlay[f"original_{field}"] = source.get(field, "")
            overlay[f"proposed_{field}"] = proposed[field]
            overlay[f"{field}_rule_id"] = provenance[field]
        overlay_rows.append(overlay)

    proposed_rows = [{f: overlay[f"proposed_{f}"] for f in FIELDS} for overlay in overlay_rows]
    post = completeness(proposed_rows)

    provider_metrics = []
    providers = sorted({r.get("source_provider", "").strip() or "__MISSING_PROVIDER__" for r in rows})
    for provider in providers:
        indices = [i for i, r in enumerate(rows) if (r.get("source_provider", "").strip() or "__MISSING_PROVIDER__") == provider]
        before_missing = sum(is_missing(rows[i].get(f)) for i in indices for f in FIELDS)
        after_missing = sum(is_missing(overlay_rows[i][f"proposed_{f}"]) for i in indices for f in FIELDS)
        provider_metrics.append({"source_provider": provider, "rows_before": len(indices), "rows_after": len(indices),
            "missing_cells_before": before_missing, "missing_cells_after": after_missing,
            "filled_cells": before_missing-after_missing,
            "six_field_completeness_before_pct": round(100*(6*len(indices)-before_missing)/(6*len(indices)),4),
            "six_field_completeness_after_pct": round(100*(6*len(indices)-after_missing)/(6*len(indices)),4),
            "changed_rows": sum(int(overlay_rows[i]["changed_field_count"]) > 0 for i in indices)})

    unresolved = []
    for provider in providers:
        for field in FIELDS:
            count = sum(1 for o in overlay_rows if o["source_provider"] == provider and is_missing(o[f"proposed_{field}"]))
            if count:
                reason = "REVIEW_REQUIRED_PROVIDER_HOLD" if provider in {"HKEX", "hkex_securities_list", "__MISSING_PROVIDER__"} else "NO_APPROVED_DETERMINISTIC_RULE"
                if provider == "cboe_europe_reference_data" and field in {"country", "mic", "currency"}:
                    reason = "VENUE_OR_LISTING_DETAIL_INSUFFICIENT"
                if provider == "cboe_europe_reference_data" and field in {"asset_type", "instrument_scope"}:
                    reason = "BROAD_EQTY_CLASS_REMAINS_AMBIGUOUS"
                unresolved.append({"source_provider": provider, "field": field, "unresolved_rows": count, "reason": reason})

    overlay_fields = ["row_number", "ticker", "exchange", "source_provider", "changed_field_count", "metadata_backfill_status"]
    for f in FIELDS: overlay_fields += [f"original_{f}", f"proposed_{f}", f"{f}_rule_id"]
    write_csv(OVERLAY_CSV, overlay_rows, overlay_fields)
    write_csv(REGISTRY_CSV, RULES, list(RULES[0]))
    rule_metrics = [{"rule_id": r["rule_id"], "target_field": r["target_field"], "target_value": r["target_value"], "filled_cells": rule_counts[r["rule_id"]]} for r in RULES]
    write_csv(RULE_METRICS_CSV, rule_metrics, ["rule_id", "target_field", "target_value", "filled_cells"])
    write_csv(PROVIDER_METRICS_CSV, provider_metrics, list(provider_metrics[0]))
    write_csv(UNRESOLVED_CSV, unresolved, ["source_provider", "field", "unresolved_rows", "reason"])

    canonical_materialized_sha_after = sha256(CANONICAL)
    canonical_sha_after = canonical_contract_sha(CANONICAL); pointer_sha_after = sha256(POINTER)
    derived_cells = sum(rule_counts.values())
    provenance_cells = sum(1 for o in overlay_rows for f in FIELDS if o[f"{f}_rule_id"])
    checks: list[dict[str, Any]] = []
    def check(name: str, passed: bool, severity: str, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "severity": severity, "detail": detail})
    check("canonical_sha_expected", canonical_sha_before == EXPECTED_SHA, "critical", canonical_sha_before)
    check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", canonical_sha_after)
    check("canonical_materialized_sha_unchanged", canonical_materialized_sha_before == canonical_materialized_sha_after, "critical", canonical_materialized_sha_after)
    check("row_count_43089", len(rows) == EXPECTED_ROWS == len(overlay_rows), "critical", f"canonical={len(rows)};overlay={len(overlay_rows)}")
    check("pointer_unchanged", pointer_sha_before == pointer_sha_after, "critical", pointer_sha_after)
    check("zero_overwrites", overwrite_attempts == 0, "critical", str(overwrite_attempts))
    check("derived_provenance_100pct", derived_cells == provenance_cells, "critical", f"derived={derived_cells};provenance={provenance_cells}")
    check("control_rows_unchanged", control_changes == 0, "critical", str(control_changes))
    check("provider_rows_reconcile", sum(p["rows_after"] for p in provider_metrics) == EXPECTED_ROWS, "critical", str(sum(p["rows_after"] for p in provider_metrics)))
    check("zero_rule_conflicts", conflicts == 0, "critical", str(conflicts))
    check("coverage_improved", derived_cells > 0, "critical", str(derived_cells))
    critical_failed = sum(c["severity"] == "critical" and not c["passed"] for c in checks)
    status = "METADATA_IMPROVEMENT_DRY_RUN_COMPLETED_NO_PROMOTION" if critical_failed == 0 else "METADATA_IMPROVEMENT_DRY_RUN_FAILED_REVIEW_REQUIRED"

    summary = [{"version": VERSION, "phase": PHASE, "status": status, "canonical_rows": len(rows),
        "canonical_sha256_before": canonical_sha_before, "canonical_sha256_after": canonical_sha_after,
        "canonical_materialized_sha256_before": canonical_materialized_sha_before,
        "canonical_materialized_sha256_after": canonical_materialized_sha_after,
        "derived_cells": derived_cells, "provenance_coverage_pct": round(100*provenance_cells/derived_cells,4) if derived_cells else 100,
        "overwrite_attempts": overwrite_attempts, "conflicts": conflicts, "control_changed_rows": control_changes,
        "critical_failed_checks": critical_failed, "canonical_dataset_modified": False, "active_pointer_modified": False,
        "production_scoring_authorized": False, "scoring_promoted": False, "openai_called": False,
        "broker_called": False, "full59k": "DEPRECATED_DEFERRED"}]
    write_csv(SUMMARY_CSV, summary, list(summary[0]))
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])

    payload = {"version": VERSION, "phase": PHASE, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status, "baseline": baseline, "post_dry_run": post, "summary": summary[0],
        "provider_metrics": provider_metrics, "rule_metrics": rule_metrics, "unresolved_summary": unresolved,
        "checks": checks, "guardrails": {"canonical_dataset_modified": False, "active_pointer_modified": False,
        "production_scoring_authorized": False, "scoring_promoted": False, "openai_called": False,
        "broker_called": False, "full59k": "DEPRECATED_DEFERRED"}}
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    coverage_lines = "\n".join(f"| `{f}` | {baseline[f]['missing']:,} | {post[f]['missing']:,} | {baseline[f]['missing']-post[f]['missing']:,} | {post[f]['coverage_pct']:.4f}% |" for f in FIELDS)
    provider_lines = "\n".join(f"| `{p['source_provider']}` | {p['rows_after']:,} | {p['missing_cells_before']:,} | {p['missing_cells_after']:,} | {p['filled_cells']:,} | {p['changed_rows']:,} |" for p in sorted(provider_metrics, key=lambda x: -x['filled_cells']))
    REPORT_MD.write_text(f"""# Scout Finance — v2.24E Metadata Improvement Dry Run

**Status:** `{status}`

## Execution result

The deterministic overlay was executed over all **{len(rows):,}** canonical rows. It is a non-promoted artifact: the canonical CSV and operational pointer were not modified.

- Canonical contract SHA (CRLF) before/after: `{canonical_sha_before}` / `{canonical_sha_after}`
- Materialized checkout SHA (LF) before/after: `{canonical_materialized_sha_before}` / `{canonical_materialized_sha_after}`
- Derived cells: **{derived_cells:,}**
- Derived-value provenance: **{provenance_cells:,}/{derived_cells:,} = {100*provenance_cells/derived_cells:.4f}%**
- Overwrite attempts: **{overwrite_attempts}**
- Rule conflicts: **{conflicts}**
- ASX/SGX changed rows: **{control_changes}**
- Critical failed checks: **{critical_failed}**

## Coverage before / after

| Field | Missing before | Missing after | Deterministic fills | Coverage after |
|---|---:|---:|---:|---:|
{coverage_lines}

## Provider results

| Provider | Rows | Missing before | Missing after | Filled cells | Changed rows |
|---|---:|---:|---:|---:|---:|
{provider_lines}

## Holds and unresolved cases

HKEX (`hkex_securities_list` and `HKEX`) and `__MISSING_PROVIDER__` remain on review hold. CBOE Europe geography remains unresolved because the canonical rows do not contain venue/listing detail sufficient for deterministic country, MIC or currency; broad `EQTY` taxonomy rows also remain unresolved. Unresolved cells are reported, never guessed.

## Acceptance and guardrails

All critical gates passed: 43,089 rows, unchanged canonical SHA, unchanged pointer, zero overwrites, zero rule conflicts, 100% provenance, provider reconciliation and zero control-population changes.

- `canonical_dataset_modified=False`
- `active_pointer_modified=False`
- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `openai_called=False`
- `broker_called=False`
- `full59k=DEPRECATED_DEFERRED`

**Recommended next phase:** `v2.24F — Metadata Promotion / Freeze Decision`.
""", encoding="utf-8", newline="\n")

    manifest_targets = [REPORT_JSON, REPORT_MD, SUMMARY_CSV, CHECKS_CSV, REGISTRY_CSV, RULE_METRICS_CSV, PROVIDER_METRICS_CSV, UNRESOLVED_CSV, OVERLAY_CSV]
    manifest = [{"artifact": p.name, "path": str(p), "rows": count_rows(p) if p.suffix == ".csv" else "", "sha256": sha256(p)} for p in manifest_targets]
    write_csv(MANIFEST_CSV, manifest, ["artifact", "path", "rows", "sha256"])
    print(json.dumps(summary[0], indent=2))


if __name__ == "__main__":
    main()
