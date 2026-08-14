#!/usr/bin/env python3
"""Fail-closed static HTML score explorer for Scout Finance v2.27D."""
from __future__ import annotations
import argparse,csv,hashlib,html,json,sys
from collections import Counter,defaultdict
from pathlib import Path

COMPONENTS=("data_quality_score","scope_confidence_score","provider_quality_score","attractiveness_score")
FORBIDDEN_DIAGNOSTIC_FIELDS=("dry_run_rank","legacy_v2_22d_score")

def digest(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def load_pointer(path):
 return json.loads(path.read_text(encoding="utf-8"))

def active_contract(p):
 c=p.get("consumer_contract",{})
 checks=[
  p.get("status") not in ("NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED",None),
  p.get("active_scoring_available") is True,
  p.get("production_scoring_authorized") is True,
  p.get("scoring_promoted") is True,
  bool(p.get("active_scoring_artifact")),
  bool(p.get("active_scoring_sha256")),
  c.get("allow_ranking") is True,
 ]
 return all(checks)

def numeric(value):
 try:return float(value)
 except (TypeError,ValueError):return None

def summarize(path):
 total=0;buckets=Counter();providers=Counter();countries=Counter();sums=defaultdict(float);counts=Counter()
 authorized_values=set();promotion_values=set();formula_values=set()
 with path.open("r",encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f);headers=set(reader.fieldnames or [])
  if "dry_run_v2_25b_score" not in headers and "score" not in headers:raise ValueError("score column missing")
  for row in reader:
   total+=1;buckets[row.get("score_bucket") or "UNKNOWN"]+=1;providers[row.get("source_provider") or "UNKNOWN"]+=1;countries[row.get("country") or "UNKNOWN"]+=1
   authorized_values.add(row.get("production_scoring_authorized",""));promotion_values.add(row.get("promotion_status",""));formula_values.add(row.get("formula_version",""))
   for k in COMPONENTS:
    v=numeric(row.get(k))
    if v is not None:sums[k]+=v;counts[k]+=1
 return {"rows":total,"buckets":buckets,"providers":providers,"countries":countries,
         "component_means":{k:(sums[k]/counts[k] if counts[k] else None) for k in COMPONENTS},
         "component_coverage":{k:counts[k] for k in COMPONENTS},
         "authorization_values":sorted(authorized_values),"promotion_values":sorted(promotion_values),"formula_values":sorted(formula_values)}

def bars(counter,total,limit=12):
 out=[]
 for label,count in counter.most_common(limit):
  pct=100*count/total if total else 0
  out.append(f'<div class="barrow"><span>{html.escape(str(label))}</span><div class="track"><i style="width:{pct:.2f}%"></i></div><b>{count:,} · {pct:.1f}%</b></div>')
 return "\n".join(out)

def page(title,badge,notice,body):
 return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>
:root{{--bg:#08111f;--card:#111d2f;--text:#edf3fb;--muted:#98a8bd;--line:#263750;--accent:#42d3a5;--warn:#ffbf69}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#08111f,#0d1727);color:var(--text);font:15px system-ui,sans-serif}}
main{{max-width:1100px;margin:auto;padding:34px}}h1{{font-size:30px;margin:.2rem 0}}h2{{font-size:18px}}.muted{{color:var(--muted)}}.badge{{display:inline-block;padding:7px 11px;border:1px solid var(--line);border-radius:999px;color:var(--warn);font-weight:700}}
.notice{{margin:22px 0;padding:16px;border-left:4px solid var(--warn);background:#211b15;border-radius:8px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:14px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}}.metric{{font-size:28px;font-weight:800}}.barrow{{display:grid;grid-template-columns:130px 1fr 105px;gap:10px;align-items:center;margin:9px 0}}
.track{{height:9px;background:#263750;border-radius:9px;overflow:hidden}}.track i{{display:block;height:100%;background:var(--accent)}}b{{text-align:right;font-size:12px}}footer{{margin-top:26px;color:var(--muted);font-size:12px}}
@media(max-width:650px){{main{{padding:20px}}.barrow{{grid-template-columns:90px 1fr}}.barrow b{{grid-column:2}}}}
</style></head><body><main><span class="badge">{html.escape(badge)}</span><h1>{html.escape(title)}</h1><div class="notice">{html.escape(notice)}</div>{body}
<footer>Scout Finance v2.27D · Static local prototype · No broker actions · No investment recommendation</footer></main></body></html>"""

def locked_html(pointer):
 body=f'<div class="grid"><section class="card"><h2>Operational state</h2><div class="metric">Unavailable</div><p class="muted">{html.escape(pointer.get("status","UNKNOWN"))}</p></section><section class="card"><h2>Safe fallback</h2><p>Universe catalog and watchlists remain available without scores.</p></section></div>'
 return page("Score Explorer","FAIL-CLOSED","No active production scoring artifact is authorized. Scores, rankings and signals are intentionally hidden.",body)

def diagnostic_html(summary):
 total=summary["rows"];means=summary["component_means"];coverage=summary["component_coverage"]
 cards="".join(f'<section class="card"><h2>{html.escape(k.replace("_"," ").title())}</h2><div class="metric">{("N/A" if means[k] is None else f"{means[k]:.1f}")}</div><p class="muted">coverage {coverage[k]:,}/{total:,}</p></section>' for k in COMPONENTS)
 body=f"""<div class="grid"><section class="card"><h2>Diagnostic rows</h2><div class="metric">{total:,}</div><p class="muted">of 43,089 operational instruments</p></section>
<section class="card"><h2>Formula</h2><div class="metric">{html.escape(", ".join(summary["formula_values"]))}</div><p class="muted">controlled dry run</p></section></div>
<h2>Component means</h2><div class="grid">{cards}</div>
<div class="grid"><section class="card"><h2>Score buckets</h2>{bars(summary["buckets"],total)}</section><section class="card"><h2>Provider coverage</h2>{bars(summary["providers"],total)}</section></div>
<section class="card"><h2>Country coverage</h2>{bars(summary["countries"],total)}</section>"""
 return page("Data-readiness Score Explorer","DIAGNOSTIC · NOT PRODUCTION","This view explains data quality and coverage only. It is not an investment ranking; attractiveness is unavailable and no assets are ordered by score.",body)

def production_html(summary):
 total=summary["rows"]
 body=f'<div class="grid"><section class="card"><h2>Authorized scored rows</h2><div class="metric">{total:,}</div></section><section class="card"><h2>Score distribution</h2>{bars(summary["buckets"],total)}</section></div>'
 return page("Production Score Explorer","AUTHORIZED PRODUCTION","Active promoted scoring passed the operational pointer contract. This prototype remains informational and performs no broker action.",body)

def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument("--pointer",type=Path,required=True);ap.add_argument("--output",type=Path,required=True)
 ap.add_argument("--mode",choices=("auto","diagnostic"),default="auto");ap.add_argument("--scores",type=Path);ap.add_argument("--acknowledge-data-readiness-only",action="store_true")
 a=ap.parse_args(argv)
 try:
  p=load_pointer(a.pointer)
  if a.mode=="diagnostic":
   if not a.acknowledge_data_readiness_only:raise ValueError("diagnostic acknowledgement required")
   if not a.scores:raise ValueError("--scores is required in diagnostic mode")
   d=p.get("diagnostic_artifact") or {}
   if d.get("role")!="DATA_READINESS_ONLY" or d.get("production_eligible") is not False:raise ValueError("pointer diagnostic contract invalid")
   if d.get("sha256") and digest(a.scores)!=d["sha256"]:raise ValueError("diagnostic artifact SHA-256 mismatch")
   s=summarize(a.scores)
   if s["rows"]!=d.get("rows"):raise ValueError("diagnostic row count mismatch")
   if any(v not in ("False","false","0") for v in s["authorization_values"]):raise ValueError("diagnostic rows claim authorization")
   output=diagnostic_html(s)
  elif active_contract(p):
   score_path=Path(p["active_scoring_artifact"])
   if not score_path.is_absolute():score_path=a.pointer.resolve().parents[2]/score_path
   if digest(score_path)!=p["active_scoring_sha256"]:raise ValueError("active score SHA-256 mismatch")
   output=production_html(summarize(score_path))
  else:output=locked_html(p)
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(output,encoding="utf-8");print(f"PASS wrote {a.output}");return 0
 except (OSError,ValueError,json.JSONDecodeError) as e:print(f"ERROR: {e}",file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
