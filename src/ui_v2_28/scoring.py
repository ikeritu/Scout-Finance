"""Fail-closed scoring summaries for the local UI."""
from __future__ import annotations
import csv,json
from collections import Counter,defaultdict
from pathlib import Path
from .paths import safe_repo_path,sha256

COMPONENTS=("data_quality_score","scope_confidence_score","provider_quality_score","attractiveness_score")
FORBIDDEN_FIELDS={"dry_run_rank","legacy_v2_22d_score"}

def diagnostic_contract(root:Path,pointer_rel="outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json"):
 pointer=safe_repo_path(root,pointer_rel);data=json.loads(pointer.read_text(encoding="utf-8"));diag=data.get("diagnostic_artifact") or {}
 valid=diag.get("role")=="DATA_READINESS_ONLY" and diag.get("production_eligible") is False and data.get("consumer_contract",{}).get("allow_ranking") is False
 return {"available":valid,"path":diag.get("path"),"sha256":diag.get("sha256"),"rows":int(diag.get("rows",0)),"role":diag.get("role"),"status":data.get("status")}

def load_diagnostic(root:Path,acknowledged:bool):
 if acknowledged is not True:raise PermissionError("diagnostic acknowledgement required")
 contract=diagnostic_contract(root)
 if not contract["available"]:raise ValueError("diagnostic contract invalid")
 path=safe_repo_path(root,contract["path"])
 if not path.is_file() or sha256(path)!=contract["sha256"]:raise ValueError("diagnostic artifact SHA-256 mismatch")
 total=0;buckets=Counter();providers=Counter();countries=Counter();sums=defaultdict(float);coverage=Counter();auth=set()
 with path.open("r",encoding="utf-8-sig",newline="") as handle:
  reader=csv.DictReader(handle)
  if FORBIDDEN_FIELDS.intersection(reader.fieldnames or ()):pass
  for row in reader:
   total+=1;buckets[row.get("score_bucket") or "Unknown"]+=1;providers[row.get("source_provider") or "Unknown"]+=1;countries[row.get("country") or "Unknown"]+=1;auth.add(row.get("production_scoring_authorized",""))
   for field in COMPONENTS:
    try:sums[field]+=float(row.get(field,""));coverage[field]+=1
    except (TypeError,ValueError):pass
 if total!=contract["rows"]:raise ValueError("diagnostic row count mismatch")
 if any(value not in ("False","false","0") for value in auth):raise ValueError("diagnostic claims production authorization")
 return {"rows":total,"role":"DATA_READINESS_ONLY","production_eligible":False,"allow_ranking":False,"component_means":{field:(sums[field]/coverage[field] if coverage[field] else None) for field in COMPONENTS},"component_coverage":dict(coverage),"buckets":dict(buckets.most_common()),"providers":dict(providers.most_common()),"countries":dict(countries.most_common())}

def distribution_rows(values,total,limit=15):
 return [{"label":key,"count":count,"percent":round(100*count/total,2) if total else 0} for key,count in list(values.items())[:limit]]
