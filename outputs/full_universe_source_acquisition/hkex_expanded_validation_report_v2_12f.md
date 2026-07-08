# v2.12F - Validate Expanded Source With HKEX

Status: **HKEX_EXPANDED_VALIDATION_PASSED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **validation-only**

Validation passed: **True**

Generated at UTC: `2026-07-08T12:14:24.347704+00:00`

## Recommended next phase

**v2.12G - HKEX Closure Report**

## Counts

- Baseline rows: 30354
- Expanded rows: 33158
- HKEX rows in expanded: 2804
- Accepted normalized HKEX candidates: 2804
- Exclusions: 14785
- Duplicate exchange+ticker keys: 0
- Duplicate exchange+ticker rows: 0
- Blank ticker rows: 0
- Blank exchange rows: 0
- Blank company_name rows: 1193
- Baseline blank company_name rows: 1193
- First expansion unlocked: True
- Full source unlocked: False
- Rows needed full source: 16842
- Critical failed checks: 0
- Warning failed checks: 0

## Provider breakdown

- cboe_europe_reference_data: 21154
- nasdaq_trader_nasdaqlisted: 3244
- hkex_securities_list: 2804
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- cboe_listed_symbols: 1193

## Integrity checks

- C001 [critical]: Baseline row count matches v2.12E rebuild report -> expected=30354; actual=30354; passed=True
- C002 [critical]: Expanded row count matches v2.12E rebuild report -> expected=33158; actual=33158; passed=True
- C003 [critical]: HKEX rows in expanded match v2.12E rebuild report -> expected=2804; actual=2804; passed=True
- C004 [critical]: Accepted normalized HKEX candidates match HKEX rows added -> expected=2804; actual=2804; passed=True
- C005 [critical]: Exclusions count matches v2.12E rebuild report -> expected=14785; actual=14785; passed=True
- C006 [critical]: Excluded normalized rows match exclusions file -> expected=14785; actual=14785; passed=True
- C007 [critical]: Duplicate exchange+ticker keys remain zero -> expected=0; actual=0; passed=True
- C008 [critical]: Blank ticker rows remain zero -> expected=0; actual=0; passed=True
- C009 [critical]: Blank exchange rows remain zero -> expected=0; actual=0; passed=True
- C010 [warning]: Known blank company_name warning did not increase versus baseline -> expected=<= 1193; actual=1193; passed=True
- C011 [critical]: HKEX expanded rows respect conservative equity allowlist -> expected=0; actual=0; passed=True
- C012 [critical]: First expansion threshold remains unlocked -> expected=True; actual=True; passed=True
- C013 [critical]: Full source threshold remains blocked -> expected=False; actual=False; passed=True
- C014 [critical]: Rows needed full source matches v2.12E rebuild report -> expected=16842; actual=16842; passed=True
- C015 [critical]: Full 59k universe was not launched -> expected=False; actual=False; passed=True

## Hard guards

- phase_type: validation-only
- network_download_performed: False
- raw_files_modified: False
- normalization_performed: False
- net_new_filtering_performed: False
- expanded_universe_rebuilt: False
- scoring_recalculated: False
- openai_called: False
- broker_called: False
- full_59k_universe_launched: False
- overwrite_allowed: False

## Scope note

v2.12F validates the expanded source created by v2.12E.

It does not rebuild, normalize, filter net-new rows, score, call OpenAI, call broker APIs, or launch full 59k.

Full 59k remains blocked.
