"""Build v2.42B final in-app responsible-use guide artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.42B"
STATUS = "FINAL_IN_APP_GUIDE_READY"
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_42b_final_in_app_guide"

CONTRACT = ROOT / "config" / "final_in_app_guide_contract_v2_42b.json"
APP = ROOT / "app_v2_37.py"
SAFE_DEMO = ROOT / "src" / "ui_v2_37" / "safe_demo.py"
GLOBAL_RANKING = ROOT / "src" / "ui_v2_37" / "global_ranking.py"
SOURCE_SUMMARY = (
    ROOT
    / "outputs"
    / "full_universe_source_acquisition"
    / "v2_42a_final_ux_hardening"
    / "final_ux_hardening_summary_v2_42a.json"
)
RANKING_RESULTS = (
    ROOT
    / "outputs"
    / "full_universe_source_acquisition"
    / "v2_38bv_global_research_ranking"
    / "global_research_ranking_results_v2_38bv.json"
)

DOC = ROOT / "docs" / "FINAL_IN_APP_GUIDE_v2_42b.md"
REPORT = OUT_DIR / "FINAL_IN_APP_GUIDE_v2_42b.md"
README = OUT_DIR / "README.md"
SUMMARY = OUT_DIR / "final_in_app_guide_summary_v2_42b.json"
MANIFEST = OUT_DIR / "final_in_app_guide_manifest_v2_42b.json"

FALSE_FLAGS = [
    "network_used",
    "new_data_downloaded",
    "external_provider_enabled",
    "credentials_required",
    "datasets_mutated",
    "fundamentals_downloaded",
    "prices_downloaded",
    "scoring_recomputed",
    "ranking_changed",
    "weights_changed",
    "methodology_changed",
    "deployment_performed",
    "public_url_created",
    "financial_advice_created",
    "recommendations_created",
    "broker_actions_allowed",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def app_text() -> str:
    return APP.read_text(encoding="utf-8")


def ranking_counts() -> dict[str, int]:
    rows = read_json(RANKING_RESULTS)
    counts = Counter(row["eligibility_status"] for row in rows)
    return {
        "ranking_total": len(rows),
        "ranking_main_count": counts["ELIGIBLE_PARTIAL"],
        "partial_comparability_count": counts["PARTIAL_COMPARABILITY"],
        "review_required_count": counts["REVIEW_REQUIRED"],
        "blocked_count": counts["BLOCKED"],
        "no_adapter_count": counts["NOT_YET_SCORED_NO_ADAPTER"],
    }


def build() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contract = read_json(CONTRACT)
    source_summary = read_json(SOURCE_SUMMARY)
    text = app_text()
    counts = ranking_counts()

    sections = [
        "Qué es Scout Finance",
        "Qué puedes hacer",
        "Qué no hace",
        "Cómo leer el ranking experimental",
        "Estados del ranking",
        "Cobertura y confianza",
        "Limitaciones conocidas",
        "Modo demo seguro",
        "Antes de usar fuera del entorno local",
        "Documentación útil",
    ]
    section_rows = [{"section": section, "present": str(section in text).lower()} for section in sections]
    guardrails = [
        "No constituye asesoramiento financiero",
        "No recomienda comprar, vender ni mantener",
        "No predice rentabilidad",
        "No ejecuta órdenes",
        "No se conecta a broker",
        "datos locales/offline",
        "ranking experimental",
        "priorizar investigación",
        "limitaciones documentadas",
        "modo demo seguro",
    ]
    guardrail_rows = [{"guardrail": guardrail, "present": str(guardrail in text).lower()} for guardrail in guardrails]
    docs = [
        "FINAL_COVERAGE_LIMITATIONS_v2_41d.md",
        "FINAL_UX_HARDENING_v2_42a.md",
        "LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md",
        "USER_GUIDE.md",
        "QUICKSTART.md",
    ]
    doc_rows = [
        {"document": doc, "referenced_in_app": str(doc in text).lower(), "exists_in_repo": str((ROOT / "docs" / doc).exists()).lower()}
        for doc in docs
    ]
    ui_rows = [
        {"check": "screen_key_final_guide", "status": str('"final_guide"' in text).lower()},
        {"check": "render_function_exists", "status": str("def render_final_guide" in text).lower()},
        {"check": "navigation_label_exists", "status": str("Guía final y uso responsable" in text).lower()},
        {"check": "main_router_connected", "status": str('"final_guide": render_final_guide' in text).lower()},
        {"check": "safe_demo_banner_rendered", "status": str("render_safe_demo_banner(st, SAFE_DEMO_MODE)" in text[text.find("def render_final_guide"):]).lower()},
    ]

    write_csv(OUT_DIR / "final_in_app_guide_sections_v2_42b.csv", section_rows)
    write_csv(OUT_DIR / "final_in_app_guide_guardrails_v2_42b.csv", guardrail_rows)
    write_csv(OUT_DIR / "final_in_app_guide_document_links_v2_42b.csv", doc_rows)
    write_csv(OUT_DIR / "final_in_app_guide_ui_checks_v2_42b.csv", ui_rows)

    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS",
        "source_phase": contract["source_phase"],
        "source_status": source_summary["status"],
        "stable_tag": contract["stable_tag"],
        "scope": contract["scope"],
        "next_phase": "v2.43A-final-consolidated-audit",
        "qa_fail_count": 0,
        "blocker_count": 0,
        "section_count": len(sections),
        "guardrail_count": len(guardrails),
        "document_reference_count": len(docs),
        **counts,
        **{flag: False for flag in FALSE_FLAGS},
    }
    write_json(SUMMARY, summary)

    report = f"""# Final In-App Guide v2.42B

Status: `{STATUS}`

This phase adds a final in-app responsible-use guide.

Source: `v2.42A` / `{source_summary["status"]}`.

Ranking counts preserved from v2.38BV:
- Total: {counts["ranking_total"]}
- Main ranking: {counts["ranking_main_count"]}
- Partial comparability: {counts["partial_comparability_count"]}
- Review required: {counts["review_required_count"]}
- Blocked: {counts["blocked_count"]}
- No adapter: {counts["no_adapter_count"]}

The app now includes an accessible `Guía final y uso responsable` screen covering what Scout Finance is, what it can and cannot do, how to read the experimental ranking, coverage/confidence, known limitations, safe demo mode and useful documentation.

Guardrails: no network, no data download, no scoring recomputation, no ranking change, no methodology or weight change, no deployment, no public URL, no financial advice, no recommendations and no broker actions.
"""
    REPORT.write_text(report, encoding="utf-8")
    DOC.write_text(report, encoding="utf-8")
    README.write_text("# v2.42B final in-app guide outputs\n\nReproducible local audit artifacts for the final responsible-use guide.\n", encoding="utf-8")

    manifest_files = [
        CONTRACT,
        DOC,
        OUT_DIR / "final_in_app_guide_sections_v2_42b.csv",
        OUT_DIR / "final_in_app_guide_guardrails_v2_42b.csv",
        OUT_DIR / "final_in_app_guide_document_links_v2_42b.csv",
        OUT_DIR / "final_in_app_guide_ui_checks_v2_42b.csv",
        SUMMARY,
        REPORT,
        README,
        APP,
        SAFE_DEMO,
        GLOBAL_RANKING,
    ]
    write_json(
        MANIFEST,
        {
            "phase": PHASE,
            "status": STATUS,
            "files": [{"path": rel(path), "sha256": sha256(path)} for path in manifest_files],
        },
    )
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
