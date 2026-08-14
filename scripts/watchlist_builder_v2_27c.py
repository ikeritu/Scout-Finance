#!/usr/bin/env python3
"""Scout Finance v2.27C watchlist builder. Metadata-only and scoring-independent."""
from __future__ import annotations
import argparse, csv, json, os, shutil, sys, tempfile, uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0"
FORBIDDEN_FIELDS = {"score","rank","recommendation","signal","target_price","allocation"}
ALIASES = {
    "identity_key": ("identity_key","stable_identity_key"),
    "isin": ("isin","ISIN"),
    "exchange": ("exchange","exchange_code","mic","MIC"),
    "ticker": ("ticker","symbol","Symbol"),
    "provider": ("source_provider","provider"),
    "instrument_id": ("instrument_id","id","security_id"),
    "name": ("name","instrument_name","company_name","description"),
    "country": ("country","country_code"),
    "currency": ("currency","currency_code"),
    "asset_type": ("asset_type","instrument_type"),
}

def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def clean(value) -> str:
    return str(value or "").strip()

def pick(row, key) -> str:
    for name in ALIASES[key]:
        if name in row and clean(row[name]):
            return clean(row[name])
    return ""

def identity(row) -> str:
    explicit = pick(row, "identity_key")
    if explicit:
        return explicit
    isin, exchange, ticker = pick(row,"isin"), pick(row,"exchange"), pick(row,"ticker")
    if isin and exchange and ticker:
        return f"isin:{isin.upper()}|exchange:{exchange.upper()}|ticker:{ticker.upper()}"
    provider, iid = pick(row,"provider"), pick(row,"instrument_id")
    symbol = ticker
    if provider and exchange and ticker and (iid or symbol):
        return f"provider:{provider.lower()}|exchange:{exchange.upper()}|ticker:{ticker.upper()}|instrument_id:{iid}|symbol:{symbol.upper()}"
    raise ValueError("row cannot form a stable identity")

def load_catalog(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def resolve(catalog, identity_key="", ticker="", exchange="", isin=""):
    if identity_key:
        matches=[r for r in catalog if identity(r)==identity_key]
    elif isin:
        matches=[r for r in catalog if pick(r,"isin").upper()==isin.upper() and (not exchange or pick(r,"exchange").upper()==exchange.upper())]
    elif ticker:
        matches=[r for r in catalog if pick(r,"ticker").upper()==ticker.upper() and (not exchange or pick(r,"exchange").upper()==exchange.upper())]
    else:
        raise ValueError("identity_key, ticker or ISIN is required")
    if not matches: raise ValueError("asset not found in catalog")
    if len(matches)>1: raise ValueError("asset is ambiguous; provide exchange or identity_key")
    return matches[0]

def snapshot(row):
    return {
        "identity_key": identity(row), "name": pick(row,"name"), "ticker": pick(row,"ticker"),
        "exchange": pick(row,"exchange"), "isin": pick(row,"isin"), "country": pick(row,"country"),
        "currency": pick(row,"currency"), "asset_type": pick(row,"asset_type"),
        "source_provider": pick(row,"provider"),
    }

def new_watchlist(name, description=""):
    ts=now()
    return {"schema_version":SCHEMA_VERSION,"watchlist_id":str(uuid.uuid4()),"name":name.strip(),
            "description":description.strip(),"created_at_utc":ts,"updated_at_utc":ts,
            "consumer_state":"CATALOG_AVAILABLE","scoring_used":False,"items":[]}

def read_watchlist(path: Path):
    data=json.loads(path.read_text(encoding="utf-8"))
    validate_data(data)
    return data

def validate_data(data):
    errors=[]
    for field in ("schema_version","watchlist_id","name","consumer_state","scoring_used","items"):
        if field not in data: errors.append(f"missing {field}")
    if data.get("scoring_used") is not False: errors.append("scoring_used must be false")
    if data.get("consumer_state")!="CATALOG_AVAILABLE": errors.append("consumer_state must be CATALOG_AVAILABLE")
    seen=set()
    for i,item in enumerate(data.get("items",[]),1):
        key=clean(item.get("identity_key"))
        if not key: errors.append(f"item {i}: missing identity_key")
        if key in seen: errors.append(f"item {i}: duplicate identity_key")
        seen.add(key)
        if FORBIDDEN_FIELDS.intersection(item): errors.append(f"item {i}: forbidden scoring field")
    if errors: raise ValueError("; ".join(errors))
    return True

def atomic_write(path: Path, data, backup=True):
    path.parent.mkdir(parents=True,exist_ok=True)
    if backup and path.exists(): shutil.copy2(path,path.with_suffix(path.suffix+".bak"))
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as f:
            json.dump(data,f,ensure_ascii=False,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def add_item(data,row,tags="",note=""):
    snap=snapshot(row);key=snap["identity_key"]
    if any(x["identity_key"]==key for x in data["items"]): raise ValueError("asset already exists in watchlist")
    snap.update({"tags":sorted({x.strip() for x in tags.split(",") if x.strip()}),"note":note.strip(),"added_at_utc":now(),"status":"active"})
    data["items"].append(snap);data["updated_at_utc"]=now();validate_data(data)

def remove_item(data,key):
    before=len(data["items"]);data["items"]=[x for x in data["items"] if x["identity_key"]!=key]
    if len(data["items"])==before: raise ValueError("asset not found in watchlist")
    data["updated_at_utc"]=now()

def safe_csv(value):
    s=clean(value)
    return "'"+s if s.startswith(("=","+","-","@")) else s

def export_csv(data,path: Path):
    fields=["identity_key","name","ticker","exchange","isin","country","currency","asset_type","source_provider","tags","note","added_at_utc","status"]
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        for item in data["items"]:
            row=dict(item);row["tags"]=",".join(item.get("tags",[]));w.writerow({k:safe_csv(row.get(k,"")) for k in fields})

def main(argv=None):
    ap=argparse.ArgumentParser(description="Build metadata-only Scout Finance watchlists")
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("init");p.add_argument("watchlist",type=Path);p.add_argument("--name",required=True);p.add_argument("--description",default="")
    for cmd in ("add","import"):
        p=sub.add_parser(cmd);p.add_argument("watchlist",type=Path);p.add_argument("--catalog",type=Path,required=True)
        if cmd=="add":
            p.add_argument("--identity",default="");p.add_argument("--ticker",default="");p.add_argument("--exchange",default="");p.add_argument("--isin",default="");p.add_argument("--tags",default="");p.add_argument("--note",default="")
        else:p.add_argument("--input",type=Path,required=True)
    p=sub.add_parser("remove");p.add_argument("watchlist",type=Path);p.add_argument("--identity",required=True)
    p=sub.add_parser("list");p.add_argument("watchlist",type=Path)
    p=sub.add_parser("validate");p.add_argument("watchlist",type=Path);p.add_argument("--catalog",type=Path)
    p=sub.add_parser("export");p.add_argument("watchlist",type=Path);p.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(argv)
    try:
        if a.cmd=="init": atomic_write(a.watchlist,new_watchlist(a.name,a.description),backup=False);print(f"created {a.watchlist}");return 0
        data=read_watchlist(a.watchlist)
        if a.cmd=="add":
            add_item(data,resolve(load_catalog(a.catalog),a.identity,a.ticker,a.exchange,a.isin),a.tags,a.note);atomic_write(a.watchlist,data);print("added");return 0
        if a.cmd=="import":
            catalog=load_catalog(a.catalog);added=skipped=0
            with a.input.open("r",encoding="utf-8-sig",newline="") as f:
                for row in csv.DictReader(f):
                    try:add_item(data,resolve(catalog,clean(row.get("identity_key")),clean(row.get("ticker")),clean(row.get("exchange")),clean(row.get("isin"))),clean(row.get("tags")),clean(row.get("note")));added+=1
                    except ValueError:skipped+=1
            atomic_write(a.watchlist,data);print(f"added={added} skipped={skipped}");return 0
        if a.cmd=="remove": remove_item(data,a.identity);atomic_write(a.watchlist,data);print("removed");return 0
        if a.cmd=="list":
            for x in data["items"]: print(f'{x["ticker"]}\t{x["exchange"]}\t{x["name"]}\t{x["identity_key"]}')
            return 0
        if a.cmd=="validate":
            if a.catalog:
                keys={identity(r) for r in load_catalog(a.catalog)}
                missing=[x["identity_key"] for x in data["items"] if x["identity_key"] not in keys]
                if missing: raise ValueError(f"{len(missing)} identities absent from catalog")
            print(f'PASS items={len(data["items"])} unique={len({x["identity_key"] for x in data["items"]})} scoring_used=false');return 0
        if a.cmd=="export": export_csv(data,a.output);print(f"exported {len(data['items'])} items");return 0
    except (OSError,ValueError,json.JSONDecodeError) as e:
        print(f"ERROR: {e}",file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
