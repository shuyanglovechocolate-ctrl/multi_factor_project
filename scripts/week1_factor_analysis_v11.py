"""Run Week 1 v1.1 analysis on the dynamic universe panel."""

from __future__ import annotations

import sys
from pathlib import Path

from week1_factor_test import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    default_args = [
        "week1_factor_test.py",
        "--panel-file",
        str(PROJECT_ROOT / "data" / "processed" / "factor_panel_dynamic.csv"),
        "--output-dir",
        str(PROJECT_ROOT / "outputs" / "week1" / "dynamic_universe"),
        "--group-mode",
        "both",
    ]
    sys.argv = default_args if len(sys.argv) == 1 else sys.argv
    main()
