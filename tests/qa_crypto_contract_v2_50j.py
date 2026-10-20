#!/usr/bin/env python3
"""QA for v2.50J (phase 5b): contract security through GoPlus, on demand. Pure checks (lookup planning, parsing, assessment, verdict wording,
orchestration, score effect) with scripted transports, then the real app through AppTest with a fake CoinGecko and a fake GoPlus that are
always patched in (the code tolerates network errors, so a blocked network would look like "no data"). Checks that a severe flag caps the score
at 44 and re-orders the list, that an unverified contract changes nothing and is never worded "seguro", that nothing from GoPlus reaches the
disk, and that every failure is explained. No network, no real key."""
from __future__ import annotations

import json
import logging
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
logging.disable(logging.CRITICAL)

from qa_crypto_search_v2_50f import (BSC, ETH, GOPLUS, PLATFORMS, PLATFORMS_STATUS, SOL, Sandbox, button, cards, direct_client, forbid_network,  # noqa: E402
                                     open_crypto_page, page_text, require)
from src.crypto_v2_50 import contract_security as cs, scoring as sc  # noqa: E402
from src.crypto_v2_50.coingecko import KEY_ENV  # noqa: E402
from src.crypto_v2_50.search import overlay_checks, run_search  # noqa: E402
from src.ui_v2_37 import crypto_screen as screen  # noqa: E402


def transport_returning(payload=None, status=200):
    return lambda url, timeout: (status, {}, json.dumps(payload if payload is not None else {"code": 1, "result": {}}).encode())


# ------------------------------------------------------------------------------------------------------------------------------ lookups

def test_lookups_are_planned_from_supported_chains_with_valid_addresses() -> None:
    good = "0x" + "a" * 40
    platforms = {"ethereum": good, "binance-smart-chain": "0xnothex", "osmosis": "osmo1abc", "solana": SOL, "tron": "T" + "A" * 33, "base": good.upper().replace("0X", "0x"),
                 "polygon-pos": "", "arbitrum-one": None, "optimistic-ethereum": "0x" + "b" * 39, "avalanche": 5}
    plan = cs.plan_lookups(platforms)
    require([l["platform"] for l in plan] == ["ethereum", "base", "tron", "solana"], f"valid addresses on supported chains, biggest chains first: {[l['platform'] for l in plan]}")
    require(all(l["chain"] == cs.CHAINS[l["platform"]] for l in plan), "each lookup carries its GoPlus chain key")
    require(cs.plan_lookups({p: good for p in ("ethereum", "binance-smart-chain", "polygon-pos", "base", "arbitrum-one", "avalanche")}, 4) and
            len(cs.plan_lookups({p: good for p in ("ethereum", "binance-smart-chain", "polygon-pos", "base", "arbitrum-one", "avalanche")}, 4)) == 4, "at most four chains")
    require(cs.plan_lookups({}) == [] and cs.plan_lookups({"osmosis": "x"}) == [], "nothing to ask")
    wide = {p: good for p in ("ethereum", "binance-smart-chain", "polygon-pos", "base", "arbitrum-one", "avalanche")}
    require([l["platform"] for l in cs.plan_lookups(wide, 4, "base")] == ["base", "ethereum", "binance-smart-chain", "polygon-pos"], "the primary platform is asked first, even if it is not among the biggest chains")
    require([l["platform"] for l in cs.plan_lookups(wide, 4, "avalanche")][0] == "avalanche" and [l["platform"] for l in cs.plan_lookups(wide, 4, "unknown-chain")][0] == "ethereum", "an unknown primary changes nothing")
    require(cs.valid_address("solana", SOL) and not cs.valid_address("solana", "0x" + "a" * 40) and not cs.valid_address("1", SOL) and not cs.valid_address("1", None), "address shapes")


def test_the_goplus_response_is_parsed_and_every_failure_is_safe() -> None:
    record = {"is_honeypot": "0"}
    got = cs.fetch_token_security("1", ETH, transport_returning({"code": 1, "message": "OK", "result": {ETH: record}}))
    require(got == record, "the record is found by address")
    require(cs.fetch_token_security("1", ETH, transport_returning({"code": 1, "result": {ETH.lower(): record}})) == record, "or by its lower-case form")
    require(cs.fetch_token_security("1", ETH, transport_returning({"code": 1, "result": {}})) is None and cs.fetch_token_security("1", ETH, transport_returning({"code": 1, "result": {ETH: {}}})) is None,
            "an empty result is None: GoPlus has nothing for the token")
    seen = []
    cs.fetch_token_security("solana", SOL, lambda u, t: (seen.append(u), (200, {}, b'{"code": 1, "result": {}}'))[1])
    cs.fetch_token_security("56", BSC, lambda u, t: (seen.append(u), (200, {}, b'{"code": 1, "result": {}}'))[1])
    require("/api/v1/solana/token_security?contract_addresses=" in seen[0] and "/api/v1/token_security/56?contract_addresses=" in seen[1], f"each chain has its endpoint: {seen}")
    secret = "SECRET-IN-ERROR"
    for transport, text in ((lambda u, t: (429, {}, b"{}"), "ritmo"), (lambda u, t: (418, {}, b"{}"), "ritmo"), (lambda u, t: (503, {}, b"{}"), "HTTP 503"),
                            (lambda u, t: (200, {}, b"<html>"), "no es JSON"), (lambda u, t: (200, {}, b'{"code": 0}'), "resultado válido"),
                            (lambda u, t: (200, {}, b"[1]"), "resultado válido"), (lambda u, t: (_ for _ in ()).throw(RuntimeError(secret)), "no respondió")):
        try:
            cs.fetch_token_security("1", ETH, transport)
        except cs.ContractSecurityError as error:
            require(text in str(error) and secret not in str(error) and error.__cause__ is None, f"{text}: {error}")
        else:
            raise AssertionError(f"{text}: no error raised")


# ------------------------------------------------------------------------------------------------------------------------------ assessment

def evm(**over) -> dict:
    return {"is_open_source": "1", "is_proxy": "0", "is_mintable": "0", "is_honeypot": "0", "cannot_buy": "0", "cannot_sell_all": "0", "hidden_owner": "0",
            "can_take_back_ownership": "0", "owner_change_balance": "0", "selfdestruct": "0", "is_airdrop_scam": "0", "fake_token": {"value": 0}, "buy_tax": "0", "sell_tax": "0",
            "holder_count": "5000", "holders": [], "is_in_dex": "1"} | over


def test_evm_flags_taxes_and_the_wording_of_the_verdict() -> None:
    clean = cs.assess("1", evm())
    require(clean["severe"] == [] and clean["evaluated"] == clean["of"] == 11 and cs.verdict(clean) == "sin señales graves en lo evaluado", str(clean))
    for key, fragment in (("is_honeypot", "honeypot"), ("cannot_buy", "comprar"), ("cannot_sell_all", "todo el saldo"), ("hidden_owner", "oculto"), ("can_take_back_ownership", "recuperar"),
                          ("owner_change_balance", "cambiar saldos"), ("selfdestruct", "autodestruirse"), ("is_airdrop_scam", "airdrop")):
        result = cs.assess("1", evm(**{key: "1"}))
        require(len(result["severe"]) == 1 and fragment in result["severe"][0] and cs.verdict(result) == "señales graves", f"{key}: {result['severe']}")
    require(cs.assess("1", evm(fake_token={"value": 1}))["severe"] == ["token falso: imita a otro"], "a fake token")
    require("impuesto de venta del 50 %" in cs.assess("1", evm(sell_tax="0.5"))["severe"][0] and "impuesto de compra del 90 %" in cs.assess("1", evm(buy_tax="0.9"))["severe"][0], "50 % and above is severe")
    mild = cs.assess("1", evm(sell_tax="0.49", buy_tax="0.12"))
    require(mild["severe"] == [] and any("venta del 49,0 %" in i["label"] and i["level"] == "alert" for i in mild["info"]) and any("compra del 12,0 %" in i["label"] for i in mild["info"]), str(mild["info"]))
    informative = cs.assess("1", evm(is_mintable="1", is_proxy="1", transfer_pausable="1", is_blacklisted="1", creator_percent="0.35"))
    labels = " | ".join(i["label"] for i in informative["info"])
    require(informative["severe"] == [] and all(w in labels for w in ("acuñar", "proxy", "pausar", "lista negra", "creador conserva el 35 %")), labels)
    partial = cs.assess("1", {"is_honeypot": "0", "is_open_source": "1"})
    require(partial["evaluated"] == 1 and partial["of"] == 11 and cs.verdict(partial) == "sin señales graves en lo evaluado (parcial)", f"omitted fields are NOT evaluated: {partial['evaluated']}")
    empty = cs.assess("1", {"token_name": "X"})
    require(empty["evaluated"] == 0 and cs.verdict(empty) == "sin evaluar", "nothing evaluated is never worded as fine")
    for text in (cs.verdict(clean), cs.verdict(partial), cs.verdict(empty), cs.verdict(cs.assess("1", evm(is_honeypot="1")))):
        require("seguro" not in text.lower(), f"the word 'seguro' must never describe a contract: {text}")
    closed = cs.assess("1", {"is_open_source": "0"})
    require(any("no está verificado" in n for n in closed["notes"]) and any(i["label"] == "código del contrato no verificado" for i in closed["info"]), "a closed-source contract says GoPlus could not evaluate most risks")


def test_holders_and_the_data_quality_notes() -> None:
    holders = [{"address": "0x" + "1" * 40, "percent": "0.30", "tag": "", "is_contract": 0, "is_locked": 0}, {"address": "0x" + "2" * 40, "percent": "0.20", "tag": "Pool", "is_contract": 1, "is_locked": 0},
               {"address": "0x" + "3" * 40, "percent": "0.10", "tag": "", "is_contract": 0, "is_locked": 1}, {"address": "0x" + "4" * 40, "percent": "0.05", "tag": "Binance", "is_contract": 0, "is_locked": 0},
               {"address": "0x" + "5" * 40, "percent": "0.04", "tag": "", "is_contract": 0, "is_locked": 0}, "junk", None]
    result = cs.assess("1", evm(holders=holders, holder_count="1"))
    h = result["holders"]
    require(abs(h["top10_share"] - 0.69) < 1e-9 and abs(h["top10_share_free"] - 0.34) < 1e-9, f"top-10 share and the part held by plain accounts: {h}")
    require(h["top"][0]["address"] == "0x1111…1111" and h["top"][1]["contract"] is True and h["top"][2]["locked"] is True, "addresses are shortened; contract and locked flags kept")
    require(any("1 solo tenedor" in n for n in result["notes"]), "1 holder next to a listed top is flagged as unreliable (it happened with USDT)")
    over = cs.assess("1", evm(holders=[{"address": "0x" + "1" * 40, "percent": "0.8"}, {"address": "0x" + "2" * 40, "percent": "0.5"}]))
    require(any("más del 100 %" in n for n in over["notes"]), "percentages above 100 % are flagged")
    none = cs.assess("1", evm(holders=[], holder_count="x"))
    require(none["holders"]["count"] is None and none["holders"]["top10_share"] is None and none["holders"]["top10_share_free"] is None, "no holders: unknown, not zero")


def test_solana_schema_is_read_as_nested_status_objects() -> None:
    clean = cs.assess("solana", GOPLUS[("solana", SOL)])
    require(clean["kind"] == "solana" and clean["severe"] == [] and clean["evaluated"] == clean["of"] == 3, str(clean))
    require([i["label"] for i in clean["info"]] == ["una autoridad puede congelar cuentas"] and clean["info"][0]["level"] == "alert", "a freezable authority is information, not a red flag")
    require(clean["holders"]["count"] == 1020153 and clean["holders"]["top"][0]["address"].startswith("9WzDXw"), "holders are read from `account`")
    base = dict(GOPLUS[("solana", SOL)])
    require(cs.assess("solana", base | {"balance_mutable_authority": {"authority": ["a"], "status": "1"}})["severe"] == ["una autoridad puede cambiar los saldos"], "balance-mutable authority is severe")
    require(cs.assess("solana", base | {"non_transferable": "1"})["severe"] == ["el token no se puede transferir"], "non-transferable is severe")
    require(cs.assess("solana", base | {"default_account_state": "2"})["severe"] == ["las cuentas nuevas nacen congeladas"], "frozen-by-default is severe")
    rich = cs.assess("solana", base | {"transfer_fee": {"x": 1}, "transfer_hook": ["p"], "mintable": {"status": "1"}})
    require({"cobra una comisión por transferencia", "ejecuta un programa externo en cada transferencia", "una autoridad puede acuñar más unidades"} <= {i["label"] for i in rich["info"]}, "fees, hooks and mint authority are information")
    sparse = cs.assess("solana", {"holder_count": "3"})
    require(sparse["evaluated"] == 0 and cs.verdict(sparse) == "sin evaluar", "a record without the authority fields evaluates nothing")


# --------------------------------------------------------------------------------------------------------------------------- orchestration

def check(box: Sandbox, coin_id: str, **kw) -> dict:
    client, cache, _ = direct_client(box)
    slept: list[float] = []
    result = cs.check_contract(client, cache, coin_id, transport=box.goplus, sleep=slept.append, **kw)
    result["slept"] = slept
    return result


def test_each_outcome_of_a_check_is_a_record_with_a_status() -> None:
    with Sandbox() as box:
        pump = check(box, "pump-coin")
        require(pump["status"] == "checked" and pump["platform"] == "binance-smart-chain" and pump["chain"] == "56" and pump["verdict"] == "señales graves", str(pump["status"]))
        require([t["outcome"] for t in pump["tried"]] == ["GoPlus no tiene datos de este contrato", "con datos"], "Ethereum had nothing; BNB Chain answered")
        require(pump["slept"] == [cs.PACE_SECONDS] and len(box.goplus.calls) == 2, "a pause between the two GoPlus calls, none before the first")
        coingecko_calls = len([u for u in box.fake.calls if "/coins/pump-coin?" in u])
        again = check(box, "pump-coin")
        require(len([u for u in box.fake.calls if "/coins/pump-coin?" in u]) == coingecko_calls == 1 and again["status"] == "checked", "the contract list comes from the 24 h cache the second time")
        low = check(box, "low-coin")
        require(low["status"] == "checked" and low["chain"] == "solana" and low["verdict"] == "sin señales graves en lo evaluado" and low["slept"] == [], low["verdict"])
        require(check(box, "dilute-coin")["status"] == "no_contract" and len([c for c in box.goplus.calls if "dilute" in c]) == 0, "no contract: nothing asked")
        unsupported = check(box, "sus-coin")
        require(unsupported["status"] == "unsupported_chain" and unsupported["platforms"] == ["osmosis"], str(unsupported))
        none = check(box, "quiet-2")
        require(none["status"] == "no_data" and none["error"] is None and none["assessment"] is None, "GoPlus had nothing: not verified")
        failed = check(box, "quiet-1")
        require(failed["status"] == "error" and "HTTP 500" in failed["error"], str(failed))
        limited = check(box, "quiet-4")
        require(limited["status"] == "error" and "ritmo" in limited["error"], str(limited))
        many = check(box, "quiet-5")
        require(many["status"] == "no_data" and [t["platform"] for t in many["tried"]] == ["arbitrum-one", "ethereum", "binance-smart-chain", "polygon-pos"], "six chains: at most four are asked, the primary platform first")
        require(len([c for c in box.goplus.calls if any("0x" + str(d) * 40 in c for d in (1, 2, 3, 5))]) == 4 and not any("0x" + "4" * 40 in c or "0x" + "6" * 40 in c for c in box.goplus.calls), "and only those four reached GoPlus")
        require(pump["primary"] is False and pump["other_platforms"] == ["ethereum"], "a check says whether the chain is the main one and which others exist")
        require(len(check(box, "quiet-5", max_chains=2)["tried"]) == 2, "the limit is a parameter")
        PLATFORMS_STATUS["code"] = 500
        broken = check(box, "quiet-3")
        require(broken["status"] == "error" and "No se pudieron obtener los contratos" in broken["error"], str(broken["error"]))


def test_a_severe_flag_caps_the_score_and_an_unverified_contract_changes_nothing() -> None:
    with Sandbox() as box:
        client, cache, _ = direct_client(box)
        scored = run_search(client, cache).scored
        by = {r["coin_id"]: r for r in scored}
        pump = by["pump-coin"]
        require(pump["score"] == 90 and pump["tier"] == sc.TIER_HIGH, "before the check")
        capped = sc.rescore(pump, ["honeypot: no se puede vender"])
        require(capped["score"] == 44 and capped["tier"] == sc.TIER_WATCH and "contrato con señales graves" in capped["risk_flags"], str(capped["risk_flags"]))
        require(capped["caps_applied"][0]["reason"] == "señal grave de contrato (GoPlus): honeypot: no se puede vender" and capped["caps_applied"][0]["max"] == 44, str(capped["caps_applied"]))
        require(capped["coin_id"] == pump["coin_id"] and capped["perp"] == pump["perp"] and capped["history_days"] == pump["history_days"] and capped["rel_vol_rolling"] == pump["rel_vol_rolling"], "the rest of the coin is untouched")
        require(sc.rescore(pump, [])["score"] == 90, "no severe flag: the same score")
        checks = {"pump-coin": check(box, "pump-coin"), "low-coin": check(box, "low-coin"), "quiet-2": check(box, "quiet-2"), "dilute-coin": check(box, "dilute-coin"), "quiet-1": check(box, "quiet-1")}
        merged = {r["coin_id"]: r for r in overlay_checks(scored, checks)}
        require(merged["pump-coin"]["score"] == 44 and merged["pump-coin"]["tier"] == sc.TIER_WATCH, "the severe check is applied")
        for coin_id in ("low-coin", "quiet-2", "dilute-coin", "quiet-1", "sus-coin"):
            require(merged[coin_id] == by[coin_id], f"{coin_id}: a clean, unverified or failed check changes nothing")
        require(overlay_checks(scored, {}) is scored, "no checks: the very same list")
        ordered = [r["coin_id"] for r in overlay_checks(scored, checks)]
        require(ordered.index("pump-coin") > ordered.index("dilute-coin") and ordered[0] == "dilute-coin", f"the list is ordered again: {ordered[:4]}")
        require(overlay_checks(scored, {"pump-coin": {"status": "checked", "assessment": None}})[0]["coin_id"] == "pump-coin", "a malformed check is ignored")


# ----------------------------------------------------------------------------------------------------------------------------- the page

def searched():
    at = open_crypto_page()
    button(at, "crypto_search").click().run()
    require(not at.exception, f"the search crashed: {[e.value[:120] for e in at.exception]}")
    return at


def open_coin(at, coin_id: str):
    button(at, f"crypto_fullpage_select_{screen.card_key(coin_id)}").click().run()
    require(not at.exception, f"the coin page crashed: {[e.value[:120] for e in at.exception]}")
    return at


def run_check(at, coin_id: str):
    button(at, f"crypto_contract_check_{screen.card_key(coin_id)}").click().run()
    require(not at.exception, f"the check crashed: {[e.value[:120] for e in at.exception]}")
    return at


def test_the_security_tab_checks_on_demand_and_a_severe_flag_changes_the_page() -> None:
    with Sandbox() as box:
        at = open_coin(searched(), "pump-coin")
        require([t.label for t in at.tabs] == ["Resumen", "Datos", "Gráfico", "Derivados", "Seguridad"], "five tabs")
        require(len(box.goplus.calls) == 0, "opening the page asks GoPlus nothing: it is on demand")
        require(any("Coste: una llamada a CoinGecko" in c.value for c in at.caption) and "crypto_contract_check_" + screen.card_key("pump-coin") in [b.key for b in at.button], "the button and its cost")
        before = len(box.fake.calls)
        run_check(at, "pump-coin")
        require(len(box.fake.calls) == before + 1 and len(box.goplus.calls) == 2, "one CoinGecko call for the contracts, two GoPlus calls (Ethereum had nothing)")
        require(any("Señales graves" in e.value and "honeypot" in e.value and "impuesto de venta del 60 %" in e.value and "limita a 44" in e.value for e in at.error), "the red flags are listed with the cap")
        text = page_text(at)
        header = next(m.value for m in at.markdown if "Pump Coin" in m.value and "/100" in m.value)
        require("44<span" in header.replace("\n", "") and "En vigilancia" in header and "Candidato explosivo" not in header, "the header now shows 44 and the watch level")
        require("Contrato con señales graves" in header, "and the risk chip")
        require("Comprobado a las" in text and "Se evaluaron 5 de 11 comprobaciones graves" in text.replace("\n", " "), "when and how much was evaluated")
        require(any("Repetir la comprobación" == b.label for b in at.button), "the button now offers to repeat")
        require(any("Tope aplicado:" in m.value and "señal grave de contrato (GoPlus)" in m.value and "máximo 44" in m.value for m in at.markdown), "the Datos tab lists the applied cap")
        button(at, "crypto_fullpage_back").click().run()
        listing = cards(at)
        require("Dilute Coin" in listing[0] and "Pump Coin" not in listing[0], "the list is ordered again: the flagged coin is no longer first")
        require(any("Pump Coin" in c and "Contrato con señales graves" in c and "En vigilancia" in c for c in listing), "its card shows the tag and the new level")
        require("2 candidatas explosivas" in page_text(at) and "1 monedas tienen señales graves de contrato" in page_text(at), "the summary counts again")
        require("CG-FAKE" not in page_text(at), "no key on the page")


def test_every_other_outcome_is_explained_and_changes_no_score() -> None:
    with Sandbox() as box:
        at = searched()
        scores = {r["coin_id"]: r["score"] for r in at.session_state["crypto_results"]}
        for coin_id, expected in (("low-coin", "sin señales graves en lo evaluado"), ):
            run_check(open_coin(at, coin_id), coin_id)
            text = page_text(at)
            require(expected in text.lower() and "Eso no es una garantía" in text and "una autoridad puede congelar cuentas" in text, f"{coin_id}: a clean check is worded with its caveat")
            require("seguro" not in text.lower().replace("no es una garantía", ""), "never 'seguro'")
            require(any(d.value.shape[0] >= 1 and "Porcentaje" in d.value.columns for d in at.dataframe), "the holders table")
            button(at, "crypto_fullpage_back").click().run()
        for coin_id, needle in (("dilute-coin", "no tiene contrato en CoinGecko"), ("sus-coin", "cadenas que GoPlus no cubre (osmosis)"), ("quiet-2", "No verificado"),
                                ("quiet-3", "dato poco fiable")):
            open_coin(at, coin_id)
            run_check(at, coin_id)
            require(needle in page_text(at), f"{coin_id}: expected '{needle}'")
            button(at, "crypto_fullpage_back").click().run()
        open_coin(at, "quiet-1")
        run_check(at, "quiet-1")
        require(any("HTTP 500" in w.value for w in at.warning), "a GoPlus failure is a warning")
        button(at, "crypto_fullpage_back").click().run()
        open_coin(at, "quiet-4")
        run_check(at, "quiet-4")
        require(any("limitó el ritmo" in w.value for w in at.warning) and len([c for c in box.goplus.calls if "f" * 40 in c]) == 1, "a rate limit is said and not insisted on")
        now = {r["coin_id"]: r["score"] for r in at.session_state["crypto_results"]}
        require(now == scores, "none of those outcomes changes a score in the stored results")


def test_without_a_key_the_tab_says_so_and_keeps_a_previous_result() -> None:
    import os

    with Sandbox() as box:
        at = open_coin(searched(), "low-coin")
        run_check(at, "low-coin")
        os.environ.pop(KEY_ENV, None)
        at.run()
        require(not at.exception and "Eso no es una garantía" in page_text(at), "a result already obtained stays visible")
    with Sandbox() as box:
        at = open_coin(searched(), "quiet-3")
        os.environ.pop(KEY_ENV, None)
        at.run()
        require(any(KEY_ENV in i.value for i in at.info) and button(at, "crypto_contract_check_" + screen.card_key("quiet-3")).disabled, "no key: the button is disabled and the page says why")
        require(len(box.goplus.calls) == 0, "and GoPlus is not called")


def test_nothing_from_goplus_reaches_the_disk_and_the_home_starts_clean() -> None:
    with Sandbox() as box:
        at = open_coin(searched(), "low-coin")
        run_check(at, "low-coin")
        files = [p.name for p in box.data_dir.rglob("*") if p.is_file()]
        blob = b"".join(p.read_bytes() for p in box.data_dir.rglob("*") if p.is_file())
        require(all(n.endswith(".bin") or n.endswith(".json") for n in files) and b"1020153" not in blob and b"balance_mutable" not in blob and b"GoPlus" not in blob,
                f"only the encrypted CoinGecko cache and the call counter are on disk, nothing from GoPlus: {files}")
        require("crypto_contract_checks" in at.session_state and len(at.session_state["crypto_contract_checks"]) == 1, "the check lives in the session")
        at.session_state["screen"] = "home"
        at.run()
        button(at, "home_crypto").click().run()
        require("crypto_contract_checks" not in at.session_state, "entering from the home clears the checks")


def test_the_modules_are_quiet_and_write_nothing() -> None:
    source = (ROOT / "src" / "crypto_v2_50" / "contract_security.py").read_text(encoding="utf-8")
    require("print(" not in source and "logging" not in source and "write_text" not in source and not re.search(r"(?<![a-z])open\(", source) and "to_csv" not in source, "no printing, logging or writing")
    require("str(error)" not in source.split("def fetch_token_security")[1].split("def ")[0] and "{error}" not in source.split("def fetch_token_security")[1].split("def ")[0], "transport error messages are never forwarded")
    ui = (ROOT / "src" / "ui_v2_37" / "crypto_screen.py").read_text(encoding="utf-8")
    require(not re.search(r"font-size:(\d|1[01])px", ui) and "seguro" not in ui.lower().replace("no es una garantía", "").replace("ni segura ni peligrosa", "").replace("sea seguro", "").replace("sea segura", ""),
            "no text under 12 px, and no wording that calls a contract safe")


CASES = [
    test_lookups_are_planned_from_supported_chains_with_valid_addresses,
    test_the_goplus_response_is_parsed_and_every_failure_is_safe,
    test_evm_flags_taxes_and_the_wording_of_the_verdict,
    test_holders_and_the_data_quality_notes,
    test_solana_schema_is_read_as_nested_status_objects,
    test_each_outcome_of_a_check_is_a_record_with_a_status,
    test_a_severe_flag_caps_the_score_and_an_unverified_contract_changes_nothing,
    test_the_security_tab_checks_on_demand_and_a_severe_flag_changes_the_page,
    test_every_other_outcome_is_explained_and_changes_no_score,
    test_without_a_key_the_tab_says_so_and_keeps_a_previous_result,
    test_nothing_from_goplus_reaches_the_disk_and_the_home_starts_clean,
    test_the_modules_are_quiet_and_write_nothing,
]


def main() -> int:
    forbid_network()
    for case in CASES:
        case()
    print("v2.50J crypto contract security QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
