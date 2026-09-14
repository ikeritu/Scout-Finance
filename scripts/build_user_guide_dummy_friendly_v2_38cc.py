#!/usr/bin/env python3
"""v2.38CC dummy-friendly user guide builder."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38CC-user-guide-dummy-friendly"
CONTRACT = ROOT / "config/user_guide_dummy_friendly_contract_v2_38cc.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cc_user_guide_dummy_friendly"

GUARDRAILS = {
    "scoring_recomputed": False,
    "methodology_changed": False,
    "weights_changed": False,
    "network_used": False,
    "financial_advice_created": False,
    "broker_actions_allowed": False,
    "recommendations_created": False,
}

ADVICE_PATTERNS = [
    r"\bstrong buy\b", r"\bbuy\b", r"\bsell\b", r"\bhold\b",
    r"\btarget price\b", r"\bexpected return\b", r"\bundervalued\b",
    r"\bovervalued\b", r"\bcomprar\b", r"\bvender\b", r"\bmantener\b",
    r"\bprecio objetivo\b", r"\brentabilidad esperada\b",
]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def clean_text(value: str) -> str:
    table = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return value.translate(table).lower()


def has_unnegated_advice(text: str) -> bool:
    normalized = clean_text(text)
    for pattern in ADVICE_PATTERNS:
        for match in re.finditer(pattern, normalized, flags=re.I):
            context = normalized[max(0, match.start() - 64):match.end() + 64]
            if "watchlist" in context:
                continue
            if not re.search(r"\b(no|not|never|nunca|sin|ni|tampoco)\b", context):
                return True
    return False


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def quick_start() -> str:
    return """# User Guide Quick Start v2.38CC

1. Open PowerShell.
2. Go to the project folder: `cd "D:\\Proyectos\\💰 Scout Finance"`.
3. If dependencies are missing, run: `python -m pip install -r requirements.txt`.
4. Start the app: `.\\run_local_ui_v2_37.bat`.
5. Open `http://localhost:8501` if needed.
6. Start with `Inicio` to confirm the app loads.
7. Open `Universo global (43.089)` to see coverage and missing data.
8. Open `Ranking global (experimental)` to review the research ranking.
9. Use search, filters, Top N, quick detail, export CSV and watchlists only as research tools.
10. Remember: this is not financial advice, not a prediction, not a buy/sell/hold signal and not connected to brokers.
"""


def faq() -> str:
    return """# User Guide FAQ v2.38CC

## Que es Scout Finance?
Una app local para investigar empresas con datos ya recolectados y auditados.

## Es una recomendacion de inversion?
No. No es asesoramiento financiero ni una recomendacion de inversion.

## Que significa que el ranking sea experimental?
Significa que ordena investigacion con un score cuantitativo, pero no esta validado como prediccion de rentabilidad futura.

## Que significa el score?
Es una puntuacion relativa calculada antes de abrir la app. Ayuda a priorizar revision, no a decidir operaciones.

## Que significa confianza?
Indica cuanta cobertura y comparabilidad tienen los factores disponibles.

## Que significa cobertura?
Es el porcentaje de factores reales disponibles para una empresa dentro del contrato del ranking.

## Por que algunas empresas estan bloqueadas?
Porque tienen cobertura real insuficiente. No se rellena con datos inventados.

## Por que algunas empresas no tienen adaptador?
Porque esa jurisdiccion todavia no tiene un adaptador real de ratios o crecimiento.

## Por que algunas empresas requieren revision?
Porque necesitan revision humana o un contrato especifico, por ejemplo entidades financieras.

## Puedo usarlo para decidir comprar o vender?
No. No sirve para decidir comprar, vender o mantener. Sirve para ordenar investigacion.

## Que hago si no arranca?
Comprueba que estas en la carpeta correcta, instala dependencias y ejecuta `run_local_ui_v2_37.bat`.

## Que hago si estoy en C:\\Users\\ikeri y Git dice que no es un repositorio?
Ejecuta `cd "D:\\Proyectos\\💰 Scout Finance"` y despues `git status`.

## Que hago si falta Streamlit?
Ejecuta `python -m pip install -r requirements.txt`.

## Que hago si el puerto 8501 esta ocupado?
Cierra el Streamlit anterior o arranca manualmente en otro puerto, por ejemplo `8502`.

## Que significa Google Finance aqui?
Es solo un enlace de consulta manual. Scout Finance no descarga ni procesa datos de Google Finance.

## Que son las watchlists?
Listas privadas locales para guardar empresas que quieres revisar despues.
"""


def guide(summary: dict[str, Any]) -> str:
    return f"""# User Guide Dummy Friendly v2.38CC

## Que es Scout Finance

Scout Finance es una aplicacion local para investigar empresas. Lee datos y resultados que ya existen en tu ordenador y los muestra de forma ordenada.

## Que no es

No es asesoramiento financiero. No predice rentabilidad. No da precio objetivo. No crea senales de comprar, vender o mantener. No se conecta a brokers.

## Arranque rapido

1. Abre PowerShell.
2. Entra en la carpeta: `cd "D:\\Proyectos\\💰 Scout Finance"`.
3. Instala dependencias si hace falta: `python -m pip install -r requirements.txt`.
4. Arranca la app: `.\\run_local_ui_v2_37.bat`.
5. Abre `http://localhost:8501` si el navegador no se abre solo.

## Pantallas principales

- `Inicio`: confirma que la app carga.
- `Universo global (43.089)`: muestra todas las empresas y la cobertura real.
- `Ranking global (experimental)`: muestra el ranking de investigacion.
- `Watchlist`: guarda empresas para revisarlas despues.

## Ranking global experimental

El ranking global experimental ordena empresas para priorizar investigacion. El resultado actual contiene {summary['total_assets']} empresas evaluadas: {summary['main_ranking_count']} en ranking principal, {summary['partial_comparability_count']} con comparabilidad parcial, {summary['review_required_count']} en revision, {summary['blocked_count']} bloqueadas y {summary['not_yet_scored_count']} sin adaptador.

## Score

El score es una puntuacion relativa ya calculada antes de abrir la app. Un score mas alto solo significa mas prioridad de investigacion dentro de este modelo experimental.

## Confianza

La confianza resume la calidad de comparacion. `HIGH` y `MEDIUM` entran en el ranking principal; `LOW` queda separado como comparabilidad parcial.

## Cobertura

La cobertura indica cuantos factores reales existen para una empresa. Si la cobertura es demasiado baja, la empresa queda bloqueada.

## Estados

- `ELIGIBLE_PARTIAL`: aparece en el ranking principal.
- `PARTIAL_COMPARABILITY`: tiene score, pero se separa por menor comparabilidad.
- `REVIEW_REQUIRED`: necesita revision antes de cualquier puntuacion automatica.
- `BLOCKED`: no tiene cobertura suficiente.
- `NOT_YET_SCORED_NO_ADAPTER`: falta un adaptador real para esa jurisdiccion.

## Filtros y exportacion

Puedes buscar por empresa, ticker, ID o pais. Tambien puedes filtrar por pais, confianza, rango de score, rango de cobertura y Top N. El CSV filtrado exporta informacion de investigacion, no datos privados de watchlist.

## Google Finance

El enlace a Google Finance es una ayuda manual. Abre una busqueda para que revises informacion externa por tu cuenta. Scout Finance no descarga datos de Google.

## Watchlists

Las watchlists son listas privadas locales. Sirven para guardar empresas que quieres revisar mas tarde con tus propias notas.

## Limitaciones

Hay paises con cobertura parcial, empresas sin precio real, jurisdicciones sin adaptador, entidades financieras con contrato pendiente y empresas bloqueadas por falta de datos. La herramienta sigue siendo experimental.

## Errores frecuentes

- Si Git dice que no es un repositorio, entra primero en `D:\\Proyectos\\💰 Scout Finance`.
- Si falta Streamlit, ejecuta `python -m pip install -r requirements.txt`.
- Si el puerto `8501` esta ocupado, cierra la app anterior o usa otro puerto.
- Si falta un output, no inventes datos: revisa que la fase correspondiente este generada.
"""


def checks(contract: dict[str, Any], docs: dict[str, str], summaries: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, expected in [("bz", contract["expected_bz_status"]), ("ca", contract["expected_ca_status"])]:
        actual = summaries[key]["status"]
        rows.append({"check": f"{key}_status", "expected": expected, "actual": actual, "status": "PASS" if actual == expected else "FAIL"})
    cb_actual = summaries["cb"]["status"]
    rows.append({"check": "cb_status", "expected": "|".join(contract["expected_cb_statuses"]), "actual": cb_actual, "status": "PASS" if cb_actual in contract["expected_cb_statuses"] else "FAIL"})
    for name, text in docs.items():
        rows.append({"check": f"{name}_no_unnegated_advice", "expected": "true", "actual": str(not has_unnegated_advice(text)).lower(), "status": "PASS" if not has_unnegated_advice(text) else "FAIL"})
    guide_clean = clean_text(docs["guide"])
    faq_clean = clean_text(docs["faq"])
    for section in contract["required_sections"]:
        token = clean_text(section)
        rows.append({"check": f"guide_section:{section}", "expected": "present", "actual": "present" if token in guide_clean else "missing", "status": "PASS" if token in guide_clean else "FAIL"})
    for question in contract["required_faq_questions"]:
        token = clean_text(question)
        rows.append({"check": f"faq_question:{question}", "expected": "present", "actual": "present" if token in faq_clean else "missing", "status": "PASS" if token in faq_clean else "FAIL"})
    for key in ["main_ranking_count", "partial_comparability_count", "review_required_count", "blocked_count", "not_yet_scored_count", "total_assets"]:
        contract_key = "expected_total_count" if key == "total_assets" else f"expected_{key}"
        expected = contract[contract_key]
        actual = summaries["cb"][key]
        rows.append({"check": f"count:{key}", "expected": expected, "actual": actual, "status": "PASS" if actual == expected else "FAIL"})
    for key, expected in GUARDRAILS.items():
        rows.append({"check": f"guardrail:{key}", "expected": expected, "actual": summaries["cb"].get(key), "status": "PASS" if summaries["cb"].get(key) == expected else "FAIL"})
    return rows


def manifest_for(inputs: list[Path], output_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {}
    for path in sorted(output_dir.glob("*")):
        if path.name != "user_guide_dummy_friendly_manifest_v2_38cc.json" and path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": summary["status"],
        "inputs": {rel(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs if path.exists()},
        "outputs": outputs,
        "guardrails": GUARDRAILS,
        "scripts": ["scripts/build_user_guide_dummy_friendly_v2_38cc.py"],
        "tests": [
            "tests/qa_user_guide_dummy_friendly_v2_38cc.py",
            "tests/qa_user_guide_dummy_friendly_full_suite_v2_38cc.py",
        ],
    }


def build(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_json(contract_path)
    inputs = {
        "bz": ROOT / contract["input_bz_summary"],
        "ca": ROOT / contract["input_ca_summary"],
        "cb": ROOT / contract["input_cb_summary"],
        "ca_guide": ROOT / contract["input_ca_operator_guide"],
        "cb_troubleshooting": ROOT / contract["input_cb_troubleshooting"],
    }
    summaries = {key: load_json(path) for key, path in inputs.items() if key in {"bz", "ca", "cb"}}
    docs = {"quick_start": quick_start(), "faq": faq(), "guide": guide(summaries["cb"])}
    check_rows = checks(contract, docs, summaries)
    qa_status = "PASS" if all(row["status"] == "PASS" for row in check_rows) else "FAIL"
    summary = {
        "phase": PHASE,
        "status": contract["expected_status"] if qa_status == "PASS" else "USER_GUIDE_DUMMY_FRIENDLY_BLOCKED",
        "qa_status": qa_status,
        "check_count": len(check_rows),
        "guide_created": True,
        "quick_start_created": True,
        "faq_created": True,
        "main_ranking_count": summaries["cb"]["main_ranking_count"],
        "partial_comparability_count": summaries["cb"]["partial_comparability_count"],
        "review_required_count": summaries["cb"]["review_required_count"],
        "blocked_count": summaries["cb"]["blocked_count"],
        "not_yet_scored_count": summaries["cb"]["not_yet_scored_count"],
        "total_assets": summaries["cb"]["total_assets"],
        **GUARDRAILS,
        "next_recommended_phase": "v2.38CD-required-outputs-checklist-missing-data-diagnostics",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_text(output_dir / "USER_GUIDE_QUICK_START_v2_38cc.md", docs["quick_start"])
    write_text(output_dir / "USER_GUIDE_FAQ_v2_38cc.md", docs["faq"])
    write_text(output_dir / "USER_GUIDE_DUMMY_FRIENDLY_v2_38cc.md", docs["guide"])
    write_text(output_dir / "README.md", "# v2.38CC User Guide Dummy Friendly\n\nEnd-user documentation for Scout Finance local research use: quick start, plain-language guide, FAQ, limitations, and common troubleshooting. No scoring, network, recommendations, broker workflow, or data changes.\n")
    write_csv(output_dir / "user_guide_dummy_friendly_checks_v2_38cc.csv", check_rows, ["check", "expected", "actual", "status"])
    write_text(output_dir / "user_guide_dummy_friendly_summary_v2_38cc.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "user_guide_dummy_friendly_manifest_v2_38cc.json", json.dumps(manifest_for([contract_path, *inputs.values()], output_dir, summary), indent=2, sort_keys=True) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.contract, args.output_dir), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
