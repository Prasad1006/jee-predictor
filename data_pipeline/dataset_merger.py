#!/usr/bin/env python3
"""
Data Ingestion Pipeline — Dataset Merger
Reads raw data.csv and merged_jee_cutoff_2018_2025.csv, normalizes fields,
classifies exam and rank types, deduplicates, and saves to master_cutoffs_merged.csv.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from data_pipeline.normalization import PipelineNormalizer
from data_pipeline.rank_classifier import classify_exam_type, classify_rank_type
from data_pipeline.round_validator import RoundValidator
from data_pipeline.duplicate_detector import DuplicateDetector

ROOT = Path(__file__).resolve().parent.parent
DATA_COLLECTING = ROOT / "data-collecting"
OUTPUT_DIR = ROOT / "data-pipeline" / "merged-data"

def merge_datasets() -> None:
    print("🚀 Initializing Dataset Merger...")
    normalizer = PipelineNormalizer()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    frames: list[pd.DataFrame] = []
    
    # 1. Process merged_jee_cutoff_2018_2025.csv
    merged_path = DATA_COLLECTING / "merged_jee_cutoff_2018_2025.csv"
    if merged_path.exists():
        print(f"  Processing {merged_path.name}...")
        df_raw = pd.read_csv(merged_path, low_memory=False)
        
        # Select and map raw columns to standard schema
        df = pd.DataFrame()
        df["institute_raw"] = df_raw["Institute"]
        df["program_name"] = df_raw["Academic Program Name"]
        df["year"] = pd.to_numeric(df_raw["Year"], errors="coerce").fillna(2025).astype(int)
        df["round"] = pd.to_numeric(df_raw["Round"], errors="coerce").fillna(1).astype(int)
        df["category"] = df_raw["Seat Type"]
        df["quota"] = df_raw["Quota"]
        df["gender"] = df_raw["Gender"]
        df["opening_rank"] = pd.to_numeric(df_raw["Opening Rank"], errors="coerce")
        df["closing_rank"] = pd.to_numeric(df_raw["Closing Rank"], errors="coerce")
        df["source"] = "merged_jee_cutoff_2018_2025.csv"
        frames.append(df)
        print(f"    Loaded {len(df)} rows.")

    # 2. Process data.csv
    data_path = DATA_COLLECTING / "data.csv"
    if data_path.exists():
        print(f"  Processing {data_path.name}...")
        df_raw = pd.read_csv(data_path, low_memory=False)
        
        df = pd.DataFrame()
        df["institute_raw"] = df_raw["institute_short"]
        df["program_name"] = df_raw["program_name"]
        df["year"] = pd.to_numeric(df_raw["year"], errors="coerce").fillna(2025).astype(int)
        df["round"] = pd.to_numeric(df_raw["round_no"], errors="coerce").fillna(1).astype(int)
        df["category"] = df_raw["category"]
        df["quota"] = df_raw["quota"]
        df["gender"] = df_raw["pool"]
        df["opening_rank"] = pd.to_numeric(df_raw["opening_rank"], errors="coerce")
        df["closing_rank"] = pd.to_numeric(df_raw["closing_rank"], errors="coerce")
        df["source"] = "data.csv"
        frames.append(df)
        print(f"    Loaded {len(df)} rows.")

    if not frames:
        raise FileNotFoundError("No raw cutoff files found in data-collecting/.")

    # Concatenate
    combined = pd.concat(frames, ignore_index=True)
    print(f"  Total records before deduplication: {len(combined)}")

    # Standardize and Normalize values
    print("  Normalizing column values and mapping colleges...")
    combined["institute_canonical"] = combined["institute_raw"].apply(normalizer.normalize_college)
    combined["branch_canonical"] = combined["program_name"].apply(normalizer.normalize_branch)
    combined["category"] = combined["category"].apply(normalizer.normalize_category)
    combined["quota"] = combined["quota"].apply(normalizer.normalize_quota)
    combined["gender"] = combined["gender"].apply(normalizer.normalize_gender)
    
    # Drop rows with invalid / empty values in critical fields
    combined = combined.dropna(subset=["institute_canonical", "closing_rank"])
    
    # 3. Classify exam_type and rank_type
    print("  Classifying exam types and rank list types...")
    combined["exam_type"] = combined["institute_canonical"].apply(classify_exam_type)
    combined["rank_type"] = combined.apply(
        lambda r: classify_rank_type(r["exam_type"], r["category"]), axis=1
    )

    # 4. Deduplicate
    print("  Detecting and removing duplicates...")
    # Prioritize merged_jee_cutoff rows over data.csv on duplicates
    priority = {"merged_jee_cutoff_2018_2025.csv": 0, "data.csv": 1}
    combined["_source_priority"] = combined["source"].map(priority).fillna(2)
    combined = combined.sort_values("_source_priority").drop(columns=["_source_priority"])
    
    dedup_cols = [
        "institute_canonical",
        "program_name",
        "year",
        "round",
        "category",
        "quota",
        "gender",
    ]
    before_dedup = len(combined)
    combined = combined.drop_duplicates(subset=dedup_cols, keep="first")
    after_dedup = len(combined)
    print(f"    Removed {before_dedup - after_dedup} exact duplicates.")

    # Sort
    combined = combined.sort_values(by=["year", "round", "institute_canonical", "closing_rank"])

    # Output to canonical merged file
    out_path = OUTPUT_DIR / "master_cutoffs_merged.csv"
    combined.to_csv(out_path, index=False)
    print(f"🎉 Merged dataset saved successfully! Total records: {len(combined)}")
    print(f"   Saved at -> {out_path}")

if __name__ == "__main__":
    merge_datasets()
