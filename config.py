"""Project configuration for equity_research_ai.

This module centralizes paths, versions, thresholds and environment-based
settings. It deliberately avoids implementing business logic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Load local .env when present. Missing .env is valid for the demo setup.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "prompts"
OUTPUTS_DIR = BASE_DIR / "outputs"

DEMO_DIR = DATA_DIR / "demo"
REAL_DIR = DATA_DIR / "real"
CACHE_DIR = DATA_DIR / "cache"

DEMO_UNIVERSE_PATH = DEMO_DIR / "demo_universe.csv"
REAL_UNIVERSE_PATH = REAL_DIR / "universe.csv"

DEMO_DB_PATH = DEMO_DIR / "demo_signals.db"
REAL_DB_PATH = REAL_DIR / "signals.db"

DEMO_CACHE_DIR = CACHE_DIR / "demo"
REAL_CACHE_DIR = CACHE_DIR / "real"

EXPORTS_DIR = OUTPUTS_DIR / "exports"
LOGS_DIR = OUTPUTS_DIR / "logs"

APP_VERSION = "v0.1"
SCORING_VERSION = "v0.1"
PROMPT_VERSION = "v0.1"
SCHEMA_VERSION = "v0.1"

MIN_PRICE = 2
MIN_MARKET_CAP = 100_000_000
MIN_AVG_VOLUME_50D = 300_000
MIN_DATA_QUALITY_SCORE = 60

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
APP_PASSWORD = os.getenv("APP_PASSWORD", "change_me")
OPENAI_MODEL_LIGHT = os.getenv("OPENAI_MODEL_LIGHT", "gpt-5.4-mini")
OPENAI_MODEL_STRONG = os.getenv("OPENAI_MODEL_STRONG", "gpt-5.5")
ENABLE_OPENAI = os.getenv("ENABLE_OPENAI", "false").lower() == "true"
ENABLE_STRONG_MODEL = os.getenv("ENABLE_STRONG_MODEL", "false").lower() == "true"
MAX_OPENAI_COMPANIES_PER_RUN = int(os.getenv("MAX_OPENAI_COMPANIES_PER_RUN", "5"))
OPENAI_DAILY_BUDGET_USD = float(os.getenv("OPENAI_DAILY_BUDGET_USD", "5"))
OPENAI_MONTHLY_BUDGET_USD = float(os.getenv("OPENAI_MONTHLY_BUDGET_USD", "50"))
DEFAULT_MODE = os.getenv("DEFAULT_MODE", "demo")


def get_paths(mode: str = DEFAULT_MODE) -> Dict[str, Path]:
    """Return project paths for demo or real mode.

    Args:
        mode: Either "demo" or "real".

    Raises:
        ValueError: If mode is not "demo" or "real".
    """
    normalized_mode = mode.lower().strip()

    if normalized_mode == "demo":
        return {
            "mode": normalized_mode,
            "data_dir": DEMO_DIR,
            "universe_path": DEMO_UNIVERSE_PATH,
            "db_path": DEMO_DB_PATH,
            "cache_dir": DEMO_CACHE_DIR,
            "exports_dir": EXPORTS_DIR,
            "logs_dir": LOGS_DIR,
            "prompts_dir": PROMPTS_DIR,
        }

    if normalized_mode == "real":
        return {
            "mode": normalized_mode,
            "data_dir": REAL_DIR,
            "universe_path": REAL_UNIVERSE_PATH,
            "db_path": REAL_DB_PATH,
            "cache_dir": REAL_CACHE_DIR,
            "exports_dir": EXPORTS_DIR,
            "logs_dir": LOGS_DIR,
            "prompts_dir": PROMPTS_DIR,
        }

    raise ValueError("mode must be either 'demo' or 'real'")
