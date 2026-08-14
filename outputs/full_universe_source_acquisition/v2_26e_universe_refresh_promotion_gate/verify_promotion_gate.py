#!/usr/bin/env python3
"""Verify the non-mutating v2.26E HOLD decision."""
import argparse, hashlib, json
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,default=Path("."))
    ap.add_argument("--report",type=Path,default=Path("outputs/full_universe_source_acquisition/v2_26e_universe_refresh_promotion_gate/promotion_gate_report.json"))
    args=ap.parse_args()
    root=args.repo_root
    report=json.loads((root/args.report).read_text(encoding="utf-8"))
    before=report["current_pointer_before"]; after=report["current_pointer_after"]
    errors=[]
    if report["promotion_authorized"] or report["promotion_executed"]: errors.append("promotion unexpectedly authorized/executed")
    if before != after: errors.append("report pointer before/after differ")
    pointer=root/before["path"]
    if not pointer.is_file(): errors.append("operational pointer missing")
    elif sha256(pointer)!=before["content_sha256"]: errors.append("operational pointer SHA-256 drift")
    if not any(g["result"] in ("FAIL","HOLD") for g in report["gates"]): errors.append("HOLD lacks blocking gate")
    if errors:
        print("\n".join(errors)); return 1
    print("PASS: v2.26E HOLD is fail-closed and operational pointer is unchanged")
    return 0
if __name__=="__main__": raise SystemExit(main())
