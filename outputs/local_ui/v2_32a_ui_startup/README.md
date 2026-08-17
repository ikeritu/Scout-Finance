# v2.32A — UI Startup and Operational Dataset Load

Status: **PASS**.

The stable local UI was exercised from a clean isolated Python environment. The installation contract, minimal dependencies, operational dataset hash, full catalogue load and a real headless Streamlit HTTP startup were validated.

Acceptance results:

- Operational universe: 43,089 rows and 43,089 unique identities.
- Canonical provider coverage: 14/14 with zero missing provenance rows.
- NSE subset: 2,013 rows.
- Streamlit process: started successfully and returned `200 ok` from its health endpoint.
- Production scoring and ranking: still disabled and fail-closed.
- Operational universe pointer, scoring pointer and dataset: unchanged.

This phase validates startup and load only. User journeys and visual usability remain in v2.32B and v2.32C.
