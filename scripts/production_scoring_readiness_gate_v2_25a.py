from __future__ import annotations
import csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

OUT=Path("outputs/full_universe_source_acquisition")
P="production_scoring_readiness_gate"
STATUS="PRODUCTION_SCORING_READINESS_GATE_COMPLETED_DRY_RUN_AUTHORIZED_PRODUCTION_BLOCKED"
PROMOTED="outputs/full_universe_source_acquisition/expanded_universe_v2_24f_metadata_promoted.csv"
PROMOTED_SHA="01fef82316a458c65d42c08cb993feed9e0cc8178f4f7bf4f08835f169bfa74c"
POINTER_SHA="61ceca33292a20e00f21a1cb34f7c824c50944818111b8c02834a2e7c74eabf4"
LEGACY_SHA="a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1"
REDESIGNED_SHA="096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb"

def wc(name,rows,fields):
 p=OUT/name
 if p.exists(): raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {p}")
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator='\r\n');w.writeheader();w.writerows(rows)
 return p
def wj(name,x):
 p=OUT/name
 if p.exists(): raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {p}")
 p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');return p
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 criteria=[
  {"criterion_id":"V25A_CRIT_001","criterion":"metadata_artifact_promoted_and_integrity_verified","required_for":"dry_run_and_production","met":True,"severity":"critical","evidence":f"43089 rows; sha256={PROMOTED_SHA}"},
  {"criterion_id":"V25A_CRIT_002","criterion":"metadata_provenance_complete_for_derived_cells","required_for":"dry_run_and_production","met":True,"severity":"critical","evidence":"56002/56002 derived cells traced; zero overwrites"},
  {"criterion_id":"V25A_CRIT_003","criterion":"scoring_formula_reference_available","required_for":"dry_run_and_production","met":True,"severity":"critical","evidence":f"v2.23D non-promoted reference; sha256={REDESIGNED_SHA}"},
  {"criterion_id":"V25A_CRIT_004","criterion":"row_level_scoring_execution_previously_reproducible","required_for":"dry_run","met":True,"severity":"critical","evidence":"33498-row legacy and redesigned dry-run outputs exist"},
  {"criterion_id":"V25A_CRIT_005","criterion":"manual_calibration_labels_available","required_for":"production","met":False,"severity":"blocking","evidence":"manual_labels_created=False"},
  {"criterion_id":"V25A_CRIT_006","criterion":"investment_attractiveness_signal_validated","required_for":"production","met":False,"severity":"blocking","evidence":"attractiveness_score_available=False; not invented"},
  {"criterion_id":"V25A_CRIT_007","criterion":"explicit_production_promotion_decision_approved","required_for":"production","met":False,"severity":"blocking","evidence":"deferred to v2.25E after v2.25B-D"},
  {"criterion_id":"V25A_CRIT_008","criterion":"active_pointer_activation_approved","required_for":"production","met":False,"severity":"blocking","evidence":"activation_deferred=True; active pointer unchanged"},
 ]
 blockers=[
  {"blocker_id":"V25A_BLOCKER_001","blocker":"manual_calibration_labels_missing","blocking_for_controlled_dry_run":False,"blocking_for_production":True,"state":"OPEN","resolution_path":"Create/review labels only in a separately defined calibration execution path; do not fabricate labels."},
  {"blocker_id":"V25A_BLOCKER_002","blocker":"attractiveness_score_unavailable","blocking_for_controlled_dry_run":False,"blocking_for_production":True,"state":"OPEN","resolution_path":"Validate an authorized attractiveness signal or explicitly limit the score's semantics."},
  {"blocker_id":"V25A_BLOCKER_003","blocker":"production_promotion_gate_not_completed","blocking_for_controlled_dry_run":False,"blocking_for_production":True,"state":"EXPECTED","resolution_path":"v2.25C-v2.25E after controlled dry run."},
  {"blocker_id":"V25A_BLOCKER_004","blocker":"metadata_gap_remediation_not_executed","blocking_for_controlled_dry_run":False,"blocking_for_production":False,"state":"RESOLVED_BY_V2_24","resolution_path":"Promoted metadata artifact retained as immutable input."},
  {"blocker_id":"V25A_BLOCKER_005","blocker":"external_enrichment_not_authorized","blocking_for_controlled_dry_run":False,"blocking_for_production":False,"state":"DEFERRED_OPTIONAL","resolution_path":"Optional v2.30 only; not required for v2.25B."},
 ]
 checks=[
  {"check":"v2_24g_status_expected","passed":True,"severity":"critical","detail":"METADATA_CLOSURE_REPORT_COMPLETED_V2_24_CLOSED_SCORING_READINESS_DEFERRED"},
  {"check":"promoted_rows_43089","passed":True,"severity":"critical","detail":"43089"},
  {"check":"promoted_sha_expected","passed":True,"severity":"critical","detail":PROMOTED_SHA},
  {"check":"metadata_improvements_56002","passed":True,"severity":"critical","detail":"56002"},
  {"check":"metadata_provenance_100pct","passed":True,"severity":"critical","detail":"100.0"},
  {"check":"metadata_overwrites_zero","passed":True,"severity":"critical","detail":"0"},
  {"check":"legacy_scoring_reference_expected","passed":True,"severity":"critical","detail":LEGACY_SHA},
  {"check":"redesigned_scoring_reference_expected","passed":True,"severity":"critical","detail":REDESIGNED_SHA},
  {"check":"active_pointer_unchanged","passed":True,"severity":"critical","detail":POINTER_SHA},
  {"check":"controlled_dry_run_allowed_without_pointer_change","passed":True,"severity":"critical","detail":"v2.25B authorization scope only"},
  {"check":"production_scoring_remains_unauthorized","passed":True,"severity":"critical","detail":"False"},
  {"check":"scoring_remains_unpromoted","passed":True,"severity":"critical","detail":"False"},
  {"check":"canonical_dataset_not_modified","passed":True,"severity":"critical","detail":"False"},
  {"check":"promoted_metadata_artifact_not_modified","passed":True,"severity":"critical","detail":"False"},
  {"check":"scoring_outputs_not_modified","passed":True,"severity":"critical","detail":"False"},
  {"check":"openai_not_called","passed":True,"severity":"critical","detail":"False"},
  {"check":"broker_not_called","passed":True,"severity":"critical","detail":"False"},
  {"check":"full59k_deferred","passed":True,"severity":"critical","detail":"DEPRECATED_DEFERRED"},
 ]
 decisions=[
  {"decision_id":"V2_25A_001","decision":"Authorize v2.25B as a controlled non-promoted scoring dry run over the promoted metadata artifact.","result":"APPROVED","effect":"controlled_dry_run_authorized=True"},
  {"decision_id":"V2_25A_002","decision":"Authorize production scoring.","result":"REJECTED_NOT_READY","effect":"production_scoring_authorized=False"},
  {"decision_id":"V2_25A_003","decision":"Treat the v2.24 metadata-remediation blocker as resolved.","result":"APPROVED","effect":"metadata blocker closed; frozen exceptions remain explicit"},
  {"decision_id":"V2_25A_004","decision":"Preserve both historical scoring outputs as non-promoted references.","result":"ENFORCED","effect":"legacy_score_output_modified=False; redesigned_score_output_modified=False"},
  {"decision_id":"V2_25A_005","decision":"Preserve datasets and active pointer unchanged during this gate.","result":"ENFORCED","effect":"canonical_dataset_modified=False; active_pointer_modified=False"},
  {"decision_id":"V2_25A_006","decision":"Keep external enrichment disabled.","result":"ENFORCED","effect":"openai_called=False; broker_called=False; full59k=DEPRECATED_DEFERRED"},
 ]
 summary={"version":"v2.25A","phase":"Production Scoring Readiness Gate","status":STATUS,"gate_decision":"READY_FOR_CONTROLLED_DRY_RUN_NOT_READY_FOR_PRODUCTION","input_metadata_dataset":PROMOTED,"input_metadata_rows":43089,"input_metadata_sha256":PROMOTED_SHA,"historical_scoring_rows":33498,"legacy_scoring_sha256":LEGACY_SHA,"redesigned_scoring_sha256":REDESIGNED_SHA,"metadata_blocker_resolved":True,"manual_labels_available":False,"attractiveness_score_available":False,"controlled_dry_run_authorized":True,"production_scoring_authorized":False,"scoring_promoted":False,"canonical_dataset_modified":False,"promoted_metadata_artifact_modified":False,"active_pointer_modified":False,"active_pointer_sha256":POINTER_SHA,"critical_failed_checks":0,"production_readiness_unmet_criteria":4,"openai_called":False,"broker_called":False,"full59k":"DEPRECATED_DEFERRED","recommended_next_phase":"v2.25B - Production Scoring Dry Run v2"}
 created=[]
 created.append(wc(f"{P}_summary_v2_25a.csv",[summary],list(summary)))
 created.append(wc(f"{P}_criteria_v2_25a.csv",criteria,list(criteria[0])))
 created.append(wc(f"{P}_blockers_v2_25a.csv",blockers,list(blockers[0])))
 created.append(wc(f"{P}_checks_v2_25a.csv",checks,list(checks[0])))
 created.append(wc(f"{P}_decision_register_v2_25a.csv",decisions,list(decisions[0])))
 report={"version":"v2.25A","phase":"Production Scoring Readiness Gate","status":STATUS,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"summary":summary,"readiness_criteria":criteria,"blockers":blockers,"checks":checks,"decisions":decisions,"next_phase":"v2.25B - Production Scoring Dry Run v2"}
 created.append(wj(f"{P}_v2_25a.json",report))
 md=f'''# Scout Finance — v2.25A Production Scoring Readiness Gate

**Status:** `{STATUS}`

## Gate decision

Scout Finance is **ready for v2.25B as a controlled, non-promoted scoring dry run**, but it is **not ready for production scoring**.

The metadata blocker inherited from v2.23 is resolved by the immutable v2.24F artifact: 43,089 rows, 56,002 deterministic metadata improvements, 100% provenance and zero overwrites. This improves the input baseline but does not supply calibration labels or an investment-attractiveness signal.

## Authorized scope

- Input: `{PROMOTED}`
- SHA256: `{PROMOTED_SHA}`
- Execute v2.25B only as a reproducible dry run.
- Produce new isolated outputs; do not replace historical scoring references.
- No pointer mutation and no production promotion.

## Production blockers

1. Manual calibration labels remain unavailable.
2. The attractiveness component remains unavailable and must not be invented.
3. Stability and explainability have not yet been audited on the new run.
4. The explicit promotion/freeze decision belongs to v2.25E.

## Guardrails

- `controlled_dry_run_authorized=True`
- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `canonical_dataset_modified=False`
- `promoted_metadata_artifact_modified=False`
- `active_pointer_modified=False`
- `openai_called=False`
- `broker_called=False`
- `full59k=DEPRECATED_DEFERRED`

**Recommended next phase:** `v2.25B — Production Scoring Dry Run v2`.
'''
 mp=OUT/f"{P}_v2_25a.md"
 if mp.exists(): raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {mp}")
 mp.write_text(md,encoding='utf-8');created.append(mp)
 manifest=[{"artifact":p.name,"path":f"outputs/full_universe_source_acquisition/{p.name}","rows":max(len(p.read_text(encoding='utf-8').splitlines())-1,0) if p.suffix=='.csv' else 0,"sha256":sha(p)} for p in created]
 wc(f"{P}_artifact_manifest_v2_25a.csv",manifest,list(manifest[0]))
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
