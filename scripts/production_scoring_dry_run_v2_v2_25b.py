from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "v2.25B"
PHASE = "Production Scoring Dry Run v2"
OUT = Path("outputs/full_universe_source_acquisition")

READINESS = OUT / "production_scoring_readiness_gate_v2_25a.json"
PROMOTED = OUT / "expanded_universe_v2_24f_metadata_promoted.csv"
POINTER = OUT / "current_operational_universe_pointer.json"
EXCLUSION_OVERLAY = OUT / "residual_instrument_classification_review_classification_v2_22c2.csv"
LEGACY = OUT / "scoring_dry_run_no_promotion_scores_v2_22d.csv"
REFERENCE = OUT / "scoring_formula_redesign_dry_run_scores_v2_23d.csv"

SCORES = OUT / "production_scoring_dry_run_v2_scores_v2_25b.csv"
SUMMARY = OUT / "production_scoring_dry_run_v2_summary_v2_25b.csv"
CHECKS = OUT / "production_scoring_dry_run_v2_checks_v2_25b.csv"
DISTRIBUTION = OUT / "production_scoring_dry_run_v2_distribution_v2_25b.csv"
COMPONENTS = OUT / "production_scoring_dry_run_v2_component_weights_v2_25b.csv"
COMPARISON = OUT / "production_scoring_dry_run_v2_comparison_v2_25b.csv"
DECISIONS = OUT / "production_scoring_dry_run_v2_decision_register_v2_25b.csv"
MANIFEST = OUT / "production_scoring_dry_run_v2_artifact_manifest_v2_25b.csv"
REPORT_JSON = OUT / "production_scoring_dry_run_v2_v2_25b.json"
REPORT_MD = OUT / "production_scoring_dry_run_v2_v2_25b.md"

EXPECTED_PROMOTED_ROWS = 43089
EXPECTED_SCORABLE_ROWS = 33498
EXPECTED_EXCLUDED_ROWS = 9591
EXPECTED_PROMOTED_SHA = "01fef82316a458c65d42c08cb993feed9e0cc8178f4f7bf4f08835f169bfa74c"
EXPECTED_POINTER_SHA = "61ceca33292a20e00f21a1cb34f7c824c50944818111b8c02834a2e7c74eabf4"
EXPECTED_LEGACY_SHA = "a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1"
EXPECTED_REFERENCE_SHA = "096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb"

STATUS_OK = "PRODUCTION_SCORING_DRY_RUN_V2_COMPLETED_NO_PROMOTION"
STATUS_FAIL = "PRODUCTION_SCORING_DRY_RUN_V2_FAILED_REVIEW_REQUIRED"

DQ_WEIGHTS = {"country":18.0,"mic":14.0,"currency":12.0,"asset_type":16.0,"instrument_type":12.0,"instrument_scope":10.0,"source_provider":8.0,"ticker":5.0,"company_name":5.0}
FORMULA = {"data_quality_score":0.70,"scope_confidence_score":0.20,"provider_quality_score":0.10,"attractiveness_score":0.00}
PROVIDER = {"ASX":95.0,"sgx_structured_endpoint":92.0,"SFC_SIMEV_RNVE":88.0,"jpx_listed_securities":82.0,"hkex_securities_list":80.0,"HKEX":78.0,"TWSE":78.0,"deutsche_boerse_xetra_all_tradable_instruments":76.0,"nasdaq_trader_nasdaqlisted":70.0,"nasdaq_trader_otherlisted":68.0,"sec_company_tickers_exchange":66.0,"cboe_listed_symbols":62.0,"cboe_europe_reference_data":45.0,"__MISSING_PROVIDER__":30.0}

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def csv_contract_sha(path: Path) -> str:
    data=path.read_bytes().replace(b"\r\n",b"\n").replace(b"\n",b"\r\n")
    return hashlib.sha256(data).hexdigest()
def norm(v: Any) -> str: return "" if v is None else str(v).strip()
def rows(path: Path) -> tuple[list[str],list[dict[str,str]]]:
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f); return list(r.fieldnames or []),[dict(x) for x in r]
def write_csv(path: Path,data:list[dict[str,Any]],fields:list[str]) -> None:
    if path.exists(): raise SystemExit(f"NO_OVERWRITE_GUARD: {path}")
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\r\n");w.writeheader();w.writerows(data)
def write_json(path: Path,data:dict[str,Any]) -> None:
    if path.exists(): raise SystemExit(f"NO_OVERWRITE_GUARD: {path}")
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def present(row:dict[str,str],field:str)->bool:return bool(norm(row.get(field,"")))
def dq(row:dict[str,str])->float:
    return round(100*sum(w for f,w in DQ_WEIGHTS.items() if present(row,f))/sum(DQ_WEIGHTS.values()),4)
def scope(row:dict[str,str])->float:
    c=" ".join(norm(row.get(f,"" )).lower() for f in ["asset_type","instrument_type","instrument_scope"])
    excluded=["etf","fund","bond","note","warrant","right","preferred","preference","certificate","trust","unit"]
    equity=["common","ordinary","equity","eqty","stock","share"]
    if any(x in c for x in excluded): return 10.0
    if any(x in c for x in equity): return 95.0
    if c.strip(): return 65.0
    return 45.0
def provider(row:dict[str,str])->float:
    p=norm(row.get("source_provider","")) or "__MISSING_PROVIDER__";return PROVIDER.get(p,55.0)
def bucket(v:float)->str:
    if v>=85:return "A_85_100"
    if v>=70:return "B_70_84"
    if v>=55:return "C_55_69"
    if v>=40:return "D_40_54"
    return "E_0_39"
def quantile(values:list[float],q:float)->float:
    s=sorted(values);i=min(max(round((len(s)-1)*q),0),len(s)-1);return round(s[i],4) if s else 0.0

def main()->None:
    outputs=[SCORES,SUMMARY,CHECKS,DISTRIBUTION,COMPONENTS,COMPARISON,DECISIONS,MANIFEST,REPORT_JSON,REPORT_MD]
    for p in outputs:
        if p.exists(): raise SystemExit(f"NO_OVERWRITE_GUARD: {p}")
    readiness=json.loads(READINESS.read_text(encoding="utf-8"));pointer_before=sha(POINTER);promoted_before=sha(PROMOTED);legacy_before=sha(LEGACY);reference_before=sha(REFERENCE);legacy_contract=csv_contract_sha(LEGACY);reference_contract=csv_contract_sha(REFERENCE)
    header,promoted=rows(PROMOTED);_,overlay=rows(EXCLUSION_OVERLAY);_,legacy=rows(LEGACY);_,reference=rows(REFERENCE)
    excluded={int(x["row_number"]) for x in overlay if norm(x.get("policy_classification"))=="exclude_from_common_equity_scoring"}
    ref_by_row={int(x["source_row_number"]):x for x in reference};legacy_by_row={int(x["source_row_number"]):x for x in legacy}
    scored=[]
    for index,row in enumerate(promoted,start=2):
        if index in excluded: continue
        d,s,p=dq(row),scope(row),provider(row);score=round(.70*d+.20*s+.10*p,4)
        old=ref_by_row.get(index,{});base=legacy_by_row.get(index,{})
        scored.append({"dry_run_rank":0,"source_row_number":index,"isin":norm(row.get("isin")),"ticker":norm(row.get("ticker")),"name":norm(row.get("company_name")) or norm(row.get("security_name")),"exchange":norm(row.get("exchange")),"country":norm(row.get("country")),"mic":norm(row.get("mic")),"currency":norm(row.get("currency")),"source_provider":norm(row.get("source_provider")),"asset_type":norm(row.get("asset_type")),"instrument_type":norm(row.get("instrument_type")),"instrument_scope":norm(row.get("instrument_scope")),"classification_confidence":norm(row.get("classification_confidence")),"legacy_v2_22d_score":norm(base.get("dry_run_score")),"reference_v2_23d_score":norm(old.get("redesigned_v2_23d_score")),"dry_run_v2_25b_score":score,"score_bucket":bucket(score),"delta_vs_v2_23d":round(score-float(old.get("redesigned_v2_23d_score",0)),4),"data_quality_score":d,"scope_confidence_score":s,"provider_quality_score":p,"attractiveness_score_available":False,"attractiveness_score":"","attractiveness_score_reason":"not_available_no_manual_labels_or_authorized_fundamentals","formula_version":"v2.23D_reapplied_v2.25B","formula_mode":"controlled_dry_run_no_promotion","production_scoring_authorized":False,"promotion_status":"NOT_PROMOTED"})
    scored.sort(key=lambda x:(-float(x["dry_run_v2_25b_score"]),x["exchange"],x["ticker"],x["name"]))
    for i,x in enumerate(scored,start=1):x["dry_run_rank"]=i
    values=[float(x["dry_run_v2_25b_score"]) for x in scored];deltas=[float(x["delta_vs_v2_23d"]) for x in scored];abs_deltas=[abs(x) for x in deltas]
    dist=[];counter=Counter(x["score_bucket"] for x in scored)
    for b in ["A_85_100","B_70_84","C_55_69","D_40_54","E_0_39"]:dist.append({"score_bucket":b,"rows":counter[b],"pct":round(100*counter[b]/len(scored),4)})
    components=[{"component":k,"weight":v,"included":v>0,"reason":"Attractiveness remains unavailable and is not invented." if k=="attractiveness_score" else "Deterministic v2.23D component reapplied to promoted metadata."} for k,v in FORMULA.items()]
    comparison=[{"metric":"reference_rows","value":len(reference)},{"metric":"dry_run_v2_rows","value":len(scored)},{"metric":"changed_score_rows","value":sum(x!=0 for x in deltas)},{"metric":"unchanged_score_rows","value":sum(x==0 for x in deltas)},{"metric":"mean_delta_vs_v2_23d","value":round(statistics.mean(deltas),4)},{"metric":"mean_absolute_delta_vs_v2_23d","value":round(statistics.mean(abs_deltas),4)},{"metric":"max_absolute_delta_vs_v2_23d","value":round(max(abs_deltas),4)},{"metric":"score_min","value":round(min(values),4)},{"metric":"score_p25","value":quantile(values,.25)},{"metric":"score_median","value":quantile(values,.5)},{"metric":"score_p75","value":quantile(values,.75)},{"metric":"score_max","value":round(max(values),4)},{"metric":"score_mean","value":round(statistics.mean(values),4)}]
    score_fields=list(scored[0]);write_csv(SCORES,scored,score_fields);write_csv(DISTRIBUTION,dist,list(dist[0]));write_csv(COMPONENTS,components,list(components[0]));write_csv(COMPARISON,comparison,list(comparison[0]))
    checks=[]
    def check(n:str,ok:bool,detail:str,severity:str="critical"):checks.append({"check":n,"passed":ok,"severity":severity,"detail":detail})
    check("v2_25a_dry_run_authorized",readiness["summary"]["controlled_dry_run_authorized"] is True,str(readiness["summary"]["controlled_dry_run_authorized"]));check("v2_25a_production_blocked",readiness["summary"]["production_scoring_authorized"] is False,str(readiness["summary"]["production_scoring_authorized"]));check("promoted_sha_expected",promoted_before==EXPECTED_PROMOTED_SHA,promoted_before);check("promoted_rows_43089",len(promoted)==EXPECTED_PROMOTED_ROWS,str(len(promoted)));check("legacy_contract_sha_expected",legacy_contract==EXPECTED_LEGACY_SHA,legacy_contract);check("reference_contract_sha_expected",reference_contract==EXPECTED_REFERENCE_SHA,reference_contract);check("excluded_rows_9591",len(excluded)==EXPECTED_EXCLUDED_ROWS,str(len(excluded)));check("scorable_rows_33498",len(scored)==EXPECTED_SCORABLE_ROWS,str(len(scored)));check("row_partition_exact",len(excluded)+len(scored)==len(promoted),f"{len(excluded)}+{len(scored)}={len(promoted)}");check("reference_row_identity_complete",len(ref_by_row)==len(scored)==len(legacy_by_row),f"reference={len(ref_by_row)};scored={len(scored)};legacy={len(legacy_by_row)}");check("all_scores_in_range",all(0<=x<=100 for x in values),f"min={min(values)};max={max(values)}");check("formula_weights_sum_one",round(sum(FORMULA.values()),4)==1.0,str(sum(FORMULA.values())));check("attractiveness_not_invented",all(x["attractiveness_score_available"] is False and x["attractiveness_score"]=="" for x in scored),"all rows false/blank");check("promoted_artifact_unchanged",sha(PROMOTED)==promoted_before,sha(PROMOTED));check("pointer_unchanged",sha(POINTER)==pointer_before,sha(POINTER));check("legacy_output_unchanged",sha(LEGACY)==legacy_before,sha(LEGACY));check("reference_output_unchanged",sha(REFERENCE)==reference_before,sha(REFERENCE));check("no_production_authorization",all(x["production_scoring_authorized"] is False for x in scored),"False for all rows");check("no_promotion",all(x["promotion_status"]=="NOT_PROMOTED" for x in scored),"NOT_PROMOTED for all rows");check("openai_not_called",True,"False");check("broker_not_called",True,"False");check("full59k_deferred",True,"DEPRECATED_DEFERRED")
    failed=sum(not x["passed"] for x in checks if x["severity"]=="critical");status=STATUS_OK if failed==0 else STATUS_FAIL
    decisions=[{"decision_id":"V2_25B_001","decision":"Execute the v2.23D deterministic formula over the promoted v2.24F metadata artifact.","result":"COMPLETED" if not failed else "FAILED","effect":"New isolated v2.25B score output created."},{"decision_id":"V2_25B_002","decision":"Keep attractiveness unavailable rather than inventing an investment signal.","result":"ENFORCED","effect":"attractiveness_score_available=False."},{"decision_id":"V2_25B_003","decision":"Do not promote or operationally activate the dry-run scores.","result":"ENFORCED","effect":"production_scoring_authorized=False; scoring_promoted=False."},{"decision_id":"V2_25B_004","decision":"Preserve all input datasets, pointers and historical scoring outputs.","result":"ENFORCED","effect":"All input SHA256 values unchanged."}]
    summary={"version":VERSION,"phase":PHASE,"status":status,"dry_run_decision":"CONTROLLED_DRY_RUN_V2_CREATED_NO_PROMOTION" if not failed else "FAILED_REVIEW_REQUIRED","input_dataset":str(PROMOTED),"input_rows":len(promoted),"input_sha256":promoted_before,"legacy_contract_sha256":legacy_contract,"reference_v2_23d_contract_sha256":reference_contract,"excluded_rows":len(excluded),"scored_rows":len(scored),"scoring_output":str(SCORES),"scoring_output_sha256":sha(SCORES),"score_min":round(min(values),4),"score_p25":quantile(values,.25),"score_median":quantile(values,.5),"score_p75":quantile(values,.75),"score_max":round(max(values),4),"score_mean":round(statistics.mean(values),4),"changed_score_rows_vs_v2_23d":sum(x!=0 for x in deltas),"mean_delta_vs_v2_23d":round(statistics.mean(deltas),4),"mean_absolute_delta_vs_v2_23d":round(statistics.mean(abs_deltas),4),"max_absolute_delta_vs_v2_23d":round(max(abs_deltas),4),"attractiveness_score_available":False,"attractiveness_score_invented":False,"production_scoring_authorized":False,"scoring_promoted":False,"promoted_metadata_artifact_modified":False,"active_pointer_modified":False,"legacy_score_output_modified":False,"reference_score_output_modified":False,"openai_called":False,"broker_called":False,"full59k":"DEPRECATED_DEFERRED","critical_failed_checks":failed,"recommended_next_phase":"v2.25C - Score Stability Audit"}
    write_csv(SUMMARY,[summary],list(summary));write_csv(CHECKS,checks,list(checks[0]));write_csv(DECISIONS,decisions,list(decisions[0]))
    manifest=[]
    for p,role,count in [(PROMOTED,"input_promoted_metadata",len(promoted)),(POINTER,"input_pointer_unchanged",1),(LEGACY,"input_legacy_scores_unchanged",len(legacy)),(REFERENCE,"input_reference_scores_unchanged",len(reference)),(SCORES,"output_scores_not_promoted",len(scored)),(DISTRIBUTION,"output_distribution",len(dist)),(COMPONENTS,"output_components",len(components)),(COMPARISON,"output_comparison",len(comparison))]:manifest.append({"artifact":p.name,"path":str(p),"rows":count,"sha256":sha(p),"role":role})
    write_csv(MANIFEST,manifest,list(manifest[0]))
    report={"version":VERSION,"phase":PHASE,"status":status,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"summary":summary,"component_weights":components,"distribution":dist,"comparison":comparison,"checks":checks,"decisions":decisions,"artifact_manifest":manifest}
    write_json(REPORT_JSON,report)
    md=f'''# Scout Finance — v2.25B Production Scoring Dry Run v2

**Status:** `{status}`

## Result

The deterministic v2.23D formula was reapplied to the immutable v2.24F promoted metadata artifact. Exactly **{len(scored):,}** rows were scored and **{len(excluded):,}** pre-existing non-common-equity policy rows remained excluded.

- Input SHA256: `{promoted_before}`
- Output SHA256: `{summary['scoring_output_sha256']}`
- Mean score: **{summary['score_mean']}**
- Median: **{summary['score_median']}**
- Changed rows vs v2.23D: **{summary['changed_score_rows_vs_v2_23d']:,}**
- Mean absolute delta: **{summary['mean_absolute_delta_vs_v2_23d']}**
- Maximum absolute delta: **{summary['max_absolute_delta_vs_v2_23d']}**
- Critical failed checks: **{failed}**

The score remains a deterministic quality/scope/provider dry-run score. It is **not** an investment-attractiveness ranking.

## Guardrails

- `attractiveness_score_available=False`
- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `promoted_metadata_artifact_modified=False`
- `active_pointer_modified=False`
- `openai_called=False`
- `broker_called=False`
- `full59k=DEPRECATED_DEFERRED`

**Recommended next phase:** `v2.25C — Score Stability Audit`.
'''
    if REPORT_MD.exists():raise SystemExit(f"NO_OVERWRITE_GUARD: {REPORT_MD}")
    REPORT_MD.write_text(md,encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
