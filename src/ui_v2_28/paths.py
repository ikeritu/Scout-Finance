"""Repository path safety helpers."""
from pathlib import Path

def safe_repo_path(root:Path,value:str)->Path:
 root=root.resolve();raw=str(value or "").replace("\\","/").lstrip("/")
 candidate=(root/raw).resolve()
 try:candidate.relative_to(root)
 except ValueError:raise ValueError("path escapes repository root")
 return candidate

def sha256(path:Path)->str:
 import hashlib
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()
