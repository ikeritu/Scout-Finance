#!/usr/bin/env python3
import csv,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ui_v2_28.catalog import assert_metadata_only,asset_by_identity,distinct_values,load_catalog,query_catalog
from src.ui_v2_28.watchlists import add,atomic_write,create,export_csv_bytes,list_watchlists,read,remove,update_item
def main():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);catalog=root/"catalog.csv"
  with catalog.open("w",encoding="utf-8",newline="") as handle:
   writer=csv.DictWriter(handle,fieldnames=["name","ticker","exchange","isin","country","currency","asset_type","source_provider"]);writer.writeheader();writer.writerows([{"name":"Alpha SA","ticker":"ALP","exchange":"XMAD","isin":"ES0001","country":"ES","currency":"EUR","asset_type":"Equity","source_provider":"p1"},{"name":"Beta Inc","ticker":"BET","exchange":"XNYS","isin":"US0002","country":"US","currency":"USD","asset_type":"Equity","source_provider":"p2"},{"name":"Unknown Fund","ticker":"UF","exchange":"XLON","isin":"GB0003","country":"","currency":"GBP","asset_type":"Fund","source_provider":"p2"}])
  rows=load_catalog(catalog);assert len(rows)==3 and assert_metadata_only(rows);assert "Unknown" in distinct_values(rows,"country")
  result=query_catalog(rows,"alp",{"currency":["EUR"]},1,25);assert result.total==1 and result.rows[0]["ticker"]=="ALP"
  pages=query_catalog(rows,page=2,page_size=2);assert pages.total==3 and pages.page==2 and len(pages.rows)==1
  key=rows[0]["identity_key"];assert asset_by_identity(rows,key)["isin"]=="ES0001"
  path,data=create(root,"Core","Metadata only");add(data,rows[0],"core,es","review");atomic_write(path,data);persisted=read(path);assert len(persisted["items"])==1 and persisted["scoring_used"] is False
  try:add(persisted,rows[0])
  except ValueError:pass
  else:raise AssertionError("duplicate accepted")
  update_item(persisted,key,"updated","note");atomic_write(path,persisted);exported=export_csv_bytes(persisted).decode("utf-8-sig");assert "score" not in exported.lower() and "identity_key" in exported
  remove(persisted,key);atomic_write(path,persisted);assert not read(path)["items"] and len(list_watchlists(root))==1
 print("PASS: catalog/search/filters/unknown/pagination/identity/watchlist/dedupe/export/fail-closed");return 0
if __name__=="__main__":raise SystemExit(main())
