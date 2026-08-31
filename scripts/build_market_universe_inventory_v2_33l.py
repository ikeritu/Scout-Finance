#!/usr/bin/env python3
"""Build the reproducible market-universe inventory for the v2.33L phase-4
scoping closure, measured against the full canonical eligible universe
(21,165 candidates from v2.33B2), not just the 240-row pilot sample.

Reads outputs/full_universe_source_acquisition/v2_33b2_eligibility_refinement/
eligibility_census_v2_33b2.csv.xz. Cross-references each exchange against the
documented outcome of its v2.33D1-K closure (hardcoded below, since those are
facts already established and published, not something to re-derive). No
network calls, no credentials, no scoring, no ranking.
"""
from __future__ import annotations

import argparse
import csv
import json
import lzma
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "outputs/full_universe_source_acquisition/v2_33b2_eligibility_refinement/eligibility_census_v2_33b2.csv.xz"
OUT_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_33l_operational_universe_scope"
ELIGIBLE_STATUS = "eligible_for_financial_enrichment_v2_33b2"

# Facts established and published in prior closures (v2.33D1 through v2.33K).
# This table does not re-derive anything; it cites the already-published decision.
MARKET_FACTS = {
    "NASDAQ": {
        "candidate_price_source": "por evaluar (Bloque B, v2.33M)",
        "validated_source": "ninguna todavía",
        "depth": "n/a",
        "lag": "n/a",
        "adjusted": "n/a",
        "license": "n/a",
        "metadata_repair_status": "no requerido (esquema limpio)",
        "operational_status": "CONDITIONAL",
        "reason": "Parte del bloque EE. UU.; pendiente de piloto específico (v2.33M).",
    },
    "NYSE": {
        "candidate_price_source": "por evaluar (Bloque B, v2.33M)",
        "validated_source": "ninguna todavía",
        "depth": "n/a", "lag": "n/a", "adjusted": "n/a", "license": "n/a",
        "metadata_repair_status": "no requerido (esquema limpio)",
        "operational_status": "CONDITIONAL",
        "reason": "Parte del bloque EE. UU.; pendiente de piloto específico (v2.33M).",
    },
    "NYSE American": {
        "candidate_price_source": "por evaluar (Bloque B, v2.33M)",
        "validated_source": "ninguna todavía",
        "depth": "n/a", "lag": "n/a", "adjusted": "n/a", "license": "n/a",
        "metadata_repair_status": "no requerido (esquema limpio)",
        "operational_status": "CONDITIONAL",
        "reason": "Parte del bloque EE. UU.; pendiente de piloto específico (v2.33M).",
    },
    "Cboe BZX": {
        "candidate_price_source": "por evaluar (Bloque B, v2.33M)",
        "validated_source": "ninguna todavía",
        "depth": "n/a", "lag": "n/a", "adjusted": "n/a", "license": "n/a",
        "metadata_repair_status": "no requerido (esquema limpio)",
        "operational_status": "CONDITIONAL",
        "reason": "Parte del bloque EE. UU.; pendiente de piloto específico (v2.33M). Solo 1 candidato.",
    },
    "JPX": {
        "candidate_price_source": "J-Quants (API oficial JPX)",
        "validated_source": "J-Quants, validado en piloto v2.33G sobre 42/42 símbolos",
        "depth": "~2 años (ventana confirmada 2024-06-08 a 2026-06-08)",
        "lag": "12 semanas",
        "adjusted": "ajustado disponible (AdjFactor/AdjClose en la API)",
        "license": "uso personal permitido; prohíbe redistribuir datos en bruto y proveer resultados repetidos a terceros (sin confirmación escrita adicional todavía, v2.33N)",
        "metadata_repair_status": "no requerido (esquema limpio)",
        "operational_status": "CONDITIONAL",
        "reason": "PASS_FOR_NEXT_CONTROLLED_PILOT en v2.33G, limitado a 42 símbolos. Ampliación a los 3.701 candidatos elegibles requiere confirmación de licencia (v2.33N) y autorización explícita por superar 500 activos.",
    },
    "TWSE": {
        "candidate_price_source": "STOCK_DAY oficial de TWSE (www.twse.com.tw)",
        "validated_source": "TWSE oficial, validado en piloto v2.33I sobre 8/8 activos",
        "depth": "hasta ~16 años (ventana confirmada desde 2010-01-04)",
        "lag": "ninguno declarado (datos hasta el día anterior)",
        "adjusted": "no ajustado (sin factor de split/dividendo en la fuente)",
        "license": "Open Government Data License v1.0 (abierta)",
        "metadata_repair_status": "no requerido (esquema limpio)",
        "operational_status": "CONDITIONAL",
        "reason": "PASS_FOR_NEXT_CONTROLLED_PILOT en v2.33I, limitado a 8 activos. Ampliación a los 696 candidatos elegibles requiere piloto ampliado (v2.33O) y autorización explícita por superar 500 activos.",
    },
    "ASX": {
        "candidate_price_source": "ninguna gratuita conocida",
        "validated_source": "ninguna",
        "depth": "n/a", "lag": "n/a", "adjusted": "n/a",
        "license": "acceso oficial exige licencia MarketSource o distribuidor de pago (confirmado en v2.33J)",
        "metadata_repair_status": "no requerido (esquema limpio)",
        "operational_status": "EXCLUDED_NO_FREE_SOURCE",
        "reason": "v2.33J: NO_FREE_SOURCE_FOUND, confirmado con evidencia de primera mano (política oficial + endpoint no oficial confirmado muerto).",
    },
    "CBOE_EUROPE": {
        "candidate_price_source": "ninguna accionable",
        "validated_source": "ninguna",
        "depth": "n/a", "lag": "n/a", "adjusted": "n/a", "license": "n/a",
        "metadata_repair_status": "no requerido (esquema limpio)",
        "operational_status": "EXCLUDED_USER_DECISION",
        "reason": "v2.33H: PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE (89/119 identificadas, sin bolsa primaria fiable). Usuario descarta opciones de pago (2026-08-31). Bloqueado indefinidamente salvo hallazgo gratuito incidental.",
    },
    "BVC": {
        "candidate_price_source": "SFC (solo resumen, no serie diaria)",
        "validated_source": "ninguna",
        "depth": "n/a", "lag": "n/a", "adjusted": "n/a",
        "license": "SFC es fuente oficial pero insuficiente; bvc.com.co no verificable de forma automatizada",
        "metadata_repair_status": "no requerido (esquema limpio)",
        "operational_status": "EXCLUDED_USER_DECISION",
        "reason": "v2.33K: inconcluso, bajo impacto (3 candidatos elegibles). Usuario decide no continuar investigando (2026-08-31). Cerrado, no pendiente.",
    },
}

# Markets currently held out of the eligible pool by a metadata/schema defect
# (not yet counted in the 21,165), tracked separately so their scale is visible.
HELD_MARKETS = {
    "hold_provider_schema_xetra": {"exchange": "XETR", "market_label": "Xetra"},
    "hold_provider_schema_sgx": {"exchange": "SGX", "market_label": "SGX"},
}


def load_census() -> list[dict]:
    with lzma.open(CENSUS, "rt", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    rows = load_census()
    eligible = [r for r in rows if r["eligibility_decision_v2_33b2"] == ELIGIBLE_STATUS]
    total_eligible = len(eligible)

    by_exchange: dict[str, list[dict]] = {}
    for r in eligible:
        by_exchange.setdefault(r["exchange"], []).append(r)

    inventory = []
    for exchange, items in sorted(by_exchange.items(), key=lambda kv: -len(kv[1])):
        countries = Counter(r["country"] for r in items)
        providers = Counter(r["source_provider"] for r in items)
        facts = MARKET_FACTS.get(exchange)
        if facts is None:
            raise SystemExit(f"No MARKET_FACTS entry for exchange {exchange!r} -- add one before publishing")
        inventory.append({
            "mercado": exchange,
            "pais": countries.most_common(1)[0][0] or "(sin país en el censo)",
            "proveedor_identidad": providers.most_common(1)[0][0],
            "candidatos_elegibles": len(items),
            "pct_del_universo_elegible": round(len(items) / total_eligible * 100, 2),
            "estado_reparacion_metadatos": facts["metadata_repair_status"],
            "fuente_precios_candidata": facts["candidate_price_source"],
            "fuente_validada": facts["validated_source"],
            "profundidad_disponible": facts["depth"],
            "retraso": facts["lag"],
            "ajustado_no_ajustado": facts["adjusted"],
            "licencia_retencion": facts["license"],
            "estado_operativo": facts["operational_status"],
            "motivo": facts["reason"],
        })

    held = []
    for status_key, label in HELD_MARKETS.items():
        items = [r for r in rows if r["eligibility_decision_v2_33b2"] == status_key]
        held.append({
            "mercado": label["market_label"],
            "candidatos_retenidos": len(items),
            "estado_operativo": "BLOCKED_METADATA_CORRUPTION",
            "motivo": f"{len(items)} filas retenidas por esquema sospechoso ({status_key}); no forman parte todavía de los 21.165 candidatos elegibles.",
        })

    us_exchanges = {"NASDAQ", "NYSE", "NYSE American", "Cboe BZX"}
    us_total = sum(r["candidatos_elegibles"] for r in inventory if r["mercado"] in us_exchanges)

    summary = {
        "phase": "v2.33L-operational-universe-scope",
        "total_eligible_candidates_v2_33b2": total_eligible,
        "total_candidates_held_by_metadata_corruption": sum(h["candidatos_retenidos"] for h in held),
        "us_bloc_total_candidates": us_total,
        "us_bloc_exchanges": sorted(us_exchanges),
        "by_operational_status": dict(Counter(r["estado_operativo"] for r in inventory)),
        "inventory": inventory,
        "held_by_metadata_corruption": held,
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fields = list(inventory[0].keys())
        csv_path = OUT_DIR / "market_universe_inventory_v2_33l.csv"
        tmp = csv_path.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(inventory)
        tmp.replace(csv_path)

        json_path = OUT_DIR / "market_universe_inventory_report_v2_33l.json"
        tmp2 = json_path.with_suffix(".json.tmp")
        tmp2.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp2.replace(json_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
