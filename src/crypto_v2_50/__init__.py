"""Crypto data layer (v2.50C): CoinGecko Demo client, call counter and encrypted short-lived cache. No UI, no scoring."""
from __future__ import annotations

from pathlib import Path

CACHE_DIRNAME = "crypto_coingecko_cache_v2_50c"
USAGE_FILENAME = "crypto_coingecko_usage_v2_50c.json"
REVOLUT_FILENAME = "crypto_revolut_assets.txt"  # the person's own list of what Revolut offers (v2.50L); only read by the app


def default_paths(data_dir: Path) -> tuple[Path, Path]:
    """(cache directory, usage counter file) inside the user's data folder (SCOUT_FINANCE_DATA_DIR redirects it)."""
    return Path(data_dir) / CACHE_DIRNAME, Path(data_dir) / USAGE_FILENAME
