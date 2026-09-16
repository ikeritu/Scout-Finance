"""Full suite for v2.44A final stable release closure."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main() -> None:
    run(["scripts/build_final_consolidated_audit_v2_43a.py"])
    run(["tests/qa_final_consolidated_audit_v2_43a.py"])
    run(["scripts/build_final_stable_release_v2_44a.py"])
    run(["tests/qa_final_stable_release_v2_44a.py"])
    print("v2.44A full suite passed")


if __name__ == "__main__":
    main()
