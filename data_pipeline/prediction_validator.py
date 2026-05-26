#!/usr/bin/env python3
"""
Data Ingestion Pipeline — Prediction Validator
Runs quality assurance checks on the merged cutoff dataset.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data-pipeline" / "merged-data" / "master_cutoffs_merged.csv"

def run_assertions() -> bool:
    if not CSV_PATH.exists():
        print(f"  [ERROR] Merged dataset not found at {CSV_PATH}. Run dataset_merger.py first.")
        return False
        
    df = pd.read_csv(CSV_PATH, low_memory=False)
    print(f"\n🔍 Running Prediction Validation Engine on {len(df)} records...")
    
    passed = True
    
    # 1. IITs should ONLY use JEE Advanced data (exclude IIITs)
    iits = df[df["institute_canonical"].str.contains("Indian Institute of Technology", case=False, na=False) & 
              ~df["institute_canonical"].str.contains("Information Technology|IIIT", case=False, na=False)]
    non_advanced_iits = iits[iits["exam_type"] != "JEE_ADVANCED"]
    if not non_advanced_iits.empty:
        print(f"  ❌ Assertion Failed: Found {len(non_advanced_iits)} IIT rows not marked as JEE_ADVANCED! Sample: {non_advanced_iits['institute_canonical'].unique()[:5]}")
        passed = False
    else:
        print("  ✓ Assertion Passed: All IIT rows are classified as JEE_ADVANCED.")

    # 2. NITs/IIITs should use JEE Main data
    nits_iiits = df[df["institute_canonical"].str.contains("National Institute of Technology|NIT|IIIT|Information Technology|Carpet|Handloom", case=False, na=False)]
    non_main = nits_iiits[nits_iiits["exam_type"] != "JEE_MAIN"]
    if not non_main.empty:
        print(f"  ❌ Assertion Failed: Found {len(non_main)} NIT/IIIT rows not marked as JEE_MAIN! Sample: {non_main['institute_canonical'].unique()[:5]}")
        passed = False
    else:
        print("  ✓ Assertion Passed: All NIT/IIIT/GFTI rows are classified as JEE_MAIN.")

    # 3. IITs should only use JEE_ADVANCED rank types
    invalid_iit_ranks = iits[~iits["rank_type"].str.startswith("JEE_ADVANCED")]
    if not invalid_iit_ranks.empty:
        print(f"  ❌ Assertion Failed: Found {len(invalid_iit_ranks)} IIT rows with non-Advanced rank types: {invalid_iit_ranks['rank_type'].unique()}")
        passed = False
    else:
        print("  ✓ Assertion Passed: IIT rows strictly use JEE_ADVANCED rank types.")

    # 4. NIT/IIITs should only use JEE_MAIN rank types
    invalid_nit_ranks = nits_iiits[~nits_iiits["rank_type"].str.startswith("JEE_MAIN")]
    if not invalid_nit_ranks.empty:
        print(f"  ❌ Assertion Failed: Found {len(invalid_nit_ranks)} NIT/IIIT rows with non-Main rank types: {invalid_nit_ranks['rank_type'].unique()}")
        passed = False
    else:
        print("  ✓ Assertion Passed: NIT/IIIT rows strictly use JEE_MAIN rank types.")

    # 5. Check rank range validity (closing rank must be >= opening rank if both present)
    invalid_ranges = df[df["opening_rank"] > df["closing_rank"]]
    if not invalid_ranges.empty:
        print(f"  ⚠️ Warning: Found {len(invalid_ranges)} rows where opening rank exceeds closing rank.")
        # Do not fail for warnings, some official reports contain anomalies
    else:
        print("  ✓ Assertion Passed: All opening ranks are <= closing ranks.")

    if passed:
        print("\n🎉 ALL PIPELINE VALIDATION GATES PASSED SUCCESSFULLY! Data integrity verified.")
    else:
        print("\n❌ PIPELINE VALIDATION FAILED! Check schema classification rules.")
        
    return passed

if __name__ == "__main__":
    run_assertions()
