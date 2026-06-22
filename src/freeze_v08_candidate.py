from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PHASE = "V0.8_FREEZE"
VERSION = "v0.8.0-candidate"
BASELINE_VERSION = "v0.7.0-candidate"
DEFAULT_TOP_N = 3


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_excluded(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = set(rel.parts)

    excluded_dirs = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
    }
    if parts & excluded_dirs:
        return True

    name = path.name.lower()
    if name.endswith((".pyc", ".pyo", ".tmp", ".log")):
        return True

    # Do not repackage old release ZIPs inside the new ZIP.
    if rel.parts and rel.parts[0] == "releases" and name.endswith(".zip"):
        return True

    return False


def collect_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and not is_excluded(path, root):
            files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(root)).lower())


def build_manifest(root: Path, files: List[Path]) -> Dict[str, Any]:
    records = []
    for path in files:
        rel = str(path.relative_to(root))
        records.append({
            "relative_path": rel,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return {
        "version": VERSION,
        "baseline_version": BASELINE_VERSION,
        "created_at": utc_iso(),
        "file_count": len(records),
        "files": records,
    }


def validate_prerequisites(root: Path) -> Dict[str, Any]:
    out = root / "outputs" / "scouting"
    j_summary = read_json(out / "phase8j_v08_candidate_audit_summary.json", {})
    j_decision = read_json(out / "phase8j_v08_candidate_readiness_decision.json", {})
    v07_lock = root / "releases" / "RELEASE_LOCK_v0.7.json"
    v07_zip = root / "releases" / "Scout_Finance_v0.7.0_candidate_FREEZE.zip"

    blockers = []
    warnings = []

    if j_summary.get("phase") != "8J":
        blockers.append("8J summary missing or invalid")
    if j_summary.get("status") != "OK":
        blockers.append("8J summary status is not OK")
    if j_summary.get("readiness") != "ready_for_v0_8_candidate":
        blockers.append("8J readiness is not ready_for_v0_8_candidate")
    if j_summary.get("blockers_count") != 0:
        blockers.append("8J blockers_count is not 0")
    if j_summary.get("warnings_count") != 0:
        warnings.append("8J warnings_count is not 0")
    if j_decision.get("readiness") != "ready_for_v0_8_candidate":
        blockers.append("8J readiness decision is not ready")
    if not v07_lock.exists():
        warnings.append("v0.7 RELEASE_LOCK_v0.7.json not found")
    if not v07_zip.exists():
        warnings.append("v0.7 frozen ZIP not found")

    for key in ["openai_called", "api_called", "yfinance_called", "pipeline_recalculated", "app_modified", "filters_modified", "release_modified"]:
        if j_summary.get(key) is not False:
            blockers.append(f"Unsafe 8J control flag: {key}={j_summary.get(key)}")

    return {
        "status": "OK" if not blockers else "BLOCKED",
        "blockers": blockers,
        "warnings": warnings,
        "v07_lock_exists": v07_lock.exists(),
        "v07_zip_exists": v07_zip.exists(),
        "j_summary": str(out / "phase8j_v08_candidate_audit_summary.json"),
        "j_decision": str(out / "phase8j_v08_candidate_readiness_decision.json"),
    }


def write_freeze_report(path: Path, freeze_meta: Dict[str, Any], prereq: Dict[str, Any]) -> None:
    lines = [
        "# Scout Finance v0.8.0-candidate FREEZE REPORT",
        "",
        f"- Version: `{VERSION}`",
        f"- Baseline: `{BASELINE_VERSION}`",
        f"- Created at: `{freeze_meta['created_at']}`",
        f"- ZIP: `{freeze_meta['zip_path']}`",
        f"- ZIP SHA256: `{freeze_meta['zip_sha256']}`",
        f"- Manifest: `{freeze_meta['manifest_path']}`",
        "",
        "## Scope",
        "",
        "v0.8 candidate includes:",
        "",
        "- Quantitative ranking pipeline already validated in v0.7.",
        "- Phase 8A dashboard final design.",
        "- Phase 8B AI Equity Research Memo Blueprint.",
        "- Phase 8C deterministic research modules.",
        "- Phase 8D candidate source binding.",
        "- Phase 8E equity research memo persistence.",
        "- Phase 8F research memo export/report layer.",
        "- Phase 8G optional AI interpretation gate and cost guardrails.",
        "- Phase 8H prompt packaging dry-run.",
        "- Phase 8I optional AI execution sandbox.",
        "- Phase 8J v0.8 candidate readiness audit.",
        "",
        "## Hard safety position",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Real AI execution disabled by default.",
        "- TOP N capped at 3.",
        "- No inventar datos.",
        "- Use `data_insufficient` when data is missing.",
        "- This is not financial advice.",
        "",
        "## Prerequisites",
        "",
        f"- Prerequisite status: `{prereq['status']}`",
        f"- v0.7 lock exists: `{prereq['v07_lock_exists']}`",
        f"- v0.7 ZIP exists: `{prereq['v07_zip_exists']}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- {b}" for b in prereq["blockers"]] or ["- None"])
    lines += ["", "## Warnings", ""]
    lines.extend([f"- {w}" for w in prereq["warnings"]] or ["- None"])
    lines += [
        "",
        "## Release decision",
        "",
        "v0.8.0-candidate is frozen as a deterministic, auditable release candidate with AI memo infrastructure prepared but real AI calls disabled by default.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def create_zip(root: Path, files: List[Path], zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, path.relative_to(root))


def main() -> None:
    root = project_root()
    releases = root / "releases"
    releases.mkdir(exist_ok=True)

    prereq = validate_prerequisites(root)
    if prereq["status"] != "OK":
        print("Scout Finance — v0.8.0-candidate freeze")
        print("=" * 92)
        print("Status: BLOCKED")
        for blocker in prereq["blockers"]:
            print(f"BLOCKER: {blocker}")
        raise SystemExit(1)

    stamp = utc_stamp()
    manifest_path = releases / "MANIFEST_v0.8.0_candidate.json"
    lock_path = releases / "RELEASE_LOCK_v0.8.json"
    report_path = releases / "FREEZE_REPORT_v0.8.md"
    zip_path = releases / "Scout_Finance_v0.8.0_candidate_FREEZE.zip"

    # First write a pre-manifest and lock, then collect final files.
    freeze_meta_pre = {
        "version": VERSION,
        "baseline_version": BASELINE_VERSION,
        "created_at": utc_iso(),
        "default_top_n": DEFAULT_TOP_N,
        "ai_execution": "disabled_by_default",
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "pipeline_recalculated": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": False,
        "prerequisites": prereq,
    }
    write_json(lock_path, freeze_meta_pre)

    files = collect_files(root)
    manifest = build_manifest(root, files)
    write_json(manifest_path, manifest)

    # Recollect so manifest and lock are included, but not final zip.
    files = collect_files(root)
    create_zip(root, files, zip_path)
    zip_sha = sha256_file(zip_path)

    freeze_meta = {
        **freeze_meta_pre,
        "zip_path": str(zip_path),
        "zip_sha256": zip_sha,
        "manifest_path": str(manifest_path),
        "lock_path": str(lock_path),
        "freeze_report_path": str(report_path),
        "file_count": len(files),
    }

    write_json(lock_path, freeze_meta)
    write_freeze_report(report_path, freeze_meta, prereq)

    # Final manifest and ZIP include final report/lock.
    files = collect_files(root)
    manifest = build_manifest(root, files)
    write_json(manifest_path, manifest)
    files = collect_files(root)
    create_zip(root, files, zip_path)
    zip_sha = sha256_file(zip_path)
    freeze_meta["zip_sha256"] = zip_sha
    freeze_meta["file_count"] = len(files)
    write_json(lock_path, freeze_meta)
    write_freeze_report(report_path, freeze_meta, prereq)

    # Final final ZIP includes latest lock/report.
    files = collect_files(root)
    manifest = build_manifest(root, files)
    write_json(manifest_path, manifest)
    files = collect_files(root)
    create_zip(root, files, zip_path)
    zip_sha = sha256_file(zip_path)
    freeze_meta["zip_sha256"] = zip_sha
    freeze_meta["file_count"] = len(files)
    write_json(lock_path, freeze_meta)
    write_freeze_report(report_path, freeze_meta, prereq)

    print("Scout Finance — v0.8.0-candidate freeze")
    print("=" * 92)
    print()
    print("Freeze")
    print("-" * 92)
    print("Status: OK")
    print(f"Version: {VERSION}")
    print(f"Baseline: {BASELINE_VERSION}")
    print(f"ZIP: {zip_path}")
    print(f"ZIP SHA256: {zip_sha}")
    print(f"Files packaged: {len(files)}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Scout Finance v0.8.0-candidate freeze is complete.")


if __name__ == "__main__":
    main()
