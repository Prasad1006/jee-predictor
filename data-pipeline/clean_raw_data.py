#!/usr/bin/env python3
"""Step 2a: Load raw CSVs, strip strings, normalize column names."""
from __future__ import annotations

import pandas as pd

from config import CLEANED, DATA_COLLECTING, PRIMARY_CSV_FILES
from utils import snake_columns, strip_dataframe_strings


def clean_file(filename: str) -> None:
    path = DATA_COLLECTING / filename
    if not path.exists():
        print(f"  skip (missing): {filename}")
        return

    df = pd.read_csv(path, low_memory=False)
    df = strip_dataframe_strings(df)
    df = snake_columns(df)

    out_path = CLEANED / f"clean_{filename}"
    df.to_csv(out_path, index=False)
    print(f"  cleaned {filename}: {df.shape[0]} rows, {df.shape[1]} cols -> {out_path.name}")


def main() -> None:
    print("Cleaning raw CSV files...")
    for filename in PRIMARY_CSV_FILES:
        clean_file(filename)
    print("Raw data cleaning complete.")


if __name__ == "__main__":
    main()
