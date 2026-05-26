#!/usr/bin/env python3
"""
Data Ingestion Pipeline — Duplicate Detector
Identifies duplicate records in cutoff datasets to preserve data integrity and prevent redundant DB rows.
"""
from __future__ import annotations

import pandas as pd

class DuplicateDetector:
    @staticmethod
    def audit_duplicates(df: pd.DataFrame) -> dict:
        dup_cols = [
            "institute_canonical",
            "program_name",
            "year",
            "round",
            "category",
            "quota",
            "gender",
        ]
        
        # Ensure we only check columns that exist
        existing_cols = [c for c in dup_cols if c in df.columns]
        if not existing_cols:
            return {"error": "No matching deduplication columns found."}
            
        duplicates = df.duplicated(subset=existing_cols, keep=False)
        total_dup = int(df.duplicated(subset=existing_cols, keep="first").sum())
        
        return {
            "total_records": len(df),
            "duplicates_removed_estimate": total_dup,
            "duplicate_percentage": round((total_dup / len(df) * 100), 2) if len(df) else 0
        }

def main() -> None:
    print("Duplicate Detector loaded.")

if __name__ == "__main__":
    main()
