#!/usr/bin/env python3
"""End-to-end analyst workflow QA for Scout Finance v2.27F."""
import importlib.util,json,tempfile
from pathlib import Path

def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 root=Path(__file__).resolve().parents[1]
 wb=module(root/"scripts/watchlist_builder_v2_27c.py","wb")
 se=module(root/"scripts/score_explorer_v2_27d.py","se")
 rg=module(root/"scripts/report_generator_v2_27e.py","rg")
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);catalog=d/"catalog.csv";watch=d/"watchlist.json";watch_csv=d/"watchlist.csv"
  scoring=d/"scoring.json";universe=d/"universe.json";explorer=d/"explorer.html";report=d/"watchlist_report.html";universe_report=d/"universe.md"
  catalog.write_text("identity_key,name,ticker,exchange,isin,country,currency,asset_type,source_provider\nqa:one,Asset One,ONE,XQ,QA0001,ES,EUR,equity,fixture\nqa:two,Asset Two,TWO,XQ,QA0002,FR,EUR,equity,fixture\n")
  scoring.write_text(json.dumps({"status":"NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED","active_scoring_available":False,"production_scoring_authorized":False,"scoring_promoted":False,"consumer_contract":{"allow_ranking":False}}))
  universe.write_text(json.dumps({"current_dataset_rows":43089,"current_dataset":"universe.csv","current_dataset_sha256":"a"*64,"quality_floor_target":42000,"quality_ceiling_target":45000,"remaining_capacity":1911}))
  data=wb.new_watchlist("Workflow QA","Integrated metadata workflow")
  wb.add_item(data,wb.resolve(wb.load_catalog(catalog),ticker="ONE",exchange="XQ"),"review,spain","Check later")
  wb.atomic_write(watch,data,backup=False);wb.export_csv(data,watch_csv)
  assert wb.read_watchlist(watch)["scoring_used"] is False
  assert se.main(["--pointer",str(scoring),"--output",str(explorer)])==0
  page=explorer.read_text();assert "FAIL-CLOSED" in page and "ranking" in page.lower()
  assert rg.main(["--type","watchlist","--watchlist",str(watch),"--scoring-pointer",str(scoring),"--format","html","--output",str(report)])==0
  assert rg.main(["--type","universe","--universe-pointer",str(universe),"--scoring-pointer",str(scoring),"--output",str(universe_report)])==0
  assert "Asset One" in report.read_text() and "43,089" in universe_report.read_text()
  assert report.with_suffix(".html.manifest.json").exists() and universe_report.with_suffix(".md.manifest.json").exists()
  exported=watch_csv.read_text(encoding="utf-8-sig")
  assert "score" not in exported.lower() and "rank" not in exported.lower()
 print("PASS: catalog-resolve/watchlist/export/locked-explorer/reports/manifests/no-score-leakage")
 return 0
if __name__=="__main__":raise SystemExit(main())
