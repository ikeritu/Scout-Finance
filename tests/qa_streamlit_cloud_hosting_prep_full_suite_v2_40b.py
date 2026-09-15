from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    run_step([sys.executable, "scripts/build_publication_decision_v2_40a.py"])
    run_step([sys.executable, "tests/qa_publication_decision_v2_40a.py"])
    run_step([sys.executable, "scripts/build_streamlit_cloud_hosting_prep_v2_40b.py"])
    run_step([sys.executable, "tests/qa_streamlit_cloud_hosting_prep_v2_40b.py"])
    print("v2.40B full suite PASS")


if __name__ == "__main__":
    main()
