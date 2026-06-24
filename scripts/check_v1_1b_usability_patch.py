from __future__ import annotations
import json
from pathlib import Path

PHASE = "v1.1B"

def root() -> Path:
    return Path(__file__).resolve().parents[1]

def ok(msg: str) -> None:
    print("OK   " + msg)

def fail(msg: str) -> None:
    print("FAIL " + msg)
    raise SystemExit(1)

def require(condition: bool, msg: str) -> None:
    ok(msg) if condition else fail(msg)

def require_file(path: Path) -> None:
    require(path.exists(), f"File exists: {path}")

def main() -> None:
    r = root()
    out = r / "outputs" / "scouting"
    print("Scout Finance — v1.1B Usability Patch checker")
    print("=" * 92)

    required = [
        r / "docs" / "QUICKSTART.md",
        r / "docs" / "v1" / "V1_1B_USABILITY_PATCH.md",
        r / "scripts" / "check_v1_1b_usability_patch.py",
    ]
    for path in required:
        require_file(path)

    text = (r / "docs" / "QUICKSTART.md").read_text(encoding="utf-8")

    required_terms = [
        "Validar que la versión congelada sigue correcta",
        "Formato general",
        "--ticker TICKER --status ESTADO",
        "Estados permitidos",
        "pending_review",
        "reviewed_watchlist",
        "reviewed_reject",
        "needs_more_data",
        "manual_review_summary.md",
        "final_review_pack.md",
        "Archivos importantes",
        "no es un asesor financiero",
        "bot de trading",
    ]
    for term in required_terms:
        require(term.lower() in text.lower(), f"QUICKSTART contains: {term}")

    summary = {
        "phase": PHASE,
        "title": "Usability Patch",
        "version": "v1.1B-usability-patch",
        "status": "OK",
        "scope": "documentation_only",
        "files": [
            "docs/QUICKSTART.md",
            "docs/v1/V1_1B_USABILITY_PATCH.md",
            "scripts/check_v1_1b_usability_patch.py",
        ],
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "pipeline_recalculated": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": False,
        "next": "v1.1A qualitative review continuation or v1.1C MVP Final Freeze",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "v1_1b_usability_patch_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    report = [
        "# v1.1B — Usability Patch",
        "",
        "Status: **OK**",
        "",
        "Scope: documentation only.",
        "",
        "## Files",
        "",
    ]
    for file in summary["files"]:
        report.append(f"- `{file}`")
    report.extend([
        "",
        "## Safety",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "- No scoring changes.",
        "- No filter changes.",
        "",
    ])
    (out / "v1_1b_usability_patch_report.md").write_text("\\n".join(report), encoding="utf-8")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.1B Usability Patch is valid")

if __name__ == "__main__":
    main()
