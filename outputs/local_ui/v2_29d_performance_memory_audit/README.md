# v2.29D — Performance & Memory Audit

Status: **COMPLETE · ALL GATES PASS**

The real 43,089-row universe was tested repeatedly: three complete loads, 60 searches, 60 filters, 40 pagination requests, twenty 1,000-item CSV exports and twenty 1,000-item HTML reports.

## Results

- Full load: 2.26s mean, 2.52s maximum.
- Peak traced memory across three load cycles: 59.28 MB.
- Search: 86.19 ms mean, 109.42 ms maximum.
- Filter: 79.25 ms mean, 96.16 ms maximum.
- Pagination: 64.71 ms mean, 82.63 ms maximum.
- 1,000-item watchlist CSV: 14.44 ms mean.
- 1,000-item HTML report: 1.57 ms mean.

The catalog query loop now reuses normalized rows and precomputes filter sets. Against v2.29B this improves mean search by 22.95%, mean filtering by 30.48% and pagination by 56.73%, with identical functional results.

No dataset, operational pointer, scoring authorization or output contract changed.

Validation: `python tests/qa_performance_memory_v2_29d.py <operational-dataset>`

Expected: `PASS: repeated-load/memory/search/filter/pagination/export/report/performance-gates`
