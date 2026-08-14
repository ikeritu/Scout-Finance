#!/usr/bin/env python3
"""Scout Finance v2.27E fail-closed Markdown/HTML report generator."""
from __future__ import annotations
import argparse,csv,hashlib,html,json,re,sys
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

FORBIDDEN_ITEM_FIELDS={"score","rank","recommendation","signal","target_price","allocation"}

def now():return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def digest(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def load(path):return json.loads(path.read_text(encoding="utf-8"))
def esc(v):return str(v or "").replace("|","\\|").replace("\n"," ")
def active_scoring(p):
 c=p.get("consumer_contract",{})
 return all([p.get("active_scoring_available") is True,p.get("production_scoring_authorized") is True,p.get("scoring_promoted") is True,c.get("allow_ranking") is True,bool(p.get("active_scoring_artifact")),bool(p.get("active_scoring_sha256"))])

def universe_report(up,sp):
 status="AUTHORIZED PRODUCTION" if active_scoring(sp) else "SCORING UNAVAILABLE · FAIL-CLOSED"
 return f"""# Scout Finance — Universe status report

**Generated:** {now()}  
**Consumer state:** CATALOG_AVAILABLE  
**Scoring:** {status}

## Operational universe

- Rows: **{up.get("current_dataset_rows",0):,}**
- Dataset: `{esc(up.get("current_dataset"))}`
- Dataset SHA-256: `{esc(up.get("current_dataset_sha256"))}`
- Quality band: {up.get("quality_floor_target","?"):,}–{up.get("quality_ceiling_target","?"):,}
- Remaining capacity: {up.get("remaining_capacity","?")}

## Safety state

{"The promoted scoring contract is active." if active_scoring(sp) else "No production score, ranking, recommendation or signal is available. Catalog exploration and watchlists remain usable."}

_Informational system report. No investment recommendation or broker action._
"""

def validate_watchlist(w):
 if w.get("scoring_used") is not False:raise ValueError("watchlist scoring_used must be false")
 if w.get("consumer_state")!="CATALOG_AVAILABLE":raise ValueError("watchlist consumer state invalid")
 seen=set()
 for x in w.get("items",[]):
  if FORBIDDEN_ITEM_FIELDS.intersection(x):raise ValueError("watchlist contains forbidden scoring field")
  k=x.get("identity_key")
  if not k or k in seen:raise ValueError("missing or duplicate watchlist identity")
  seen.add(k)

def watchlist_report(w,sp):
 validate_watchlist(w);rows=[]
 for x in w.get("items",[]):
  rows.append(f'| {esc(x.get("ticker"))} | {esc(x.get("exchange"))} | {esc(x.get("name"))} | {esc(", ".join(x.get("tags",[])))} | {esc(x.get("note"))} |')
 table="\n".join(rows) if rows else "| — | — | Empty watchlist | — | — |"
 return f"""# Scout Finance — Watchlist report

**Generated:** {now()}  
**Watchlist:** {esc(w.get("name"))}  
**Items:** {len(w.get("items",[]))}  
**Consumer state:** CATALOG_AVAILABLE  
**Scoring:** {"AUTHORIZED PRODUCTION" if active_scoring(sp) else "UNAVAILABLE · NOT USED"}

| Ticker | Exchange | Name | Tags | Note |
|---|---|---|---|---|
{table}

Scores, ranks, recommendations and signals are intentionally excluded.

_Informational watchlist. No investment recommendation or broker action._
"""

def diagnostic_summary(path):
 total=0;buckets=Counter();sums=defaultdict(float);counts=Counter();auth=set();promo=set()
 components=("data_quality_score","scope_confidence_score","provider_quality_score","attractiveness_score")
 with path.open("r",encoding="utf-8-sig",newline="") as f:
  for row in csv.DictReader(f):
   total+=1;buckets[row.get("score_bucket") or "UNKNOWN"]+=1;auth.add(row.get("production_scoring_authorized",""));promo.add(row.get("promotion_status",""))
   for k in components:
    try:sums[k]+=float(row.get(k,""));counts[k]+=1
    except (TypeError,ValueError):pass
 return total,buckets,{k:(sums[k]/counts[k] if counts[k] else None) for k in components},auth,promo

def diagnostic_report(sp,scores):
 d=sp.get("diagnostic_artifact") or {}
 if d.get("role")!="DATA_READINESS_ONLY" or d.get("production_eligible") is not False:raise ValueError("diagnostic contract invalid")
 if digest(scores)!=d.get("sha256"):raise ValueError("diagnostic SHA-256 mismatch")
 total,buckets,means,auth,promo=diagnostic_summary(scores)
 if total!=d.get("rows"):raise ValueError("diagnostic row count mismatch")
 if any(x not in ("False","false","0") for x in auth):raise ValueError("diagnostic claims production authorization")
 bucket_lines="\n".join(f"- {esc(k)}: {v:,} ({100*v/total:.1f}%)" for k,v in buckets.most_common())
 component_lines="\n".join(f'- {k.replace("_"," ").title()}: **{("N/A" if v is None else f"{v:.1f}")}**' for k,v in means.items())
 return f"""# Scout Finance — Data-readiness diagnostic

**Generated:** {now()}  
**Role:** DATA_READINESS_ONLY  
**Rows:** {total:,} / 43,089  
**Production authorized:** No  
**Promotion:** {esc(", ".join(sorted(promo)))}

## Component means

{component_lines}

## Diagnostic buckets

{bucket_lines}

This diagnostic measures data readiness and coverage. The source `dry_run_rank` is ignored and no assets are ordered or selected.

_Not investment analysis. No recommendation, signal, allocation or broker action._
"""

def markdown_to_html(md):
 lines=md.splitlines();out=[];in_list=False;in_table=False
 for line in lines:
  if line.startswith("|"):
   cells=[html.escape(x.strip()) for x in line.strip("|").split("|")]
   if all(re.fullmatch(r"-+",x.replace(":","")) for x in cells):continue
   if not in_table:out.append("<table>");in_table=True
   out.append("<tr>"+"".join(f"<td>{x}</td>" for x in cells)+"</tr>");continue
  if in_table:out.append("</table>");in_table=False
  if line.startswith("- "):
   if not in_list:out.append("<ul>");in_list=True
   out.append(f"<li>{html.escape(line[2:])}</li>");continue
  if in_list:out.append("</ul>");in_list=False
  if line.startswith("# "):out.append(f"<h1>{html.escape(line[2:])}</h1>")
  elif line.startswith("## "):out.append(f"<h2>{html.escape(line[3:])}</h2>")
  elif line.strip():out.append(f"<p>{html.escape(line)}</p>")
 if in_list:out.append("</ul>")
 if in_table:out.append("</table>")
 body="\n".join(out)
 return f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Scout Finance report</title><style>body{{max-width:980px;margin:auto;padding:32px;font:15px system-ui;color:#172033}}h1{{color:#0b6b58}}table{{width:100%;border-collapse:collapse}}td{{border:1px solid #d8dee8;padding:8px}}p,li{{line-height:1.55}}@media(max-width:650px){{body{{padding:16px}}table{{font-size:12px}}}}</style></head><body>{body}</body></html>'

def write_report(text,output,fmt,sources,kind,state):
 rendered=text if fmt=="md" else markdown_to_html(text)
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(rendered,encoding="utf-8")
 manifest={"schema_version":"1.0","report_type":kind,"consumer_state":state,"generated_at_utc":now(),"format":fmt,"report_path":str(output),"report_sha256":digest(output),"sources":[{"path":str(p),"sha256":digest(p)} for p in sources],"investment_recommendation":False,"broker_action":False}
 mpath=output.with_suffix(output.suffix+".manifest.json");mpath.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8");return mpath

def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument("--type",choices=("universe","watchlist","diagnostic"),required=True);ap.add_argument("--format",choices=("md","html"),default="md");ap.add_argument("--output",type=Path,required=True)
 ap.add_argument("--universe-pointer",type=Path);ap.add_argument("--scoring-pointer",type=Path,required=True);ap.add_argument("--watchlist",type=Path);ap.add_argument("--scores",type=Path);ap.add_argument("--acknowledge-data-readiness-only",action="store_true")
 a=ap.parse_args(argv)
 try:
  sp=load(a.scoring_pointer);sources=[a.scoring_pointer]
  if a.type=="universe":
   if not a.universe_pointer:raise ValueError("--universe-pointer required")
   text=universe_report(load(a.universe_pointer),sp);sources.append(a.universe_pointer);state="CATALOG_AVAILABLE"
  elif a.type=="watchlist":
   if not a.watchlist:raise ValueError("--watchlist required")
   text=watchlist_report(load(a.watchlist),sp);sources.append(a.watchlist);state="CATALOG_AVAILABLE"
  else:
   if not a.acknowledge_data_readiness_only:raise ValueError("diagnostic acknowledgement required")
   if not a.scores:raise ValueError("--scores required")
   text=diagnostic_report(sp,a.scores);sources.append(a.scores);state="DIAGNOSTIC_LOCKED"
  m=write_report(text,a.output,a.format,sources,a.type,state);print(f"PASS wrote {a.output} and {m}");return 0
 except (OSError,ValueError,json.JSONDecodeError) as e:print(f"ERROR: {e}",file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
