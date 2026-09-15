"""Safe demo mode controls for Scout Finance.

The mode is opt-in through SCOUT_FINANCE_SAFE_DEMO_MODE. Missing or unknown
values keep the existing local research app behavior.
"""
from __future__ import annotations

import os


TRUTHY_VALUES = {"1", "true", "yes", "on", "safe_demo"}

SAFE_DEMO_LABEL = "Modo demo seguro"
SAFE_DEMO_DISCLAIMER = (
    "Modo demo seguro: datos estaticos/offline, ranking experimental de investigacion, "
    "sin asesoramiento financiero, sin broker, sin proveedores externos y sin acciones de escritura."
)


def is_safe_demo_mode() -> bool:
    return os.getenv("SCOUT_FINANCE_SAFE_DEMO_MODE", "").strip().casefold() in TRUTHY_VALUES


def render_safe_demo_banner(st, enabled: bool) -> None:
    if enabled:
        st.warning(SAFE_DEMO_DISCLAIMER)


def blocked_message(action: str) -> str:
    return f"{action} no disponible en Modo demo seguro."
