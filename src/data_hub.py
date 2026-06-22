from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_SCOUTING_DIR = PROJECT_ROOT / "outputs" / "scouting"
DATA_CACHE_DIR = PROJECT_ROOT / "data" / "cache"

DEFAULT_DATA_MODE = "local_only"
ALLOWED_DATA_MODES = {"local_only", "audit_only"}


@dataclass(frozen=True)
class DataSourceRecord:
    source_id: str
    source_type: str
    path: str
    exists: bool
    ticker: Optional[str]
    source: str
    as_of_date: Optional[str]
    fetched_at: Optional[str]
    dataset_version: str
    cache_key: str
    size_bytes: Optional[int]
    sha256: Optional[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def get_data_mode() -> str:
    mode = os.getenv("SCOUT_FINANCE_DATA_MODE", DEFAULT_DATA_MODE).strip().lower() or DEFAULT_DATA_MODE
    if mode not in ALLOWED_DATA_MODES:
        return DEFAULT_DATA_MODE
    return mode


def is_local_only() -> bool:
    return get_data_mode() in {"local_only", "audit_only"}


def ensure_no_external_fetch() -> Dict[str, Any]:
    return {
        "data_mode": get_data_mode(),
        "external_fetch_allowed": False,
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "network_called": False,
    }


def sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_cache_key(
    *,
    ticker: Optional[str],
    source: str,
    as_of_date: Optional[str],
    dataset_version: str,
    path: Optional[str] = None,
) -> str:
    raw = json.dumps(
        {
            "ticker": ticker or "",
            "source": source,
            "as_of_date": as_of_date or "",
            "dataset_version": dataset_version,
            "path": path or "",
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def infer_ticker_from_name(path: Path) -> Optional[str]:
    stem = path.stem.upper()
    parts = stem.replace("-", "_").split("_")
    for part in parts:
        if 1 <= len(part) <= 6 and part.isalnum() and part.isupper() and not part.isdigit():
            if part not in {"CSV", "JSON", "MD", "TOP", "PHASE", "AUDIT", "REPORT", "INDEX"}:
                return part
    return None


def make_source_record(
    path: Path,
    *,
    source_type: str,
    source: str,
    dataset_version: str,
    ticker: Optional[str] = None,
    as_of_date: Optional[str] = None,
    fetched_at: Optional[str] = None,
) -> DataSourceRecord:
    abs_path = path if path.is_absolute() else PROJECT_ROOT / path
    rel = str(abs_path.relative_to(PROJECT_ROOT)) if abs_path.exists() else str(path)
    detected_ticker = ticker or infer_ticker_from_name(abs_path)
    cache_key = build_cache_key(
        ticker=detected_ticker,
        source=source,
        as_of_date=as_of_date,
        dataset_version=dataset_version,
        path=rel,
    )
    return DataSourceRecord(
        source_id=cache_key[:16],
        source_type=source_type,
        path=rel,
        exists=abs_path.exists(),
        ticker=detected_ticker,
        source=source,
        as_of_date=as_of_date,
        fetched_at=fetched_at,
        dataset_version=dataset_version,
        cache_key=cache_key,
        size_bytes=abs_path.stat().st_size if abs_path.exists() and abs_path.is_file() else None,
        sha256=sha256_file(abs_path),
    )


def discover_local_sources(
    *,
    dataset_version: str = "phase9b_minimal_datahub_v0_1",
    include_outputs: bool = True,
    include_stage_data: bool = True,
) -> List[DataSourceRecord]:
    records: List[DataSourceRecord] = []

    if include_outputs and OUTPUTS_SCOUTING_DIR.exists():
        for path in OUTPUTS_SCOUTING_DIR.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".json", ".csv", ".md"}:
                source_type = path.suffix.lower().lstrip(".")
                records.append(
                    make_source_record(
                        path,
                        source_type=source_type,
                        source="outputs/scouting",
                        dataset_version=dataset_version,
                    )
                )

    if include_stage_data:
        stages_dir = PROJECT_ROOT / "data" / "stages"
        if stages_dir.exists():
            for path in stages_dir.rglob("*.csv"):
                records.append(
                    make_source_record(
                        path,
                        source_type="csv",
                        source="data/stages",
                        dataset_version=dataset_version,
                    )
                )

    return sorted(records, key=lambda r: (r.source, r.path))


def records_to_dicts(records: Iterable[DataSourceRecord]) -> List[Dict[str, Any]]:
    return [asdict(record) for record in records]


def write_source_manifest(path: Path, records: Iterable[DataSourceRecord]) -> Dict[str, Any]:
    record_dicts = records_to_dicts(records)
    payload = {
        "created_at": utc_now(),
        "data_mode": get_data_mode(),
        "external_fetch_allowed": False,
        "record_count": len(record_dicts),
        "records": record_dicts,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def write_source_manifest_csv(path: Path, records: Iterable[DataSourceRecord]) -> None:
    rows = records_to_dicts(records)
    fields = [
        "source_id",
        "source_type",
        "path",
        "exists",
        "ticker",
        "source",
        "as_of_date",
        "fetched_at",
        "dataset_version",
        "cache_key",
        "size_bytes",
        "sha256",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def load_local_json(path: Path) -> Any:
    guard = ensure_no_external_fetch()
    if guard["external_fetch_allowed"]:
        raise RuntimeError("External fetch is not allowed in DataHub local mode.")
    abs_path = path if path.is_absolute() else PROJECT_ROOT / path
    return json.loads(abs_path.read_text(encoding="utf-8"))


def load_local_csv_rows(path: Path) -> List[Dict[str, str]]:
    guard = ensure_no_external_fetch()
    if guard["external_fetch_allowed"]:
        raise RuntimeError("External fetch is not allowed in DataHub local mode.")
    abs_path = path if path.is_absolute() else PROJECT_ROOT / path
    with abs_path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))
