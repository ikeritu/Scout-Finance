from __future__ import annotations
# v1.4E1 UTF-8 console hotfix
import sys, contextlib, io
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import argparse, csv, json, math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "real" / "real_universe.csv"
OUT_SCOUT = ROOT / "outputs" / "scouting"
OUT_MARKET = ROOT / "outputs" / "market_data"
OUT_ROWS = OUT_MARKET / "real_market_data_rows.csv"
OUT_SUMMARY = OUT_MARKET / "real_market_data_summary.json"
OUT_REPORT = OUT_MARKET / "real_market_data_report.md"
OUT_ENRICHED = OUT_SCOUT / "real_universe_market_data_candidates.csv"
OUT_ACTIVE = OUT_SCOUT / "active_real_universe_top_candidates.csv"

def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")

def norm(v: Any) -> str:
    return str(v or "").strip()

def up(v: Any) -> str:
    return norm(v).upper().replace("$", "")

def sf(v: Any) -> float | None:
    try:
        if v is None: return None
        if isinstance(v, float) and math.isnan(v): return None
        return float(v)
    except Exception:
        return None

def pct(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or a == 0: return None
    return round((b / a - 1) * 100, 2)

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def fetch_one(ticker: str) -> dict[str, Any]:
    try:
        import yfinance as yf
    except Exception as exc:
        return {"ticker": ticker, "market_data_status": "YFINANCE_NOT_INSTALLED", "error": str(exc), "market_data_timestamp": now_utc()}
    try:
        t = yf.Ticker(ticker)
        info = {}
        try:
            info = t.fast_info or {}
        except Exception:
            info = {}
        with contextlib.redirect_stderr(io.StringIO()):
            hist = t.history(period="1mo", interval="1d", auto_adjust=False)
        closes = [float(x) for x in hist["Close"].dropna().tolist()] if hist is not None and not hist.empty and "Close" in hist else []
        vols = [float(x) for x in hist["Volume"].dropna().tolist()] if hist is not None and not hist.empty and "Volume" in hist else []
        last = closes[-1] if closes else sf(info.get("last_price"))
        prev = closes[-2] if len(closes) >= 2 else sf(info.get("previous_close"))
        c5 = closes[-6] if len(closes) >= 6 else (closes[0] if closes else None)
        c20 = closes[-21] if len(closes) >= 21 else (closes[0] if closes else None)
        vol = vols[-1] if vols else sf(info.get("last_volume"))
        avg = round(sum(vols[-20:]) / len(vols[-20:]), 2) if vols else None
        rel = round(vol / avg, 2) if vol and avg else None
        mcap = sf(info.get("market_cap"))
        return {
            "ticker": ticker,
            "market_data_status": "OK" if last else "NO_PRICE",
            "regular_market_price": round(last, 4) if last else "",
            "price_at_signal": round(last, 4) if last else "",
            "previous_close": round(prev, 4) if prev else "",
            "market_cap": int(mcap) if mcap else "",
            "volume": int(vol) if vol else "",
            "average_volume": int(avg) if avg else "",
            "relative_volume": rel if rel is not None else "",
            "change_1d": pct(prev, last),
            "change_5d": pct(c5, last),
            "change_20d": pct(c20, last),
            "currency": norm(info.get("currency")),
            "market_data_timestamp": now_utc(),
            "error": "",
        }
    except Exception as exc:
        return {"ticker": ticker, "market_data_status": "ERROR", "error": str(exc), "market_data_timestamp": now_utc()}

def score(row: dict[str, Any], idx: int) -> float:
    s = 75.0
    if sf(row.get("regular_market_price")): s += 6
    else: s -= 10
    mc = sf(row.get("market_cap"))
    if mc and mc > 1_000_000_000: s += 6
    elif mc: s += 2
    else: s -= 4
    vol = sf(row.get("volume"))
    if vol and vol > 100_000: s += 4
    elif vol: s += 1
    else: s -= 3
    chg20 = sf(row.get("change_20d"))
    if chg20 is not None and -25 <= chg20 <= 40: s += 2
    elif chg20 is not None: s -= 3
    s += max(0, 5 - idx * 0.1)
    return round(max(0, min(100, s)), 2)

def fetch() -> dict[str, Any]:
    OUT_SCOUT.mkdir(parents=True, exist_ok=True)
    OUT_MARKET.mkdir(parents=True, exist_ok=True)
    if not INPUT.exists():
        summary = {"phase":"v1.4E","status":"MISSING_INPUT","tickers_processed":0,"tickers_ok":0,"tickers_error":0,"top_tickers":"","score_method":"market_data_score_yfinance_cache_v0","yfinance_called":False,"openai_called":False,"broker_called":False,"pipeline_recalculated":False,"financial_statement_scoring_recalculated":False}
        write_json(OUT_SUMMARY, summary); return summary
    rows = read_csv(INPUT)
    seen, raw, enriched = set(), [], []
    yf_called = False
    for r in rows:
        ticker = up(r.get("ticker"))
        if not ticker or ticker in seen: continue
        seen.add(ticker)
        md = fetch_one(ticker)
        if md.get("market_data_status") != "YFINANCE_NOT_INSTALLED": yf_called = True
        merged = {"ticker":ticker,"name":norm(r.get("name")) or ticker,"company_name":norm(r.get("name")) or ticker,"exchange":up(r.get("exchange")),"country":up(r.get("country")),"sector":norm(r.get("sector")),"industry":norm(r.get("industry")), **md}
        raw.append(merged)
    for i, r in enumerate(raw, 1):
        st = "MARKET_DATA_SCORE" if r.get("market_data_status") == "OK" else "MARKET_DATA_PARTIAL"
        enriched.append({**r, "final_stage3_score": score(r, i), "stage3_category":"market_data_score", "stage3_status":st, "risk_score":"", "data_quality_score":100.0 if st=="MARKET_DATA_SCORE" else 60.0, "data_quality_label":st, "business_quality_score":"", "financial_health_score":"", "growth_score":"", "valuation_score":"", "moat_proxy_score":"", "momentum_score":"", "liquidity_score":"", "score_method":"market_data_score_yfinance_cache_v0", "source":"data/real/real_universe.csv", "note":"Market-data score from yfinance cache. Not financial statement scoring or investment advice."})
    enriched.sort(key=lambda x: x["final_stage3_score"], reverse=True)
    okn = sum(1 for r in enriched if r["stage3_status"] == "MARKET_DATA_SCORE")
    summary = {"phase":"v1.4E","title":"Real Market Data Adapter","status":"OK" if okn else "PARTIAL_OR_ERROR","created_at":now_utc(),"tickers_processed":len(enriched),"tickers_ok":okn,"tickers_error":len(enriched)-okn,"top_tickers":", ".join(r["ticker"] for r in enriched[:10]),"score_method":"market_data_score_yfinance_cache_v0","yfinance_called":yf_called,"openai_called":False,"broker_called":False,"pipeline_recalculated":False,"financial_statement_scoring_recalculated":False}
    write_csv(OUT_ROWS, raw); write_csv(OUT_ENRICHED, enriched); write_csv(OUT_ACTIVE, enriched); write_json(OUT_SUMMARY, summary)
    OUT_REPORT.write_text("# Scout Finance - v1.4E1 Real Market Data Adapter Hotfix Report\\n\\n" + json.dumps(summary, indent=2), encoding="utf-8")
    return summary

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--fetch", action="store_true")
    a = p.parse_args()
    if not a.fetch:
        p.print_help(); return
    s = fetch()
    print("Scout Finance - v1.4E1 Real Market Data Adapter Hotfix")
    print("="*92)
    print(f"Status: {s['status']}")
    print(f"Tickers processed: {s['tickers_processed']}")
    print(f"Tickers OK: {s['tickers_ok']}")
    print(f"Tickers error: {s['tickers_error']}")
    print(f"Top tickers: {s['top_tickers']}")
    print(f"Score method: {s['score_method']}")
    print(f"yfinance called: {s['yfinance_called']}")
    print("OpenAI called: False")
    print("Broker called: False")
    print("Pipeline recalculated: False")
    print("Financial statement scoring recalculated: False")
    print("Report: outputs/market_data/real_market_data_report.md")

if __name__ == "__main__":
    main()
