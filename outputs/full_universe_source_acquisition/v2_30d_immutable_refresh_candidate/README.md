# v2.30D — Immutable Refresh Candidate Build

Status: **full candidate materialized and validated; not promoted**.

The candidate contains the complete 43,089-row universe. It is stored as XZ-compressed CSV to keep the repository artifact compact while retaining a fully reversible physical dataset.

## Exact transformation

Only 2,013 cells changed, all in `source_provider`. Rows matching the reconciled NSE predicate now contain `nse_india`. No identity, market, classification or scoring field changed.

## Validation

- Rows: 43,089 before and after.
- Columns: 33 before and after.
- Changed rows/cells: 2,013/2,013.
- Unexpected changed fields: 0.
- Blank `source_provider`: 2,013 → 0.
- Canonical provider coverage: 14/14.
- Candidate CSV SHA256: `73cf3528a56e79833b3b2cad33ed0b0eb577e3e7dcd803d2976be0ef771deebe`.
- XZ SHA256: `4cbde1e534ccf145542e6d0bd0c1f5aec7dba4d43037aea5f115e1ea9b46d6bf`.

To extract: `xz -dc refresh_candidate_v2_30d.csv.xz > refresh_candidate_v2_30d.csv`.

The current universe and scoring pointers remain unchanged. Next: **v2.30E — delta, quality and rollback gate**.
