"""Contract security of a token through GoPlus (v2.50J, phase 5b). Pure functions over injectable transports: no key, no Streamlit, no disk.

What the v2.50H pilot established and this module honours:
  * GoPlus answers without a key but its limits and terms are not documented, and in the pilot only 19 of 48 asked tokens came back with data; for the
    USDT contract it reported `holder_count = 1`. So its answers are evidence, never proof: the verdict is worded "señales graves" / "sin señales
    graves en lo evaluado" / "no verificado" and never "seguro", and a field GoPlus leaves out is "no evaluado" (its documentation: no return = unknown).
  * Run on demand, one coin at a time, with a pause between calls, trying every supported chain of the coin (at most MAX_CHAINS).
  * Nothing from GoPlus is written to disk: the page keeps the result in the session only.
The contract addresses come from CoinGecko (`/coins/{id}`, platforms), cached with the rest of its data (encrypted, 24 h).
"""
from __future__ import annotations

import json
import re
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.parse import quote

from .cache import ProtectedCache
from .coingecko import CoinGeckoClient, CoinGeckoError
from .signals import finite

BASE_URL = "https://api.gopluslabs.io"
MAX_CHAINS = 4
PACE_SECONDS = 0.7
SEVERE_TAX = 0.5  # a buy or sell tax of 50% or more is a trap in practice

# CoinGecko platform id -> GoPlus chain key. "solana" has its own endpoint with another schema.
CHAINS = {
    "ethereum": "1", "binance-smart-chain": "56", "polygon-pos": "137", "arbitrum-one": "42161", "optimistic-ethereum": "10", "base": "8453",
    "avalanche": "43114", "tron": "tron", "fantom": "250", "cronos": "25", "linea": "59144", "mantle": "5000", "blast": "81457", "scroll": "534352",
    "zksync": "324", "solana": "solana",
}
_ADDRESS = {"solana": re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$"), "tron": re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")}
_EVM_ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")

# (key, label) of the unambiguous red flags of an EVM token; "1" means present. fake_token and the taxes are handled apart.
EVM_SEVERE = (
    ("is_honeypot", "honeypot: no se puede vender"), ("cannot_buy", "no se puede comprar"), ("cannot_sell_all", "no se puede vender todo el saldo"),
    ("hidden_owner", "propietario oculto"), ("can_take_back_ownership", "el propietario puede recuperar la propiedad"),
    ("owner_change_balance", "el propietario puede cambiar saldos"), ("selfdestruct", "el contrato puede autodestruirse"), ("is_airdrop_scam", "estafa de airdrop"),
)
EVM_INFO = (
    ("is_mintable", "puede acuñar más unidades"), ("is_proxy", "contrato proxy: su lógica puede cambiar"), ("transfer_pausable", "el propietario puede pausar las transferencias"),
    ("trading_cooldown", "enfriamiento entre operaciones"), ("is_blacklisted", "tiene lista negra"), ("is_whitelisted", "tiene lista blanca"),
    ("is_anti_whale", "límite anti-ballenas"), ("slippage_modifiable", "el propietario puede cambiar el deslizamiento"), ("external_call", "llama a contratos externos"),
)
Transport = Callable[[str, float], tuple[int, dict, bytes]]


class ContractSecurityError(Exception):
    """Safe by construction: a short reason, never a URL or a response body."""


def default_transport(url: str, timeout: float) -> tuple[int, dict, bytes]:
    import certifi

    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers={"User-Agent": "scout-finance-local", "accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()


def valid_address(chain: str, address: Any) -> bool:
    if not isinstance(address, str):
        return False
    pattern = _ADDRESS.get(chain)
    return bool(pattern.match(address)) if pattern else bool(_EVM_ADDRESS.match(address))


def plan_lookups(platforms: Mapping[str, Any], max_chains: int = MAX_CHAINS, primary: str | None = None) -> list[dict]:
    """The (platform, chain, address) triples worth asking GoPlus about: supported chains with a well-formed address, the coin's PRIMARY platform
    (CoinGecko's `asset_platform_id`) first, then the biggest chains. The first chain with data is the one reported, so the order matters: a token
    often has minor deployments elsewhere (a bridged copy with 36 holders is not the token people trade)."""
    lookups = []
    for platform in sorted(platforms):
        chain = CHAINS.get(platform)
        address = platforms[platform]
        if chain is None or not valid_address(chain, address):
            continue
        lookups.append({"platform": platform, "chain": chain, "address": address})
    order = {chain: i for i, chain in enumerate(CHAINS.values())}
    lookups.sort(key=lambda l: (l["platform"] != primary, order.get(l["chain"], 99), l["platform"]))  # the primary platform, then the biggest chains
    return lookups[:max_chains]


def fetch_token_security(chain: str, address: str, transport: Transport | None = None, timeout: float = 20.0) -> dict | None:
    """GoPlus's record for the token, or None when GoPlus has nothing for it (an empty result is common: the pilot got data for ~40% of asks)."""
    path = "/api/v1/solana/token_security" if chain == "solana" else f"/api/v1/token_security/{quote(chain, safe='')}"
    try:
        status, _headers, body = (transport or default_transport)(f"{BASE_URL}{path}?contract_addresses={quote(address, safe='')}", timeout)
    except Exception as error:  # the message could contain the request; keep only the type
        raise ContractSecurityError(f"GoPlus no respondió ({type(error).__name__}).") from None
    if status in (418, 429):
        raise ContractSecurityError("GoPlus limitó el ritmo de peticiones.")
    if status != 200:
        raise ContractSecurityError(f"GoPlus respondió con HTTP {status}.")
    try:
        data = json.loads(body)
    except ValueError:
        raise ContractSecurityError("GoPlus devolvió una respuesta que no es JSON.") from None
    if not isinstance(data, dict) or data.get("code") != 1:
        raise ContractSecurityError("GoPlus no devolvió un resultado válido.")
    result = data.get("result")
    if not isinstance(result, dict) or not result:
        return None
    record = result.get(address) or result.get(address.lower()) or next(iter(result.values()), None)
    return record if isinstance(record, dict) and record else None


# ------------------------------------------------------------------------------------------------------------------------ assessment

def _flag(record: Mapping, key: str) -> bool | None:
    value = record.get(key)
    if value in ("1", 1, True):
        return True
    if value in ("0", 0, False):
        return False
    return None  # omitted or unrecognised: unknown, never "false"


def _status(record: Mapping, key: str) -> bool | None:
    value = record.get(key)
    return _flag(value, "status") if isinstance(value, dict) else None


def _holders(record: Mapping) -> dict:
    rows = []
    for h in (record.get("holders") or [])[:10]:
        if not isinstance(h, dict):
            continue
        percent = finite(h.get("percent"))
        address = str(h.get("address") or h.get("account") or "")
        rows.append({"address": (address[:6] + "…" + address[-4:]) if len(address) > 12 else address, "percent": percent, "tag": str(h.get("tag") or "").strip(),
                     "contract": h.get("is_contract") in (1, "1"), "locked": h.get("is_locked") in (1, "1")})
    percents = [r["percent"] for r in rows if r["percent"] is not None]
    free = [r["percent"] for r in rows if r["percent"] is not None and not r["contract"] and not r["locked"] and not r["tag"]]
    count = finite(record.get("holder_count"))
    return {"count": int(count) if count is not None else None, "top": rows, "top10_share": sum(percents) if percents else None,
            "top10_share_free": sum(free) if rows and percents else None}


def assess(chain: str, record: Mapping) -> dict:
    """Turn a GoPlus record into severe flags, information and holders. A field that GoPlus leaves out is NOT evaluated (never "no problem")."""
    severe: list[str] = []
    info: list[dict] = []
    checks = 0
    evaluated = 0
    notes: list[str] = []
    if chain == "solana":
        solana_severe = (("balance_mutable_authority", "una autoridad puede cambiar los saldos"),)
        checks = len(solana_severe) + 2
        for key, label in solana_severe:
            flag = _status(record, key)
            evaluated += flag is not None
            if flag:
                severe.append(label)
        nt = _flag(record, "non_transferable")
        evaluated += nt is not None
        if nt:
            severe.append("el token no se puede transferir")
        state = str(record.get("default_account_state") or "")
        evaluated += bool(state)
        if state == "2":
            severe.append("las cuentas nuevas nacen congeladas")
        for key, label in (("mintable", "una autoridad puede acuñar más unidades"), ("freezable", "una autoridad puede congelar cuentas"), ("closable", "una autoridad puede cerrar el token"),
                           ("metadata_mutable", "los metadatos pueden cambiarse")):
            flag = _status(record, key)
            if flag:
                info.append({"label": label, "level": "alert" if key in ("mintable", "freezable") else "info"})
        if record.get("transfer_fee"):
            info.append({"label": "cobra una comisión por transferencia", "level": "alert"})
        if record.get("transfer_hook"):
            info.append({"label": "ejecuta un programa externo en cada transferencia", "level": "alert"})
    else:
        checks = len(EVM_SEVERE) + 3  # the flags, fake token, buy tax and sell tax
        open_source = _flag(record, "is_open_source")
        if open_source is False:
            notes.append("El código del contrato no está verificado: GoPlus no pudo evaluar la mayoría de los riesgos.")
            info.append({"label": "código del contrato no verificado", "level": "alert"})
        for key, label in EVM_SEVERE:
            flag = _flag(record, key)
            evaluated += flag is not None
            if flag:
                severe.append(label)
        fake = record.get("fake_token")
        if isinstance(fake, dict) and fake.get("value") in (0, 1, "0", "1"):
            evaluated += 1
            if fake.get("value") in (1, "1"):
                severe.append("token falso: imita a otro")
        for key, name in (("buy_tax", "compra"), ("sell_tax", "venta")):
            tax = finite(record.get(key))
            evaluated += tax is not None
            if tax is not None and tax >= SEVERE_TAX:
                severe.append(f"impuesto de {name} del {tax * 100:.0f} %")
            elif tax is not None and tax > 0:
                info.append({"label": f"impuesto de {name} del {tax * 100:.1f} %".replace(".", ","), "level": "alert" if tax >= 0.1 else "info"})
        for key, label in EVM_INFO:
            if _flag(record, key):
                info.append({"label": label, "level": "alert" if key in ("is_mintable", "transfer_pausable", "is_proxy") else "info"})
        creator = finite(record.get("creator_percent"))
        if creator is not None and creator >= 0.2:
            info.append({"label": f"el creador conserva el {creator * 100:.0f} % del suministro", "level": "alert"})
        if _flag(record, "is_in_dex") is False:
            info.append({"label": "no cotiza en ningún DEX conocido por GoPlus", "level": "info"})
    holders = _holders(record)
    if holders["count"] is not None and holders["count"] <= 1 and holders["top"]:
        notes.append("GoPlus informa de 1 solo tenedor mientras lista varios: dato poco fiable (ya se vio con tokens muy conocidos).")
    if holders["top10_share"] is not None and holders["top10_share"] > 1.05:
        notes.append("Los porcentajes de los mayores tenedores suman más del 100 %: dato poco fiable.")
    return {"kind": "solana" if chain == "solana" else "evm", "severe": severe, "info": info, "evaluated": evaluated, "of": checks, "holders": holders, "notes": notes}


def verdict(assessment: Mapping) -> str:
    """Never "seguro": the most favourable wording is "sin señales graves en lo evaluado"."""
    if assessment["severe"]:
        return "señales graves"
    if assessment["evaluated"] == 0:
        return "sin evaluar"
    return "sin señales graves en lo evaluado" + (" (parcial)" if assessment["evaluated"] < assessment["of"] else "")


# ------------------------------------------------------------------------------------------------------------------------ orchestration

def contract_platforms(client: CoinGeckoClient, cache: ProtectedCache, coin_id: str) -> dict:
    """{"platforms": the coin's contract address on each blockchain platform, "primary": its main platform or None} (CoinGecko `/coins/{id}`; cached
    with the rest of its data, encrypted, 24 h)."""
    name = f"platforms2-{coin_id}"
    hit = cache.get(name)
    if hit is not None:
        return hit[0]
    raw = client.get_json(f"/coins/{quote(coin_id, safe='')}", {"localization": "false", "tickers": "false", "market_data": "false", "community_data": "false",
                                                              "developer_data": "false", "sparkline": "false"})
    platforms = {k: v for k, v in ((raw.get("platforms") or {}) if isinstance(raw, dict) else {}).items() if isinstance(k, str) and k and isinstance(v, str) and v}
    primary = raw.get("asset_platform_id") if isinstance(raw, dict) and isinstance(raw.get("asset_platform_id"), str) and raw.get("asset_platform_id") in platforms else None
    info = {"platforms": platforms, "primary": primary}
    cache.put(name, info)
    return info


def check_contract(client: CoinGeckoClient, cache: ProtectedCache, coin_id: str, *, transport: Transport | None = None, sleep: Callable[[float], None] = time.sleep,
                   max_chains: int = MAX_CHAINS, pace: float = PACE_SECONDS) -> dict:
    """One on-demand check. Always returns a record with a `status`: checked | no_contract | unsupported_chain | no_data | error."""
    base = {"coin_id": coin_id, "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tried": [], "chain": None, "platform": None, "address": None,
            "assessment": None, "verdict": None, "error": None}
    try:
        info = contract_platforms(client, cache, coin_id)
        platforms, primary = info["platforms"], info["primary"]
    except CoinGeckoError as error:
        return base | {"status": "error", "error": f"No se pudieron obtener los contratos de la moneda. {error}"}
    if not platforms:
        return base | {"status": "no_contract"}
    lookups = plan_lookups(platforms, max_chains, primary)
    if not lookups:
        return base | {"status": "unsupported_chain", "platforms": sorted(platforms)}
    tried = []
    for number, lookup in enumerate(lookups):
        if number:
            sleep(pace)
        try:
            record = fetch_token_security(lookup["chain"], lookup["address"], transport)
        except ContractSecurityError as error:
            tried.append({"platform": lookup["platform"], "outcome": str(error)})
            if "ritmo" in str(error):
                break  # a rate limit: stop asking
            continue
        if record is None:
            tried.append({"platform": lookup["platform"], "outcome": "GoPlus no tiene datos de este contrato"})
            continue
        assessment = assess(lookup["chain"], record)
        tried.append({"platform": lookup["platform"], "outcome": "con datos"})
        return base | lookup | {"status": "checked", "tried": tried, "assessment": assessment, "verdict": verdict(assessment), "primary": lookup["platform"] == primary,
                                "other_platforms": sorted(set(platforms) - {lookup["platform"]})}
    only_errors = tried and all(t["outcome"] != "GoPlus no tiene datos de este contrato" for t in tried)
    return base | {"status": "error" if only_errors else "no_data", "tried": tried, "error": tried[-1]["outcome"] if only_errors else None}
