# v2.19A - Next Provider Route Selection

Status: **NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_KRX_SELECTED_ACQUISITION_PLAN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **route-selection-only**

Generated at UTC: `2026-08-11T15:16:01.860965+00:00`

## Executive summary

v2.19A selects the next official provider route after TWSE + TPEx closure.

Selected route: **KRX — Korea Exchange Official Listed Securities Route**

This phase is route-selection-only. It does not download raw data, does not extract candidates, does not rebuild an expanded dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Current validated candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Intermediate quality target: `45,000-47,500`
- Stretch target: `50,000`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Selected route

- Selected route id: `KRX_KOREA_EXCHANGE`
- Selected route name: `KRX — Korea Exchange Official Listed Securities Route`
- Provider: `KRX`
- Market: `South Korea`
- Primary URLs: `https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp | https://data.krx.co.kr/ | https://www.data.go.kr/en/data/15094775/openapi.do`
- Selection reason: `Best balance of official exchange source, structured/listed-company coverage, expected net-new contribution, and manageable validation scope.`

## Candidate routes

- #1 `KRX_KOREA_EXCHANGE` — KRX / South Korea — selected — Best balance of official exchange source, structured/listed-company coverage, expected net-new contribution, and manageable validation scope.
- #2 `HKEX_HONG_KONG_EXCHANGE` — HKEX / Hong Kong — backup — Strong official source, but instrument filtering may be more complex because full securities lists include non-common instruments.
- #3 `TMX_TSX_TSXV_CANADA` — TMX / Canada — backup — Potentially strong contribution, but should be evaluated after KRX because TSX/TSXV may require careful issuer/security filtering.
- #4 `ASX_AUSTRALIAN_SECURITIES_EXCHANGE` — ASX / Australia — backup — Good official CSV-style candidate source; likely useful if KRX/HKEX/TMX do not close the 50k gap.
- #5 `TPEx_REPAIR_LATER` — TPEx / Taiwan — deferred — Do not reopen immediately; TWSE closure explicitly left TPEx deferred_or_repair_later.

## Next actions

- Phigh `KRX` — prepare_acquisition_plan — v2.19B - KRX Korea Exchange Acquisition Plan
- Pmedium `50k` — maintain_50k_as_stretch_target — v2.19B - KRX Korea Exchange Acquisition Plan
- Pmedium `backup_routes` — preserve_hkex_tmx_asx_backup_order — v2.20 or later if needed after KRX closure

## Checks

- v2_18i_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_closure_report_v2_18i.json
- v2_18i_status_expected: PASS (critical) — TWSE_TPEX_CLOSURE_COMPLETED_40996_CANDIDATES_NEXT_PROVIDER_SELECTION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- active_canonical_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- current_validated_candidate_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9004
- route_candidates_available: PASS (critical) — route_candidates=5
- selected_route_is_krx: PASS (critical) — selected_route_id=KRX_KOREA_EXCHANGE
- selected_route_has_official_sources: PASS (critical) — KRX Global Listed Company; KRX Data Marketplace; Public Data Portal KRX Listed Stock Information
- selected_route_not_full59k: PASS (critical) — full59k not selected
- selected_route_not_tpex_repair: PASS (critical) — TPEx repair deferred
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- candidate_dataset_not_modified: PASS (critical) — candidate_dataset_modified=False
- no_raw_acquisition: PASS (critical) — raw_acquisition_performed=False
- no_candidate_extraction: PASS (critical) — candidate_extraction_performed=False
- no_expanded_rebuild: PASS (critical) — expanded_rebuild_candidate_performed=False
- route_selection_only: PASS (critical) — phase_type=route-selection-only
- network_not_used_by_script: PASS (critical) — network_download_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- next_provider_needed: PASS (critical) — rows_needed_to_50k=9004

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Closure report performed: false
- Route selection performed: true
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Current candidate dataset read: true
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`v2.19B - KRX Korea Exchange Acquisition Plan`
