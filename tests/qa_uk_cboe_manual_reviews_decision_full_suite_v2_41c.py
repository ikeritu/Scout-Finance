from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    run_step([sys.executable, "scripts/build_luxembourg_adapter_or_closure_v2_41b.py"])
    run_step([sys.executable, "tests/qa_luxembourg_adapter_or_closure_v2_41b.py"])
    run_step([sys.executable, "scripts/build_uk_cboe_manual_reviews_decision_v2_41c.py"])
    run_step([sys.executable, "tests/qa_uk_cboe_manual_reviews_decision_v2_41c.py"])
    print("v2.41C full suite PASS")


if __name__ == "__main__":
    main()
