"""Full chained QA for v2.41D final coverage limitations."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(args: list[str]) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    run_step([sys.executable, "scripts/build_uk_cboe_manual_reviews_decision_v2_41c.py"])
    run_step([sys.executable, "tests/qa_uk_cboe_manual_reviews_decision_v2_41c.py"])
    run_step([sys.executable, "scripts/build_final_coverage_limitations_v2_41d.py"])
    run_step([sys.executable, "tests/qa_final_coverage_limitations_v2_41d.py"])
    print("v2.41D full suite passed")


if __name__ == "__main__":
    main()
