"""Metadata-only catalog services for the v2.28 UI."""
from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ALIASES={
 "identity_key":("identity_key","stable_identity_key"),
 "name":("name","instrument_name","company_name","description","security_name"),
 "ticker":("ticker","symbol","Symbol"),
 "isin":("isin","ISIN"),
 "exchange":("exchange","exchange_code","mic","MIC"),
 "country":("country","country_code"),
 "currency":("currency","currency_code"),
 "asset_type":("asset_type","instrument_type","type"),
 "provider":("source_provider","provider"),
 "instrument_id":("instrument_id","security_id","id"),
}
FORBIDDEN_OUTPUT_TOKENS=("score","rank","recommendation","signal","target_price","allocation")
DISPLAY_FIELDS=("identity_key","name","ticker","exchange","isin","country","currency","asset_type","provider")

def clean(value)->str:return str(value or "").strip()

def pick(row:Mapping,key:str)->str:
 for name in ALIASES[key]:
  value=clean(row.get(name))
  if value:return value
 return ""

def stable_identity(row:Mapping)->str:
 explicit=pick(row,"identity_key")
 if explicit:return explicit
 isin,exchange,ticker=pick(row,"isin"),pick(row,"exchange"),pick(row,"ticker")
 if isin and exchange and ticker:return f"isin:{isin.upper()}|exchange:{exchange.upper()}|ticker:{ticker.upper()}"
 provider,iid=pick(row,"provider"),pick(row,"instrument_id")
 if provider and exchange and ticker:
  return f"provider:{provider.lower()}|exchange:{exchange.upper()}|ticker:{ticker.upper()}|instrument_id:{iid}|symbol:{ticker.upper()}"
 raise ValueError("row cannot form a stable identity")

def normalized_asset(row:Mapping)->dict:
 asset={key:pick(row,key) for key in DISPLAY_FIELDS if key!="identity_key"}
 asset["identity_key"]=stable_identity(row)
 return {key:asset.get(key,"") or "Unknown" for key in DISPLAY_FIELDS}

def load_catalog(path:Path)->list[dict]:
 with path.open("r",encoding="utf-8-sig",newline="") as handle:
  return [normalized_asset(row) for row in csv.DictReader(handle)]

def distinct_values(rows:Iterable[Mapping],field:str)->list[str]:
 values={clean(row.get(field)) or "Unknown" for row in rows}
 return sorted(values,key=lambda value:(value=="Unknown",value.casefold()))

@dataclass(frozen=True)
class CatalogPage:
 rows:tuple[dict,...];total:int;page:int;page_size:int;pages:int

def query_catalog(rows:Sequence[Mapping],search="",filters=None,page=1,page_size=50)->CatalogPage:
 filters=filters or {};needle=clean(search).casefold();selected=[]
 for source in rows:
  row={key:clean(source.get(key)) or "Unknown" for key in DISPLAY_FIELDS}
  if needle and not any(needle in row[key].casefold() for key in ("name","ticker","isin","identity_key")):continue
  if any(values and row.get(field,"Unknown") not in set(values) for field,values in filters.items()):continue
  selected.append(row)
 page_size=max(1,min(int(page_size),250));pages=max(1,(len(selected)+page_size-1)//page_size);page=max(1,min(int(page),pages))
 start=(page-1)*page_size
 return CatalogPage(tuple(selected[start:start+page_size]),len(selected),page,page_size,pages)

def asset_by_identity(rows:Iterable[Mapping],identity_key:str):
 matches=[dict(row) for row in rows if clean(row.get("identity_key"))==clean(identity_key)]
 if len(matches)!=1:raise ValueError("asset identity is missing or ambiguous")
 return matches[0]

def assert_metadata_only(rows:Iterable[Mapping]):
 for row in rows:
  for field in row:
   if any(token in field.casefold() for token in FORBIDDEN_OUTPUT_TOKENS):
    raise ValueError(f"forbidden scoring field: {field}")
 return True
