#!/usr/bin/env python3
"""Offline QA for the v2.38AX Luxembourg fundamentals extractor. No real
network calls and no real Centrale des Bilans data -- builds small
synthetic XML fixtures shaped exactly like the real schema (confirmed live
via a byte-range sample of the real 2026 Q1 file, quoted in the script's
own docstring), and parses them with the standard library's own
ElementTree, the same code path used on the real files.
"""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/fetch_europe_luxembourg_fundamentals_v2_38ax.py"


def module():
    spec = importlib.util.spec_from_file_location("fetch_europe_luxembourg_fundamentals_v2_38ax", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_rcs_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "isin", "gleif_lookup_status", "rcs_number"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rcs_row(asset_id: str, ticker: str, rcs: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "isin": "LU0000000000", "gleif_lookup_status": "resolved", "rcs_number": rcs}


QUARTER_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<STATECCDBDeclarations>
  <Declarations STATECPublicationDate="2026-01-01">
{declarers}
  </Declarations>
</STATECCDBDeclarations>
"""

FULL_DECLARER_TEMPLATE = """
    <Declarer>
      <RcsNumber>{rcs}</RcsNumber>
      <LegalUnitName>{name}</LegalUnitName>
      <Declaration language="FR" model="1" type="CA_BILAN">
        <StartDate>{start}</StartDate>
        <EndDate>{end}</EndDate>
        <YearRef>{year}</YearRef>
        <FormData>
          <Field dataType="DECIMAL" ecdf="201" id="0_Actif_2010">
            <Label>TOTAL DU BILAN (ACTIF)</Label>
            <Data>{total_assets}</Data>
            <PreviousData>0</PreviousData>
          </Field>
          <Field dataType="DECIMAL" ecdf="301" id="0_CapPropres_2010">
            <Label>Capitaux propres</Label>
            <Data>{equity}</Data>
            <PreviousData>0</PreviousData>
          </Field>
        </FormData>
      </Declaration>
      <Declaration language="FR" model="1" type="CA_COMPP">
        <StartDate>{start}</StartDate>
        <EndDate>{end}</EndDate>
        <YearRef>{year}</YearRef>
        <FormData>
          <Field dataType="DECIMAL" ecdf="701" id="0_CA_2010">
            <Label>Montant net du chiffre d'affaires</Label>
            <Data>{revenue}</Data>
            <PreviousData>0</PreviousData>
          </Field>
          <Field dataType="DECIMAL" ecdf="799" id="0_Resultat_2010">
            <Label>Resultat de l'exercice</Label>
            <Data>{net_profit}</Data>
            <PreviousData>0</PreviousData>
          </Field>
        </FormData>
      </Declaration>
    </Declarer>
"""

CONFIDENTIAL_PL_DECLARER_TEMPLATE = """
    <Declarer>
      <RcsNumber>{rcs}</RcsNumber>
      <LegalUnitName>{name}</LegalUnitName>
      <Declaration language="FR" model="1" type="CA_BILAN">
        <StartDate>{start}</StartDate>
        <EndDate>{end}</EndDate>
        <YearRef>{year}</YearRef>
        <FormData>
          <Field dataType="DECIMAL" ecdf="201" id="0_Actif_2010">
            <Label>TOTAL DU BILAN (ACTIF)</Label>
            <Data>{total_assets}</Data>
            <PreviousData>0</PreviousData>
          </Field>
        </FormData>
      </Declaration>
    </Declarer>
"""


def write_quarter_file(path: Path, declarer_xml_blocks: list[str]) -> None:
    path.write_text(QUARTER_XML_TEMPLATE.format(declarers="".join(declarer_xml_blocks)), encoding="utf-8")


def test_full_declarer_extracts_all_four_tracked_concepts():
    mod = module()
    xml = FULL_DECLARER_TEMPLATE.format(rcs="B82454", name="ArcelorMittal", start="2025-01-01", end="2025-12-31", year="2025", total_assets="99999999.00", equity="55555555.00", revenue="12345678.00", net_profit="1000000.00")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        qfile = root / "deposit-2026q1.xml"
        write_quarter_file(qfile, [xml])
        found = mod.scan_quarter_file(qfile, {"B82454"}, "2026q1")
    assert "B82454" in found
    rec = found["B82454"]
    assert rec["legal_unit_name"] == "ArcelorMittal"
    assert rec["concepts"]["total_assets"]["value"] == "99999999.00"
    assert rec["concepts"]["equity"]["value"] == "55555555.00"
    assert rec["concepts"]["revenue"]["value"] == "12345678.00"
    assert rec["concepts"]["net_profit"]["value"] == "1000000.00"
    assert rec["balance_sheet_disclosed"] is True
    assert rec["profit_loss_disclosed"] is True


def test_confidential_profit_and_loss_is_missing_never_zero():
    """Real dataset behavior: a company that ticked "P&L confidential" at
    filing time simply has no CA_COMPP/CA_COMPPABR declaration in the
    public file at all -- this must surface as
    profit_loss_disclosed=False and no revenue/net_profit concept, never
    as a fabricated 0."""
    mod = module()
    xml = CONFIDENTIAL_PL_DECLARER_TEMPLATE.format(rcs="B999999", name="Private Holding SA", start="2025-01-01", end="2025-12-31", year="2025", total_assets="500000.00")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        qfile = root / "deposit-2026q1.xml"
        write_quarter_file(qfile, [xml])
        found = mod.scan_quarter_file(qfile, {"B999999"}, "2026q1")
    rec = found["B999999"]
    assert rec["balance_sheet_disclosed"] is True
    assert rec["profit_loss_disclosed"] is False
    assert "revenue" not in rec["concepts"]
    assert "net_profit" not in rec["concepts"]
    assert "total_assets" in rec["concepts"]


def test_untargeted_rcs_numbers_are_skipped_and_never_extracted():
    mod = module()
    xml = FULL_DECLARER_TEMPLATE.format(rcs="B111111", name="Not Our Company", start="2025-01-01", end="2025-12-31", year="2025", total_assets="1", equity="1", revenue="1", net_profit="1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        qfile = root / "deposit-2026q1.xml"
        write_quarter_file(qfile, [xml])
        found = mod.scan_quarter_file(qfile, {"B82454"}, "2026q1")
    assert found == {}


def test_build_stops_scanning_older_quarters_once_all_targets_found():
    """The whole point of newest-first scanning: once every target RCS is
    found in the newest quarter, older (larger, in this dataset's real
    case) quarter files must never even be downloaded."""
    mod = module()
    calls = []

    def fake_download(url, dest):
        calls.append(dest.name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        xml = FULL_DECLARER_TEMPLATE.format(rcs="B82454", name="ArcelorMittal", start="2025-01-01", end="2025-12-31", year="2025", total_assets="1", equity="1", revenue="1", net_profit="1")
        write_quarter_file(dest, [xml])

    mod.download_quarter = fake_download
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "rcs.csv"
        write_rcs_matrix(matrix, [rcs_row("U1", "ARRD", "B82454")])
        quarters = [("2026q2", "http://example.invalid/q2.xml"), ("2026q1", "http://example.invalid/q1.xml"), ("2025q4", "http://example.invalid/q4.xml")]
        report = mod.build(matrix, root / "out", root / "cache", quarters, execute=True)
    assert calls == ["deposit-2026q2.xml"]
    assert report["found"] == 1


def test_dry_run_never_touches_network():
    mod = module()
    calls = []
    mod.download_quarter = lambda url, dest: calls.append(dest)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "rcs.csv"
        write_rcs_matrix(matrix, [rcs_row("U1", "ARRD", "B82454")])
        report = mod.build(matrix, root / "out", root / "cache", [("2026q2", "http://example.invalid/q2.xml")], execute=False)
    assert report["status"] == "DRY_RUN"
    assert calls == []


def test_resumable_skips_download_if_quarter_file_already_cached():
    """Real download_quarter, called directly (not via build) with a
    deliberately unreachable URL: if the destination already exists, it
    must return without ever attempting the network call -- if it tried,
    this would raise a urllib error and fail the test."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cached = root / "deposit-2026q2.xml"
        write_quarter_file(cached, [FULL_DECLARER_TEMPLATE.format(rcs="B82454", name="ArcelorMittal", start="2025-01-01", end="2025-12-31", year="2025", total_assets="1", equity="1", revenue="1", net_profit="1")])
        original_mtime = cached.stat().st_mtime
        mod.download_quarter("http://example.invalid/should-never-be-fetched.xml", cached)
        assert cached.stat().st_mtime == original_mtime


CASES = [
    test_full_declarer_extracts_all_four_tracked_concepts,
    test_confidential_profit_and_loss_is_missing_never_zero,
    test_untargeted_rcs_numbers_are_skipped_and_never_extracted,
    test_build_stops_scanning_older_quarters_once_all_targets_found,
    test_dry_run_never_touches_network,
    test_resumable_skips_download_if_quarter_file_already_cached,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AX-europe-luxembourg-fundamentals/concept-extraction/confidential-omission/target-filter/stop-early/dry-run/resumable/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
