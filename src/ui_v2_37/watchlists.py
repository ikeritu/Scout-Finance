"""Private v2.37 watchlists with controlled research states."""
from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "2.0"
STATUSES = ("WATCHLIST", "REJECT", "NEEDS_MORE_DATA", "REVIEW_LATER")
MAX_IMPORT_BYTES = 1_000_000


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    clean = re.sub(r"[^\w-]+", "-", str(value).strip().lower(), flags=re.UNICODE).strip("-")
    return clean[:60] or "watchlist"


def folder(root: Path) -> Path:
    return root.resolve() / "data" / "watchlists"


def validate(data: dict) -> None:
    if data.get("schema_version") != SCHEMA_VERSION or not data.get("watchlist_id") or not data.get("name"):
        raise ValueError("watchlist incompatible or incomplete")
    seen = set()
    for item in data.get("items", []):
        asset_id = item.get("asset_id")
        if not asset_id or asset_id in seen:
            raise ValueError("asset_id missing or duplicated")
        seen.add(asset_id)
        if item.get("research_status") not in STATUSES:
            raise ValueError("invalid research status")
        if any(key in item for key in ("allocation", "target_price", "broker_order")):
            raise ValueError("forbidden trading field")


def create(root: Path, name: str, description: str = "") -> tuple[Path, dict]:
    if not str(name).strip():
        raise ValueError("El nombre es obligatorio")
    path = folder(root) / f"{_slug(name)}.v2_37.json"
    if path.exists():
        raise ValueError("Ya existe una watchlist con ese nombre")
    stamp = now()
    data = {"schema_version": SCHEMA_VERSION, "watchlist_id": str(uuid.uuid4()), "name": str(name).strip(), "description": str(description).strip(), "created_at_utc": stamp, "updated_at_utc": stamp, "items": []}
    atomic_write(path, data)
    return path, data


def atomic_write(path: Path, data: dict) -> None:
    validate(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate(data)
    return data


def scan(root: Path) -> tuple[list[tuple[Path, dict]], list[tuple[Path, str]]]:
    valid, errors = [], []
    for path in sorted(folder(root).glob("*.v2_37.json")) if folder(root).exists() else []:
        try:
            valid.append((path, read(path)))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append((path, str(exc)))
    return valid, errors


def add(data: dict, asset: dict, status: str = "WATCHLIST", note: str = "") -> None:
    if status not in STATUSES:
        raise ValueError("Estado no permitido")
    if any(item["asset_id"] == asset["asset_id"] for item in data["items"]):
        raise ValueError("El activo ya está en esta watchlist")
    data["items"].append({"asset_id": asset["asset_id"], "ticker": asset["ticker"], "company_name": asset["company_name"], "market": asset["market"], "research_status": status, "note": str(note).strip(), "added_at_utc": now()})
    data["updated_at_utc"] = now()
    validate(data)


def update(data: dict, asset_id: str, status: str, note: str) -> None:
    if status not in STATUSES:
        raise ValueError("Estado no permitido")
    item = next((item for item in data["items"] if item["asset_id"] == asset_id), None)
    if not item:
        raise ValueError("Activo no encontrado")
    item.update({"research_status": status, "note": str(note).strip()})
    data["updated_at_utc"] = now()


def remove(data: dict, asset_id: str) -> None:
    data["items"] = [item for item in data["items"] if item["asset_id"] != asset_id]
    data["updated_at_utc"] = now()


def export_csv(data: dict) -> bytes:
    out = io.StringIO(newline="")
    fields = ["asset_id", "ticker", "company_name", "market", "research_status", "note", "added_at_utc"]
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for source in data["items"]:
        row = dict(source)
        for key, value in row.items():
            if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
                row[key] = "'" + value
        writer.writerow({key: row.get(key, "") for key in fields})
    return ("\ufeff" + out.getvalue()).encode("utf-8")


def import_json_bytes(payload: bytes) -> dict:
    if len(payload) > MAX_IMPORT_BYTES:
        raise ValueError("El archivo supera 1 MB")
    data = json.loads(payload.decode("utf-8-sig"))
    validate(data)
    return data
