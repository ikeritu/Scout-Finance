#!/usr/bin/env python3
import hashlib,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ui_v2_28.paths import sha256_matches
def main():
 with tempfile.TemporaryDirectory() as td:
  path=Path(td)/"universe.csv";lf=b"ticker,name\nABC,Alpha\n";crlf=lf.replace(b"\n",b"\r\n");expected=hashlib.sha256(crlf).hexdigest();path.write_bytes(lf)
  assert sha256_matches(path,expected,True);assert not sha256_matches(path,expected,False)
  path.write_bytes(lf.replace(b"Alpha",b"Altered"));assert not sha256_matches(path,expected,True)
  txt=Path(td)/"file.txt";txt.write_bytes(lf);assert not sha256_matches(txt,expected,True)
 print("PASS: exact-hash/CSV-LF-CRLF-compatibility/content-tamper/non-CSV-strict");return 0
if __name__=="__main__":raise SystemExit(main())
