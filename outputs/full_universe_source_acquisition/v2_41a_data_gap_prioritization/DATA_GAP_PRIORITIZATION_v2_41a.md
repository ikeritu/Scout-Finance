# Data Gap Prioritization v2.41A

Status: `DATA_GAP_PRIORITIZATION_READY`

This phase prioritizes known data gaps using local artifacts only. It does not download data, does not call network, does not recompute scoring, does not change ranking and does not provide financial recommendations.

Primary next phase: `v2.41B-luxembourg-adapter-or-closure`

## Gap Decisions

| Gap | Decision | Priority | Next phase |
| --- | --- | --- | --- |
| GAP-LUX-ADAPTER | ATTACK_NEXT | 1 | v2.41B-luxembourg-adapter-or-closure |
| GAP-EXTERNAL-PUBLICATION-RISK | KEEP_DOCUMENTED_LIMITATION | 2 | PROJECT_CLOSE_FINAL_REPORT |
| GAP-UK-OFFICIAL-ACCESS | REQUIRES_USER_DECISION | 3 | v2.41C-uk-cboe-manual-review-decision |
| GAP-MANUAL-REVIEWS | DEFER_POST_RELEASE | 4 | v2.41C-uk-cboe-manual-review-decision |
| GAP-FINANCIAL-INSTITUTIONS | REQUIRES_USER_DECISION | 5 | v2.41C-uk-cboe-manual-review-decision |
| GAP-CBOE-EUROPE | BLOCKED_STRUCTURAL | 6 | v2.41C-uk-cboe-manual-review-decision |
| GAP-EUROPE-PRICES | BLOCKED_STRUCTURAL | 7 | v2.41D-final-coverage-limitations |
| GAP-COVERAGE-BELOW-THRESHOLD | KEEP_DOCUMENTED_LIMITATION | 8 | v2.41D-final-coverage-limitations |
| GAP-SECURITY-WARNINGS | KEEP_DOCUMENTED_LIMITATION | 9 | v2.43A-final-consolidated-audit |
| GAP-PRODUCT-LEGAL-WORDING | KEEP_DOCUMENTED_LIMITATION | 10 | v2.42B-final-in-app-guide |
