#!/usr/bin/env python3
"""Run the full Step 2 data cleaning pipeline."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

STEPS = [
    "auto_populate_colleges.py",
    "clean_raw_data.py",
    "standardize_columns.py",
    "normalize_colleges.py",
    "merge_and_deduplicate.py",
    "validate_data.py",
]


def run_step(script: str) -> None:
    path = Path(__file__).parent / script
    print(f"\n{'='*60}\n>>> {script}\n{'='*60}")
    result = subprocess.run([sys.executable, str(path)], cwd=path.parent)
    if result.returncode != 0:
        raise SystemExit(f"Pipeline failed at {script} (exit {result.returncode})")


def main() -> None:
    print("JoSAA Data Cleaning Pipeline — Step 2")
    for step in STEPS:
        run_step(step)
    print("\nAll steps completed successfully.")


if __name__ == "__main__":
    main()
