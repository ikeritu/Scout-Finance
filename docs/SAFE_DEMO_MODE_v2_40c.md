# Safe Demo Mode v2.40C

Status: `SAFE_DEMO_MODE_READY`

Scout Finance now has an opt-in safe demo mode for future Streamlit Cloud publication checks. The mode is enabled only with `SCOUT_FINANCE_SAFE_DEMO_MODE=1`; by default it is off and the local research workflow remains unchanged.

## Demo Behavior

- Shows a visible `Modo demo seguro` label and disclaimer.
- Uses static/offline data already generated in the repository.
- Blocks refresh/rebuild actions from the UI.
- Blocks watchlist writes and private watchlist interaction.
- Keeps ranking read-only and experimental.
- Keeps exports limited to sanitized ranking/report outputs already designed for research use.
- Provides no financial advice, no recommendations, no broker workflow and no external provider access.

No deployment was performed in this phase.
