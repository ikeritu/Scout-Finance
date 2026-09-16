"""Full chained QA for v2.42B final in-app responsible-use guide."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(args: list[str]) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    run_step([sys.executable, "scripts/build_final_ux_hardening_v2_42a.py"])
    run_step([sys.executable, "tests/qa_final_ux_hardening_v2_42a.py"])
    run_step([sys.executable, "scripts/build_final_in_app_guide_v2_42b.py"])
    run_step([sys.executable, "tests/qa_final_in_app_guide_v2_42b.py"])
    print("v2.42B full suite passed")


if __name__ == "__main__":
    main()
