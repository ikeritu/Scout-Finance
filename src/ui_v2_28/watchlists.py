"""Safe local watchlist persistence for the v2.28 UI."""
from __future__ import annotations
import csv,io,json,os,shutil,tempfile,uuid
from datetime import datetime,timezone
from pathlib import Path
from .catalog import DISPLAY_FIELDS,clean

SCHEMA_VERSION="1.0"
FORBIDDEN_FIELDS={"score","rank","recommendation","signal","target_price","allocation"}

def now():return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def slug(value):
 safe="".join(c.lower() if c.isalnum() else "-" for c in clean(value)).strip("-")
 return "-".join(filter(None,safe.split("-")))[:60] or "watchlist"
def watchlist_dir(root:Path)->Path:return root.resolve()/"data"/"watchlists"
def watchlist_path(root:Path,name:str)->Path:return watchlist_dir(root)/(slug(name)+".json")

def new_watchlist(name,description=""):
 if not clean(name):raise ValueError("watchlist name is required")
 ts=now();return {"schema_version":SCHEMA_VERSION,"watchlist_id":str(uuid.uuid4()),"name":clean(name),"description":clean(description),"created_at_utc":ts,"updated_at_utc":ts,"consumer_state":"CATALOG_AVAILABLE","scoring_used":False,"items":[]}

def validate(data):
 required={"schema_version","watchlist_id","name","consumer_state","scoring_used","items"};errors=[]
 if required-set(data):errors.append("missing required fields")
 if data.get("schema_version")!=SCHEMA_VERSION:errors.append("unsupported schema")
 if data.get("consumer_state")!="CATALOG_AVAILABLE" or data.get("scoring_used") is not False:errors.append("scoring contract violation")
 seen=set()
 for item in data.get("items",[]):
  key=clean(item.get("identity_key"))
  if not key or key in seen:errors.append("missing or duplicate identity")
  seen.add(key)
  if FORBIDDEN_FIELDS.intersection(item):errors.append("forbidden scoring field")
 if errors:raise ValueError("; ".join(errors))
 return True

def atomic_write(path:Path,data):
 validate(data);path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():shutil.copy2(path,path.with_suffix(".json.bak"))
 fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as handle:
   json.dump(data,handle,ensure_ascii=False,indent=2);handle.write("\n");handle.flush();os.fsync(handle.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)

def read(path:Path):
 data=json.loads(path.read_text(encoding="utf-8"));validate(data);return data
def list_watchlists(root:Path):
 folder=watchlist_dir(root)
 return [(path,read(path)) for path in sorted(folder.glob("*.json"))] if folder.exists() else []
def create(root:Path,name,description=""):
 path=watchlist_path(root,name)
 if path.exists():raise ValueError("watchlist already exists")
 data=new_watchlist(name,description);atomic_write(path,data);return path,data
def update_metadata(path:Path,data,name,description=""):
 data["name"]=clean(name);data["description"]=clean(description);data["updated_at_utc"]=now();atomic_write(path,data)
def add(data,asset,tags="",note=""):
 key=clean(asset.get("identity_key"))
 if not key:raise ValueError("asset identity is required")
 if any(item["identity_key"]==key for item in data["items"]):raise ValueError("asset already exists in watchlist")
 item={field:clean(asset.get(field)) or "Unknown" for field in DISPLAY_FIELDS}
 item.update({"tags":sorted({x.strip() for x in clean(tags).split(",") if x.strip()}),"note":clean(note),"added_at_utc":now(),"status":"active"})
 data["items"].append(item);data["updated_at_utc"]=now();validate(data)
def remove(data,identity_key):
 before=len(data["items"]);data["items"]=[x for x in data["items"] if x["identity_key"]!=identity_key]
 if len(data["items"])==before:raise ValueError("asset not found in watchlist")
 data["updated_at_utc"]=now()
def update_item(data,identity_key,tags="",note=""):
 item=next((x for x in data["items"] if x["identity_key"]==identity_key),None)
 if not item:raise ValueError("asset not found in watchlist")
 item["tags"]=sorted({x.strip() for x in clean(tags).split(",") if x.strip()});item["note"]=clean(note);data["updated_at_utc"]=now()
def export_csv_bytes(data):
 fields=list(DISPLAY_FIELDS)+["tags","note","added_at_utc","status"];out=io.StringIO(newline="")
 writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
 for item in data["items"]:
  row=dict(item);row["tags"]=",".join(row.get("tags",[]))
  for key,value in row.items():
   if isinstance(value,str) and value.startswith(("=","+","-","@")):row[key]="'"+value
  writer.writerow({key:row.get(key,"") for key in fields})
 return ("\ufeff"+out.getvalue()).encode("utf-8")
