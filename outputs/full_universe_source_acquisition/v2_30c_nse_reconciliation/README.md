# v2.30C — NSE Missing Rows Reconciliation

Status: **2,013/2,013 reconciled; candidate build ready; pointers unchanged**.

Every NSE row previously grouped as missing provenance now has an individual disposition. The proposed deterministic action is to set `source_provider=nse_india` only where all three predicates match: `provider=nse_india_v2_17g`, `exchange=NSE`, and `country=India`.

## Reconciliation result

- Dispositioned: 2,013/2,013.
- Ready for candidate normalization: 2,013.
- Unresolved or quarantined: 0.
- Unique instrument IDs, symbols and ISINs: 2,013 each.
- Duplicate groups: 0.
- Cross-cohort identity collisions: 0.
- Unrelated rows selected by the alias rule: 0.

The ledger records the proposed change row by row. It is evidence for the next phase, not a mutation of the active universe.

Next: **v2.30D — materialize a new immutable candidate with 14/14 canonical provider coverage**.
