#!/usr/bin/env python3
"""v2.39C security and sensitive files audit builder."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.39C-security-sensitive-files-audit"
CONTRACT = ROOT / "config/security_sensitive_files_audit_contract_v2_39c.json"
SOURCE_SUMMARY = ROOT / "outputs/full_universe_source_acquisition/v2_39b_public_documentation_cleanup/public_documentation_cleanup_summary_v2_39b.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39c_security_sensitive_files_audit"

GUARDRAILS = {
    "network_used": False,
    "datasets_mutated": False,
    "scoring_recomputed": False,
    "weights_changed": False,
    "ranking_changed": False,
    "methodology_changed": False,
    "ui_changed": False,
    "financial_advice_created": False,
    "broker_actions_allowed": False,
    "tag_created": False,
    "github_release_created": False,
}

TEXT_EXTENSIONS = {
    ".bat", ".cfg", ".csv", ".css", ".html", ".ini", ".js", ".json", ".lock",
    ".md", ".ps1", ".py", ".rst", ".sh", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml",
}
SENSITIVE_EXTENSIONS = {".env", ".pem", ".key", ".p12", ".pfx", ".crt", ".sqlite", ".db", ".docx", ".xlsx", ".zip", ".parquet", ".pkl"}
PLACEHOLDER_RE = re.compile(r"(your_|example|dummy|placeholder|redacted|<[^>]+>|xxxx|changeme|google_maps_api_key)", re.IGNORECASE)
PATTERNS = [
    ("PRIVATE-KEY", "private_keys", "BLOCKER", re.compile(r"BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY")),
    ("EMBEDDED-CREDENTIAL-URL", "secrets", "BLOCKER", re.compile(r"https?://[^/\s:@]+:[^/\s:@]+@")),
    ("GENERIC-API-KEY", "api_keys", "WARN", re.compile(r"\b[A-Z0-9_]*(API[_-]?KEY|SECRET[_-]?KEY)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,})", re.IGNORECASE)),
    ("GENERIC-TOKEN", "tokens", "WARN", re.compile(r"\b[A-Z0-9_]*(TOKEN|SECRET)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-.]{20,})", re.IGNORECASE)),
    ("GENERIC-PASSWORD", "passwords", "WARN", re.compile(r"\b(PASSWORD|PASSWD|PWD)\b\s*[:=]\s*['\"]?([^'\"\s]{8,})", re.IGNORECASE)),
    ("WINDOWS-USER-PATH", "local_paths", "WARN", re.compile(r"[A-Z]:\\Users\\[^\\\s]+\\", re.IGNORECASE)),
    ("UNIX-USER-PATH", "local_paths", "WARN", re.compile(r"(/Users|/home)/[^/\s]+/")),
    ("EMAIL", "public_documentation_claims", "WARN", re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
]


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def tracked_files() -> list[Path]:
    return [ROOT / line for line in run_git(["ls-files"]).splitlines() if line]


def untracked_files() -> list[Path]:
    return [ROOT / line for line in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines() if line]


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {".gitignore", "Dockerfile", "requirements.txt"}


def text_or_empty(path: Path) -> str:
    rpath = rel(path)
    scan_prefixes = ("app", "config/", "docs/", "scripts/", "src/", "tests/")
    scan_root_docs = {"README.md", "VERSION.md", "CHANGELOG.md", "ROADMAP_v2_38_CURRENT.md", ".gitignore"}
    if not (rpath.startswith(scan_prefixes) or rpath in scan_root_docs):
        return ""
    if not is_text_file(path):
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def add_row(rows: list[dict[str, Any]], check_id: str, category: str, severity: str, status: str, path: str, evidence: str, remediation: str) -> None:
    rows.append({
        "check_id": check_id,
        "category": category,
        "severity": severity,
        "status": status,
        "path": path,
        "evidence": evidence,
        "remediation": remediation,
    })


def scan_files(contract: dict[str, Any], files: list[Path], untracked: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    per_file_counts: dict[tuple[str, str], int] = {}
    for path in files:
        rpath = rel(path)
        suffix = path.suffix.lower()
        size = path.stat().st_size if path.exists() else 0
        if suffix in SENSITIVE_EXTENSIONS:
            severity = "WARN"
            status = "WARN"
            if suffix in {".env", ".pem", ".key", ".p12", ".pfx"}:
                severity = status = "BLOCKER"
            add_row(rows, f"EXT-{suffix or path.name}", "sensitive_extensions", severity, status, rpath, f"tracked extension {suffix or path.name}", "Review whether this file belongs in public Git.")
        if size > contract["oversized_file_warning_bytes"]:
            add_row(rows, "SIZE-001", "oversized_files", "WARN", "WARN", rpath, f"{size} bytes", "Confirm the file is intentionally tracked.")
        content = text_or_empty(path)
        if not content:
            continue
        for pattern_id, category, severity, regex in PATTERNS:
            for match in regex.finditer(content):
                snippet = match.group(0)[:120].replace("\n", " ")
                if PLACEHOLDER_RE.search(snippet):
                    continue
                if pattern_id == "EMAIL" and ("codex@openai.com" in snippet or "noreply" in snippet.lower()):
                    continue
                key = (pattern_id, rpath, snippet)
                file_key = (pattern_id, rpath)
                if key in seen or per_file_counts.get(file_key, 0) >= 3:
                    continue
                seen.add(key)
                per_file_counts[file_key] = per_file_counts.get(file_key, 0) + 1
                add_row(rows, pattern_id, category, severity, severity, rpath, snippet, "Review and redact if this is real sensitive information.")
    for category in ["secrets", "api_keys", "tokens", "passwords", "private_keys", "env_files"]:
        has_issue = any(row["category"] == category for row in rows)
        if not has_issue:
            add_row(rows, f"PASS-{category}", category, "PASS", "PASS", ".", f"No {category} blockers found.", "No action required.")
    for path in untracked:
        if OUT in path.parents:
            continue
        add_row(rows, "UNTRACKED-REVIEW", "working_tree_untracked_review", "WARN", "WARN", rel(path), "untracked local file", "Keep out of commit unless it belongs to a scoped phase.")
    return rows


def pattern_rows() -> list[dict[str, Any]]:
    return [
        {"pattern_id": pid, "category": cat, "default_severity": sev, "description": regex.pattern}
        for pid, cat, sev, regex in PATTERNS
    ]


def gitignore_status() -> tuple[str, list[str]]:
    path = ROOT / ".gitignore"
    required = [".env", "__pycache__", ".pytest_cache", ".venv", "venv", "*.tmp", "*.log"]
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    missing = [item for item in required if item not in text]
    return ("PASS" if not missing else "WARN", missing)


def report_md(summary: dict[str, Any], rows: list[dict[str, Any]], missing_gitignore: list[str]) -> str:
    warn_rows = [row for row in rows if row["status"] == "WARN"]
    blocker_rows = [row for row in rows if row["status"] == "BLOCKER"]
    lines = [
        "# Security Sensitive Files Audit v2.39C",
        "",
        f"Decision: `{summary['status']}`.",
        "",
        "This offline audit reviews tracked repository files, relevant untracked local files, sensitive extensions, secret-like patterns, local paths, binary/publication risks and `.gitignore` policy before broader release preparation.",
        "",
        "## Results",
        "",
        f"- Tracked files scanned: {summary['tracked_files_scanned']}",
        f"- Untracked files reviewed: {summary['untracked_files_reviewed']}",
        f"- Patterns checked: {summary['patterns_checked']}",
        f"- PASS rows: {summary['pass_count']}",
        f"- WARN rows: {summary['warn_count']}",
        f"- BLOCKER rows: {summary['blocker_count']}",
        f"- Gitignore policy: `{summary['gitignore_policy_status']}`",
        "",
        "## Guardrails",
        "",
        "No network, scoring, ranking, methodology, weights, dataset mutation, broker workflow, tag creation or GitHub release was performed.",
    ]
    if missing_gitignore:
        lines.extend(["", "## Gitignore Warnings", "", f"Missing recommended patterns: `{', '.join(missing_gitignore)}`."])
    if warn_rows:
        lines.extend(["", "## Warnings Documented", "", "| Path | Category | Evidence | Remediation |", "| --- | --- | --- | --- |"])
        for row in warn_rows[:50]:
            lines.append(f"| `{row['path']}` | {row['category']} | {row['evidence']} | {row['remediation']} |")
    if blocker_rows:
        lines.extend(["", "## Blockers", "", "| Path | Category | Evidence | Remediation |", "| --- | --- | --- | --- |"])
        for row in blocker_rows:
            lines.append(f"| `{row['path']}` | {row['category']} | {row['evidence']} | {row['remediation']} |")
    lines.extend(["", f"Next recommended phase: `{summary['next_recommended_phase']}`.", ""])
    return "\n".join(lines)


def manifest(summary: dict[str, Any], outputs: list[Path]) -> dict[str, Any]:
    return {
        "phase": PHASE,
        "status": summary["status"],
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"]).strip(),
        "source_commit": run_git(["rev-parse", "--short", "HEAD"]).strip(),
        "stable_tag": summary["stable_tag"],
        "inputs": {
            rel(CONTRACT): {"bytes": CONTRACT.stat().st_size, "sha256": sha256(CONTRACT)},
            rel(SOURCE_SUMMARY): {"bytes": SOURCE_SUMMARY.stat().st_size, "sha256": sha256(SOURCE_SUMMARY)},
        },
        "outputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in outputs if path.exists()},
        "guardrails": GUARDRAILS,
        "network_used": False,
        "scoring_recomputed": False,
        "broker_actions_allowed": False,
        "github_release_created": False,
    }


def build() -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_SUMMARY.read_text(encoding="utf-8"))
    files = tracked_files()
    untracked = untracked_files()
    rows = scan_files(contract, files, untracked)
    gitignore_policy, missing_gitignore = gitignore_status()
    if missing_gitignore:
        add_row(rows, "GITIGNORE-001", "ignored_files_policy", "WARN", "WARN", ".gitignore", ",".join(missing_gitignore), "Add missing ignore patterns in a scoped future cleanup if needed.")
    pass_count = sum(row["status"] == "PASS" for row in rows)
    warn_count = sum(row["status"] == "WARN" for row in rows)
    blocker_count = sum(row["status"] == "BLOCKER" for row in rows)
    summary = {
        "phase": PHASE,
        "status": "SECURITY_SENSITIVE_FILES_AUDIT_READY" if blocker_count == 0 else "SECURITY_SENSITIVE_FILES_AUDIT_BLOCKED",
        "qa_status": "PASS" if blocker_count == 0 else "FAIL",
        "source_phase": contract["source_phase"],
        "source_status": source.get("status"),
        "stable_tag": contract["stable_tag"],
        "publication_scope": contract["publication_scope"],
        "tracked_files_scanned": len(files),
        "untracked_files_reviewed": len([p for p in untracked if OUT not in p.parents]),
        "patterns_checked": len(PATTERNS),
        "pass_count": pass_count,
        "warn_count": warn_count,
        "blocker_count": blocker_count,
        "sensitive_secret_count": sum(row["category"] in {"secrets", "api_keys", "tokens", "passwords"} for row in rows if row["status"] != "PASS"),
        "private_key_count": sum(row["category"] == "private_keys" and row["status"] != "PASS" for row in rows),
        "env_file_count": sum(row["path"].endswith(".env") for row in rows),
        "personal_document_count": sum(row["path"].endswith((".docx", ".xlsx")) for row in rows),
        "oversized_file_warn_count": sum(row["category"] == "oversized_files" for row in rows),
        "gitignore_policy_status": gitignore_policy,
        "next_recommended_phase": contract["next_recommended_phase"],
        **GUARDRAILS,
    }
    matrix_path = OUT / "security_sensitive_files_audit_matrix_v2_39c.csv"
    patterns_path = OUT / "security_sensitive_patterns_v2_39c.csv"
    summary_path = OUT / "security_sensitive_files_summary_v2_39c.json"
    report_path = OUT / "SECURITY_SENSITIVE_FILES_AUDIT_v2_39c.md"
    readme_path = OUT / "README.md"
    write_csv(matrix_path, rows, ["check_id", "category", "severity", "status", "path", "evidence", "remediation"])
    write_csv(patterns_path, pattern_rows(), ["pattern_id", "category", "default_severity", "description"])
    write_json(summary_path, summary)
    write_text(report_path, report_md(summary, rows, missing_gitignore))
    write_text(readme_path, "# v2.39C Security Sensitive Files Audit\n\nOffline security and sensitive-file audit outputs for Scout Finance.\n")
    manifest_path = OUT / "security_sensitive_files_manifest_v2_39c.json"
    outputs = [matrix_path, patterns_path, summary_path, report_path, readme_path]
    write_json(manifest_path, manifest(summary, outputs))
    return summary


def main() -> int:
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
