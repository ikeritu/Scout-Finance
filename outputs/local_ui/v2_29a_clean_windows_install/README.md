# v2.29A — Clean Windows Installation

Status: **COMPLETE**

- Minimal UI-only dependency set added.
- PowerShell installer creates `.venv`, installs dependencies and optionally launches Streamlit.
- Preflight verifier checks Python, required files, dependencies, pointer containment, universe row count, dataset existence/SHA-256 and scoring fail-closed state.
- Tampered datasets and path traversal fail the installation gate.
- Stable v2.28 application and operational pointers remain unchanged.

Validation: `python tests/qa_clean_windows_install_v2_29a.py`

Expected: `PASS: clean-install/requirements/python/pointers/hash/path-safety/fail-closed/tamper-detection`
