# v2.28F — Local UI Closure

Status: **CLOSED · STABLE · POINTER-SAFE · FAIL-CLOSED**

All six v2.28 phases are complete. `app_v2_28.py` is the stable local entrypoint; `app.py` remains the untouched legacy entrypoint.

The closure adds a Windows launcher, end-user guide, private-watchlist Git exclusions, final component inventory and full regression gate across v2.28C–E.

Operational facts remain unchanged: 43,089 universe rows; production scoring unavailable; ranking, recommendations, signals, allocation and broker actions prohibited.

Validation: `python tests/qa_local_ui_closure_v2_28f.py`

Expected: `PASS: inventory/launcher/guide/private-watchlists/v2.28C-D-E-regression/stable-freeze`
