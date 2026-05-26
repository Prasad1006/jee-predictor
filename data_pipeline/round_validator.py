#!/usr/bin/env python3
"""
Data Ingestion Pipeline — Round Validator
Checks rounds for valid integer ranges (1-7), identifies maximum rounds per year, and checks for inconsistencies.
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_COLLECTING = ROOT / "data-collecting"

class RoundValidator:
    @staticmethod
    def get_round_summary(df: pd.DataFrame, round_col: str, year_col: str) -> dict:
        # Convert columns to numeric if possible
        rounds = pd.to_numeric(df[round_col], errors="coerce")
        years = pd.to_numeric(df[year_col], errors="coerce")
        
        # Unique years and max rounds mapping
        max_rounds = {}
        for y in df[year_col].dropna().unique():
            y_int = int(float(y))
            y_df = df[df[year_col] == y]
            max_r = int(pd.to_numeric(y_df[round_col], errors="coerce").max())
            max_rounds[y_int] = max_r
            
        invalid_rounds = int(rounds.isna().sum() + ((rounds < 1) | (rounds > 7)).sum())
        
        return {
            "max_rounds_per_year": max_rounds,
            "invalid_rounds_count": invalid_rounds,
            "unique_rounds": sorted(df[round_col].dropna().unique().tolist())
        }

def main() -> None:
    print("Round Validator loaded.")

if __name__ == "__main__":
    main()
