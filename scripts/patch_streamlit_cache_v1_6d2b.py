from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


HELPER_MARKER = "# >>> v1.6D2B STREAMLIT CACHE FOR CSV JSON READS"


HELPERS = r'''
# >>> v1.6D2B STREAMLIT CACHE FOR CSV JSON READS
def _sf16d2b_file_mtime(path: Path) -> float:
    """Return file mtime for Streamlit cache invalidation."""
    try:
        return float(path.stat().st_mtime)
    except OSError:
        return 0.0


@st.cache_data(show_spinner=False)
def _sf16d2b_cached_read_text(path_str: str, mtime: float) -> str:
    """Cached text reader. mtime is part of the cache key."""
    return Path(path_str).read_text(encoding="utf-8", errors="replace")


@st.cache_data(show_spinner=False)
def _sf16d2b_cached_read_json(path_str: str, mtime: float) -> dict:
    """Cached JSON reader. mtime is part of the cache key."""
    text = Path(path_str).read_text(encoding="utf-8", errors="replace")
    return json.loads(text)


@st.cache_data(show_spinner=False)
def _sf16d2b_cached_read_csv(path_str: str, mtime: float, nrows: int | None = None) -> pd.DataFrame:
    """Cached CSV reader. mtime is part of the cache key."""
    if nrows is None:
        return pd.read_csv(path_str)
    return pd.read_csv(path_str, nrows=nrows)


def _sf16d2b_read_text(path: Path) -> str:
    return _sf16d2b_cached_read_text(str(path), _sf16d2b_file_mtime(path))


def _sf16d2b_read_json(path: Path) -> dict:
    return _sf16d2b_cached_read_json(str(path), _sf16d2b_file_mtime(path))


def _sf16d2b_read_csv(path: Path, nrows: int | None = None) -> pd.DataFrame:
    return _sf16d2b_cached_read_csv(str(path), _sf16d2b_file_mtime(path), nrows)
# <<< v1.6D2B STREAMLIT CACHE FOR CSV JSON READS
'''


def main() -> int:
    text = APP.read_text(encoding="utf-8")

    if "# v1.6D2B streamlit cache csv json reads packaged" not in text:
        text = "# v1.6D2B streamlit cache csv json reads packaged\n" + text

    if HELPER_MARKER not in text:
        needle = "def _read_text_file(path: Path) -> str:\n"
        idx = text.find(needle)
        if idx == -1:
            raise RuntimeError("Could not find _read_text_file() anchor")
        text = text[:idx] + HELPERS.strip() + "\n\n" + text[idx:]

    replacements = {
        'return path.read_text(encoding="utf-8", errors="replace")':
            'return _sf16d2b_read_text(path)',

        'summary = json.loads(summary_path.read_text(encoding="utf-8"))':
            'summary = _sf16d2b_read_json(summary_path)',

        'data = json.loads(path.read_text(encoding="utf-8"))':
            'data = _sf16d2b_read_json(path)',

        'return json.loads(path.read_text(encoding="utf-8"))':
            'return _sf16d2b_read_json(path)',

        '_sf7c1 = json.loads(_sf7c1_summary_path.read_text(encoding="utf-8"))':
            '_sf7c1 = _sf16d2b_read_json(_sf7c1_summary_path)',

        'df = pd.read_csv(candidates_path)':
            'df = _sf16d2b_read_csv(candidates_path)',

        'rows = int(len(pd.read_csv(candidates_path)))':
            'rows = int(len(_sf16d2b_read_csv(candidates_path)))',

        'df = pd.read_csv(path)':
            'df = _sf16d2b_read_csv(path)',

        'return pd.read_csv(path)':
            'return _sf16d2b_read_csv(path)',

        'df = pd.read_csv(paths["input"])':
            'df = _sf16d2b_read_csv(paths["input"])',

        'df = pd.read_csv(scored_path)':
            'df = _sf16d2b_read_csv(scored_path)',

        'df = pd.read_csv(enriched_path)':
            'df = _sf16d2b_read_csv(enriched_path)',

        'active_df = pd.read_csv(active_path, nrows=5)':
            'active_df = _sf16d2b_read_csv(active_path, nrows=5)',

        'return int(len(pd.read_csv(path)))':
            'return int(len(_sf16d2b_read_csv(path)))',
    }

    applied = 0
    for old, new in replacements.items():
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            applied += count

    APP.write_text(text, encoding="utf-8")

    print("Scout Finance ? v1.6D2B Streamlit Cache for CSV/JSON Reads")
    print("=" * 92)
    print(f"OK   app.py updated: {APP}")
    print(f"OK   Replacement applications: {applied}")
    print("OK   Cache invalidation uses file mtime")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
