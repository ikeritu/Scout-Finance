# v2.32B — Real User Journey Acceptance

Status: **PASS · 21/21 journeys**.

The application was exercised through Streamlit's UI testing runtime using the full 43,089-row operational universe. The test navigated the same widgets, session state and reruns used by a local user.

Validated journeys cover startup, fail-closed status, search, provider filters, asset detail, watchlist creation/editing/persistence/export/removal, universe/watchlist/diagnostic reports, explicit diagnostic consent, maintenance and help.

One functional incident was discovered and closed: diagnostic consent was tied only to the checkbox widget and disappeared after navigation, making the diagnostic report unreachable. Consent is now persisted separately after the user explicitly opens the diagnostic.

The temporary acceptance watchlist is removed after every run. No dataset or pointer was modified, and production scoring remains unavailable.
