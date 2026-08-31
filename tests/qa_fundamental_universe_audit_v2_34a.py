#!/usr/bin/env python3
"""QA gate for the phase-5 fundamentals universe manifest (block A). No
network calls; reads only local phase-4 artifacts already in the repo.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location("prepare_fundamental_universe_v2_34a", ROOT / "scripts/prepare_fundamental_universe_v2_34a.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    mod = module()
    manifest = mod.build_manifest()
    assert len(manifest) == 50, f"expected 50 assets, got {len(manifest)}"

    jpx = [r for r in manifest if r["exchange"] == "JPX"]
    twse = [r for r in manifest if r["exchange"] == "TWSE"]
    assert len(jpx) == 42 and len(twse) == 8

    assert all(r["identity_status"] == "identity_verified" for r in manifest), "every asset must be identity_verified per A.3"
    assert all(r["company_name"].strip() for r in manifest), "no asset may have an empty company name"
    assert all(r["fundamentals_eligible"] for r in manifest)
    assert len({r["asset_id"] for r in manifest}) == 50, "asset_id must be unique"

    # No fabricated identifiers: ISIN/LEI must be honestly empty, not guessed.
    assert all(r["isin"] == "" for r in manifest)
    assert all(r["lei"] == "" for r in manifest)

    # Reproducibility.
    manifest2 = mod.build_manifest()
    assert manifest == manifest2, "manifest is not reproducible across runs"

    print(json.dumps({"assets": len(manifest), "jpx": len(jpx), "twse": len(twse)}, ensure_ascii=False))
    print("PASS: v2.34A-fundamental-universe/50-assets/identity-verified/reproducible/no-fabricated-ids")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
