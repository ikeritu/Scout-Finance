from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    run_step([sys.executable, "scripts/build_controlled_external_publication_qa_v2_40d.py"])
    run_step([sys.executable, "tests/qa_controlled_external_publication_qa_v2_40d.py"])
    run_step([sys.executable, "scripts/build_data_gap_prioritization_v2_41a.py"])
    run_step([sys.executable, "tests/qa_data_gap_prioritization_v2_41a.py"])
    print("v2.41A full suite PASS")


if __name__ == "__main__":
    main()
