# v2.28A — Local UI Requirements

**Status:** `LOCAL_UI_REQUIREMENTS_APPROVED_STREAMLIT_REUSE_WITH_POINTER_SAFE_REFACTOR_REQUIRED`

Streamlit will be retained for the local single-user dashboard, but the existing `app.py` requires a pointer-safe refactor before reuse.

## Target navigation

- Inicio / Estado
- Universo
- Watchlists
- Score Explorer
- Informes y exports
- Detalle de activo
- Mantenimiento
- Ayuda y límites

## Critical rule

The legacy Ranking render path must not be reused directly. Every score view must first pass the v2.25F operational scoring pointer. With the current state, the UI must show **SCORING UNAVAILABLE / FAIL-CLOSED** and continue with catalog and watchlist functionality.

## Current truth displayed by the UI

- Operational universe: **43,089**
- Scoring: **inactive**
- Ranking allowed: **false**
- Refresh promotion: **HOLD**
- Provider replay: **13/14**
- Missing replay rows: **2,013**

## Architecture decision

Reuse Streamlit, the visual tokens and the local launch model. Extract pointer-safe data adapters, state logic and views from the monolithic legacy app. No provider, OpenAI, yfinance or pipeline call may run during initial page load.

No code, pointer or dataset was changed in this requirements phase.

**Next:** v2.28B - UI Architecture & Data Adapter.
