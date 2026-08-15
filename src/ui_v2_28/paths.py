"""Repository path safety helpers."""
from pathlib import Path
def safe_repo_path(root:Path,value:str)->Path:
 root=root.resolve();raw=str(value or "").replace("\\","/").lstrip("/");candidate=(root/raw).resolve()
 try:candidate.relative_to(root)
 except ValueError:raise ValueError("path escapes repository root")
 return candidate
def sha256(path:Path)->str:
 import hashlib
 h=hashlib.sha256()
 with path.open("rb") as handle:
  for chunk in iter(lambda:handle.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def sha256_matches(path:Path,expected:str,allow_csv_eol_normalization=False)->bool:
 actual=sha256(path)
 if actual==expected:return True
 if not allow_csv_eol_normalization or path.suffix.lower()!=".csv":return False
 import hashlib
 raw=path.read_bytes()
 if b"\r" in raw:return False
 return hashlib.sha256(raw.replace(b"\n",b"\r\n")).hexdigest()==expected
