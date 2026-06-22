"""
Cache module.

This module provides a simple file-based cache for MVP dataframes.

Current scope:
- Save and load pandas DataFrames as CSV.
- Save and load metadata as JSON.
- Cache market snapshots by mode and date.
- List and clear cache files.

Not included in this phase:
- Advanced cache invalidation.
- Database cache.
- Remote cache.
- Background jobs.
- Streamlit UI.
- yfinance integration changes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from config import get_paths


DEFAULT_CACHE_SUBDIR = "market_snapshots"


def utc_now_iso() -> str:
    """
    Return current UTC datetime in ISO format.
    """

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today_utc_str() -> str:
    """
    Return current UTC date as YYYYMMDD.
    """

    return datetime.now(timezone.utc).strftime("%Y%m%d")


def get_cache_dir(mode: str = "demo", subdir: str = DEFAULT_CACHE_SUBDIR) -> Path:
    """
    Resolve and create the cache directory for a mode.

    Parameters
    ----------
    mode:
        Either "demo" or "real".
    subdir:
        Cache subdirectory name.

    Returns
    -------
    pathlib.Path
        Cache directory.
    """

    if mode not in {"demo", "real"}:
        raise ValueError("Invalid mode. Expected 'demo' or 'real'.")

    paths = get_paths(mode)

    if "cache_dir" in paths:
        cache_root = Path(paths["cache_dir"])
    else:
        cache_root = Path("data") / "cache" / mode

    cache_dir = cache_root / subdir
    cache_dir.mkdir(parents=True, exist_ok=True)

    return cache_dir


def build_cache_key(
    name: str,
    mode: str = "demo",
    period: str | None = None,
    date_str: str | None = None,
) -> str:
    """
    Build a simple cache key.

    Parameters
    ----------
    name:
        Logical cache name, for example "market_snapshot".
    mode:
        Either "demo" or "real".
    period:
        Optional period label, for example "1y".
    date_str:
        Optional date. If None, today's UTC date is used.

    Returns
    -------
    str
        Cache key safe for filenames.
    """

    if date_str is None:
        date_str = today_utc_str()

    parts = [name, mode]

    if period:
        parts.append(period)

    parts.append(date_str)

    return "_".join(parts).replace("/", "-").replace("\\", "-")


def get_cache_paths(
    name: str,
    mode: str = "demo",
    period: str | None = None,
    subdir: str = DEFAULT_CACHE_SUBDIR,
    date_str: str | None = None,
) -> dict[str, Path]:
    """
    Return CSV and metadata paths for a cache entry.
    """

    cache_dir = get_cache_dir(mode=mode, subdir=subdir)
    cache_key = build_cache_key(
        name=name,
        mode=mode,
        period=period,
        date_str=date_str,
    )

    return {
        "csv": cache_dir / f"{cache_key}.csv",
        "metadata": cache_dir / f"{cache_key}.json",
    }


def save_dataframe_cache(
    df: pd.DataFrame,
    name: str,
    mode: str = "demo",
    period: str | None = None,
    subdir: str = DEFAULT_CACHE_SUBDIR,
    metadata: dict[str, Any] | None = None,
) -> dict[str, str]:
    """
    Save a dataframe and metadata to cache.

    Parameters
    ----------
    df:
        DataFrame to save.
    name:
        Logical cache name.
    mode:
        Either "demo" or "real".
    period:
        Optional period label.
    subdir:
        Cache subdirectory.
    metadata:
        Optional metadata dictionary.

    Returns
    -------
    dict[str, str]
        Paths to created files.
    """

    paths = get_cache_paths(
        name=name,
        mode=mode,
        period=period,
        subdir=subdir,
    )

    df.to_csv(paths["csv"], index=False, encoding="utf-8-sig")

    cache_metadata = {
        "name": name,
        "mode": mode,
        "period": period,
        "subdir": subdir,
        "created_at": utc_now_iso(),
        "rows": int(len(df)),
        "columns": list(df.columns),
    }

    if metadata:
        cache_metadata.update(metadata)

    with open(paths["metadata"], "w", encoding="utf-8") as file:
        json.dump(cache_metadata, file, indent=2, ensure_ascii=False)

    return {
        "csv": str(paths["csv"]),
        "metadata": str(paths["metadata"]),
    }


def cache_exists(
    name: str,
    mode: str = "demo",
    period: str | None = None,
    subdir: str = DEFAULT_CACHE_SUBDIR,
    date_str: str | None = None,
) -> bool:
    """
    Return whether a cache entry exists.
    """

    paths = get_cache_paths(
        name=name,
        mode=mode,
        period=period,
        subdir=subdir,
        date_str=date_str,
    )

    return paths["csv"].exists() and paths["metadata"].exists()


def load_dataframe_cache(
    name: str,
    mode: str = "demo",
    period: str | None = None,
    subdir: str = DEFAULT_CACHE_SUBDIR,
    date_str: str | None = None,
) -> pd.DataFrame:
    """
    Load a cached dataframe.

    Raises
    ------
    FileNotFoundError
        If the cache file does not exist.
    """

    paths = get_cache_paths(
        name=name,
        mode=mode,
        period=period,
        subdir=subdir,
        date_str=date_str,
    )

    if not paths["csv"].exists():
        raise FileNotFoundError(f"Cache CSV not found: {paths['csv']}")

    return pd.read_csv(paths["csv"])


def load_cache_metadata(
    name: str,
    mode: str = "demo",
    period: str | None = None,
    subdir: str = DEFAULT_CACHE_SUBDIR,
    date_str: str | None = None,
) -> dict[str, Any]:
    """
    Load cached metadata.

    Raises
    ------
    FileNotFoundError
        If the metadata file does not exist.
    """

    paths = get_cache_paths(
        name=name,
        mode=mode,
        period=period,
        subdir=subdir,
        date_str=date_str,
    )

    if not paths["metadata"].exists():
        raise FileNotFoundError(f"Cache metadata not found: {paths['metadata']}")

    with open(paths["metadata"], "r", encoding="utf-8") as file:
        return json.load(file)


def save_market_snapshot_cache(
    df: pd.DataFrame,
    mode: str = "demo",
    period: str = "1y",
    metadata: dict[str, Any] | None = None,
) -> dict[str, str]:
    """
    Save a market snapshot dataframe to cache.
    """

    return save_dataframe_cache(
        df=df,
        name="market_snapshot",
        mode=mode,
        period=period,
        subdir=DEFAULT_CACHE_SUBDIR,
        metadata=metadata,
    )


def load_market_snapshot_cache(
    mode: str = "demo",
    period: str = "1y",
    date_str: str | None = None,
) -> pd.DataFrame:
    """
    Load a cached market snapshot dataframe.
    """

    return load_dataframe_cache(
        name="market_snapshot",
        mode=mode,
        period=period,
        subdir=DEFAULT_CACHE_SUBDIR,
        date_str=date_str,
    )


def market_snapshot_cache_exists(
    mode: str = "demo",
    period: str = "1y",
    date_str: str | None = None,
) -> bool:
    """
    Return whether a cached market snapshot exists.
    """

    return cache_exists(
        name="market_snapshot",
        mode=mode,
        period=period,
        subdir=DEFAULT_CACHE_SUBDIR,
        date_str=date_str,
    )


def list_cache_files(
    mode: str = "demo",
    subdir: str | None = None,
) -> pd.DataFrame:
    """
    List cache files for a mode.

    Parameters
    ----------
    mode:
        Either "demo" or "real".
    subdir:
        Optional cache subdirectory.

    Returns
    -------
    pandas.DataFrame
        Cache files with basic metadata.
    """

    if mode not in {"demo", "real"}:
        raise ValueError("Invalid mode. Expected 'demo' or 'real'.")

    paths = get_paths(mode)

    if "cache_dir" in paths:
        cache_root = Path(paths["cache_dir"])
    else:
        cache_root = Path("data") / "cache" / mode

    if subdir:
        search_root = cache_root / subdir
    else:
        search_root = cache_root

    if not search_root.exists():
        return pd.DataFrame(
            columns=["path", "name", "suffix", "size_bytes", "modified_at"]
        )

    rows = []

    for file_path in search_root.rglob("*"):
        if not file_path.is_file():
            continue

        stat = file_path.stat()
        rows.append(
            {
                "path": str(file_path),
                "name": file_path.name,
                "suffix": file_path.suffix,
                "size_bytes": int(stat.st_size),
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime,
                    tz=timezone.utc,
                ).isoformat(timespec="seconds"),
            }
        )

    return pd.DataFrame(rows).sort_values(
        by="modified_at",
        ascending=False,
    ).reset_index(drop=True)


def clear_cache(
    mode: str = "demo",
    subdir: str | None = None,
    suffixes: tuple[str, ...] = (".csv", ".json"),
) -> int:
    """
    Delete cache files for a mode.

    Parameters
    ----------
    mode:
        Either "demo" or "real".
    subdir:
        Optional cache subdirectory.
    suffixes:
        File suffixes to delete.

    Returns
    -------
    int
        Number of deleted files.
    """

    files_df = list_cache_files(mode=mode, subdir=subdir)

    if files_df.empty:
        return 0

    deleted = 0

    for _, row in files_df.iterrows():
        file_path = Path(row["path"])

        if file_path.suffix not in suffixes:
            continue

        file_path.unlink()
        deleted += 1

    return deleted


if __name__ == "__main__":
    from src.market_data import build_market_snapshot
    from src.universe import validate_and_load_universe

    mode = "demo"
    period = "1y"

    print("Cache status before demo:")
    print(f"- market_snapshot cache exists: {market_snapshot_cache_exists(mode=mode, period=period)}")

    universe_df, universe_summary = validate_and_load_universe(mode=mode)

    print("\nUniverse summary:")
    for key, value in universe_summary.items():
        print(f"- {key}: {value}")

    print("\nBuilding market snapshot and saving cache...")
    snapshot_df = build_market_snapshot(universe_df, period=period)

    saved_paths = save_market_snapshot_cache(
        snapshot_df,
        mode=mode,
        period=period,
        metadata={
            "source": "src.cache console demo",
            "universe_size": universe_summary["total_companies"],
        },
    )

    print("\nSaved cache files:")
    for key, value in saved_paths.items():
        print(f"- {key}: {value}")

    print("\nCache metadata:")
    metadata = load_cache_metadata(
        name="market_snapshot",
        mode=mode,
        period=period,
        subdir=DEFAULT_CACHE_SUBDIR,
    )
    for key, value in metadata.items():
        if key == "columns":
            print(f"- {key}: {len(value)} columns")
        else:
            print(f"- {key}: {value}")

    loaded_df = load_market_snapshot_cache(mode=mode, period=period)

    print("\nLoaded cached snapshot:")
    print(f"- rows: {len(loaded_df)}")
    print(f"- columns: {len(loaded_df.columns)}")
    print(f"- first_5_tickers: {loaded_df['ticker'].head(5).tolist() if 'ticker' in loaded_df.columns else []}")

    print("\nCache files:")
    cache_files_df = list_cache_files(mode=mode, subdir=DEFAULT_CACHE_SUBDIR)
    if cache_files_df.empty:
        print("No cache files found.")
    else:
        columns_to_show = ["name", "suffix", "size_bytes", "modified_at"]
        print(cache_files_df[columns_to_show].to_string(index=False))
