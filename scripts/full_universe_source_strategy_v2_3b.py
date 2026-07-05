from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.3B"
METHOD = "full_universe_source_strategy_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "full_universe_source_strategy_v2_3b.json"
OUT_MD = OUT_DIR / "full_universe_source_strategy_v2_3b.md"

AUDIT_V2_3A = OUT_DIR / "full_universe_source_acquisition_audit_v2_3a.json"

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}

    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    audit = read_json(AUDIT_V2_3A)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    if not audit.get("_exists"):
        blockers.append(f"Missing required v2.3A audit: {rel(AUDIT_V2_3A)}")
        audit_status = None
        csv_files_scanned = 0
        full_candidates_count = 0
        partial_candidates_count = 0
        top_candidates = []
    else:
        audit_status = audit.get("audit_status")
        csv_files_scanned = int(audit.get("csv_files_scanned") or 0)
        full_candidates_count = int(audit.get("full_candidates_count") or 0)
        partial_candidates_count = int(audit.get("partial_candidates_count") or 0)
        top_candidates = audit.get("top_candidates", [])

        positives.append(f"v2.3A audit found and readable: {rel(AUDIT_V2_3A)}")
        positives.append(f"CSV files scanned in v2.3A: {csv_files_scanned}")

    best_local_candidate = None
    if top_candidates:
        best_local_candidate = top_candidates[0]
        positives.append(
            f"Best local candidate: {best_local_candidate.get('path')} "
            f"with {best_local_candidate.get('rows')} rows."
        )

    if full_candidates_count > 0:
        decision = "FULL_SOURCE_CANDIDATE_AVAILABLE"
        readiness_score = 80
        positives.append("At least one local full universe source candidate exists.")
        recommendation = "Proceed to v2.3C full source normalization using the best candidate."
    elif partial_candidates_count > 0:
        decision = "EXTERNAL_OR_EXPANDED_SOURCE_REQUIRED"
        readiness_score = 60
        warnings.append("No local full universe source exists.")
        warnings.append("Current local universe is partial and cannot unlock full 59k.")
        recommendation = (
            "Do not run full 59k. Choose a source expansion strategy first. "
            "Recommended route: build an expanded public-market universe by combining official exchange symbol lists, "
            "then normalize and validate it before repeating v2.2C and v2.2E."
        )
    else:
        decision = "SOURCE_STRATEGY_BLOCKED"
        readiness_score = 0
        blockers.append("No usable source candidates found in v2.3A.")
        recommendation = "Acquire at least one usable public-market source before continuing."

    strategies = [
        {
            "id": "A",
            "name": "Expand current public exchange universe",
            "summary": "Build a larger source by combining official symbol lists from NASDAQ/NYSE/AMEX and additional exchanges.",
            "pros": [
                "Auditable and reproducible.",
                "Can reuse current Symbol -> ticker mapping.",
                "Keeps the project close to real public market data.",
                "Best fit for incremental validation.",
            ],
            "cons": [
                "May still not reach 59k without global exchanges.",
                "Requires careful deduplication by ticker/exchange/country.",
                "Needs clear source provenance per exchange.",
            ],
            "risk": "MEDIUM",
            "recommended": True,
            "next_step": "Create v2.3C source expansion plan and define provider/exchange list.",
        },
        {
            "id": "B",
            "name": "Global multi-exchange universe",
            "summary": "Create a broader global universe across US, Europe, Asia and other listed markets.",
            "pros": [
                "Most likely path to 50k-59k instruments.",
                "Better long-term fit for global scouting.",
            ],
            "cons": [
                "Higher normalization complexity.",
                "Ticker collisions across exchanges are likely.",
                "Country, currency and exchange metadata become mandatory.",
            ],
            "risk": "HIGH",
            "recommended": False,
            "next_step": "Use only after Strategy A is stable.",
        },
        {
            "id": "C",
            "name": "Close 59k as future and keep 5k-7k mode",
            "summary": "Accept the current partial universe as the operating universe for now.",
            "pros": [
                "Lowest technical risk.",
                "Current pipeline already validates partial source and small batch.",
                "Allows moving back to product features.",
            ],
            "cons": [
                "Does not satisfy the original 59k ambition.",
                "Full 59k dry-run remains blocked.",
            ],
            "risk": "LOW",
            "recommended": False,
            "next_step": "Tag current state and continue with MVP/product improvements.",
        },
        {
            "id": "D",
            "name": "External complete dataset",
            "summary": "Find or purchase/download a complete listed-companies dataset and validate it.",
            "pros": [
                "Fastest route if a trustworthy dataset is available.",
                "Could immediately unlock v2.2C/v2.2E repeat.",
            ],
            "cons": [
                "Licensing and freshness risk.",
                "Potential hidden quality issues.",
                "May introduce non-reproducible dependency.",
            ],
            "risk": "MEDIUM_HIGH",
            "recommended": False,
            "next_step": "Only use if license, freshness and schema are clear.",
        },
    ]

    recommended_strategy = next((s for s in strategies if s["recommended"]), None)

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "decision": decision,
        "readiness_score": readiness_score,
        "expected_full_rows": EXPECTED_FULL_ROWS,
        "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
        "v2_3a_audit": {
            "path": rel(AUDIT_V2_3A),
            "exists": audit.get("_exists"),
            "audit_status": audit_status,
            "csv_files_scanned": csv_files_scanned,
            "full_candidates_count": full_candidates_count,
            "partial_candidates_count": partial_candidates_count,
        },
        "best_local_candidate": best_local_candidate,
        "strategies": strategies,
        "recommended_strategy": recommended_strategy,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
        },
        "recommendation": recommendation,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.3B Full Universe Source Strategy")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Decision: **{decision}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Expected full rows: {EXPECTED_FULL_ROWS}")
    md.append(f"- Minimum full source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("")
    md.append("## v2.3A audit input")
    md.append("")
    for key, value in payload["v2_3a_audit"].items():
        md.append(f"- {key}: {value}")
    md.append("")
    md.append("## Best local candidate")
    md.append("")
    if best_local_candidate:
        md.append(f"- Path: `{best_local_candidate.get('path')}`")
        md.append(f"- Rows: {best_local_candidate.get('rows')}")
        md.append(f"- Status: {best_local_candidate.get('candidate_status')}")
        md.append(f"- Scope: {best_local_candidate.get('candidate_scope')}")
        md.append(f"- Ticker column: {best_local_candidate.get('ticker_column')}")
    else:
        md.append("- No local candidate available.")
    md.append("")
    md.append("## Strategy options")
    md.append("")
    for strategy in strategies:
        marker = " ? **RECOMMENDED**" if strategy["recommended"] else ""
        md.append(f"### Strategy {strategy['id']} ? {strategy['name']}{marker}")
        md.append("")
        md.append(strategy["summary"])
        md.append("")
        md.append(f"- Risk: {strategy['risk']}")
        md.append(f"- Next step: {strategy['next_step']}")
        md.append("")
        md.append("Pros:")
        for item in strategy["pros"]:
            md.append(f"- {item}")
        md.append("")
        md.append("Cons:")
        for item in strategy["cons"]:
            md.append(f"- {item}")
        md.append("")
    md.append("## Positives")
    md.append("")
    if positives:
        for item in positives:
            md.append(f"- {item}")
    else:
        md.append("- No positives detected.")
    md.append("")
    md.append("## Blockers")
    md.append("")
    if blockers:
        for item in blockers:
            md.append(f"- {item}")
    else:
        md.append("- No blockers detected.")
    md.append("")
    md.append("## Warnings")
    md.append("")
    if warnings:
        for item in warnings:
            md.append(f"- {item}")
    else:
        md.append("- No warnings detected.")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(recommendation)
    md.append("")
    md.append("Important: v2.3B is a strategy gate only. It does not download data, execute scoring, call OpenAI, call a broker, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.3B Full Universe Source Strategy")
    print("=" * 92)
    print(f"OK   Decision: {decision}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   v2.3A audit status: {audit_status}")
    print(f"OK   Full candidates: {full_candidates_count}")
    print(f"OK   Partial candidates: {partial_candidates_count}")
    if best_local_candidate:
        print(f"OK   Best local candidate: {best_local_candidate.get('path')} ({best_local_candidate.get('rows')} rows)")
    print(f"OK   Recommended strategy: {recommended_strategy.get('id') if recommended_strategy else None}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
