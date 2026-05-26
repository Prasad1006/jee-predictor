#!/usr/bin/env python3
"""Step 2d: Unify cutoff datasets into one master CSV."""
from __future__ import annotations

import json

import pandas as pd

from config import MERGED, NORMALIZED


def to_master_schema(df: pd.DataFrame, source: str, institute_col: str, program_col: str) -> pd.DataFrame:
    round_col = "round" if "round" in df.columns else "round_no"
    return pd.DataFrame(
        {
            "institute_raw": df[institute_col],
            "institute_canonical": df.get("institute_canonical"),
            "program_name": df[program_col],
            "branch_canonical": df.get("branch_canonical"),
            "year": pd.to_numeric(df["year"], errors="coerce"),
            "round": df[round_col],
            "category": df.get("seat_type", df.get("category")),
            "quota": df["quota"],
            "gender": df.get("gender"),
            "opening_rank": pd.to_numeric(df["opening_rank"], errors="coerce"),
            "closing_rank": pd.to_numeric(df["closing_rank"], errors="coerce"),
            "match_type": df.get("match_type"),
            "needs_manual_review": df.get("needs_manual_review"),
            "source": source,
        }
    )


def main() -> None:
    print("Merging and deduplicating...")
    frames: list[pd.DataFrame] = []

    merged_path = NORMALIZED / "merged_cutoffs_normalized.csv"
    if merged_path.exists():
        df = pd.read_csv(merged_path, low_memory=False)
        frames.append(
            to_master_schema(
                df,
                source="merged_jee_cutoff_2018_2025",
                institute_col="institute",
                program_col="academic_program_name",
            )
        )

    data_path = NORMALIZED / "data_normalized.csv"
    if data_path.exists():
        df = pd.read_csv(data_path, low_memory=False)
        frames.append(
            to_master_schema(
                df,
                source="data.csv",
                institute_col="institute_short",
                program_col="program_name",
            )
        )

    if not frames:
        raise FileNotFoundError("No normalized cutoff files found. Run normalize_colleges.py first.")

    combined = pd.concat(frames, ignore_index=True)
    before = len(combined)

    dedup_cols = [
        "institute_canonical",
        "program_name",
        "year",
        "round",
        "category",
        "quota",
        "gender",
        "opening_rank",
        "closing_rank",
    ]
    # Prefer merged_jee_cutoff rows over data.csv on duplicates
    priority = {"merged_jee_cutoff_2018_2025": 0, "data.csv": 1}
    combined["_source_priority"] = combined["source"].map(priority).fillna(2)
    combined = combined.sort_values("_source_priority").drop(columns=["_source_priority"])
    combined = combined.drop_duplicates(subset=dedup_cols, keep="first")
    after = len(combined)

    out_path = MERGED / "master_cutoffs_merged.csv"
    combined.to_csv(out_path, index=False)

    report = {
        "total_records_before": before,
        "total_records_after": after,
        "duplicates_removed": before - after,
        "dedup_percentage": round((before - after) / before * 100, 4) if before else 0,
    }
    with open(MERGED / "dedup_report.json", "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print(f"  merged {after} records ({before - after} duplicates removed)")
    print(f"  saved -> {out_path}")


if __name__ == "__main__":
    main()
