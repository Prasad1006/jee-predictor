#!/usr/bin/env python3
"""Step 2b: Apply canonical category, quota, gender, state, and branch mappings."""
from __future__ import annotations

import pandas as pd

from config import CLEANED, MAPPINGS, STANDARDIZED
from utils import load_json, load_mapping, strip_dataframe_strings


def _vectorized_branch(
    series: pd.Series, branch_abbrev: dict[str, str], branch_aliases: dict[str, list[str]]
) -> pd.Series:
    """Fast branch tagging on unique program names only."""
    import re

    unique = series.dropna().astype(str).unique()
    lookup: dict[str, str] = {}
    alias_pairs = [(a.upper(), c) for c, aliases in branch_aliases.items() for a in aliases]

    for name in unique:
        text = name.upper()
        found = ""
        for abbrev, canonical in branch_abbrev.items():
            if re.search(rf"\b{re.escape(abbrev)}\b", text):
                found = canonical
                break
        if not found:
            for alias, canonical in alias_pairs:
                if alias in text:
                    found = canonical
                    break
        lookup[name] = found

    return series.astype(str).map(lookup).fillna("")


def apply_map(series: pd.Series, mapping: dict[str, str], default_key: str | None = None) -> pd.Series:
    mapped = series.map(mapping)
    if default_key and default_key in mapping.values():
        default = mapping.get(default_key)
    else:
        default = None
    if default:
        return mapped.fillna(series).fillna(default)
    return mapped.fillna(series)


def standardize_cutoff_frames() -> None:
    category_map = load_mapping("canonical_categories.json")
    quota_map = load_mapping("canonical_quotas.json")
    gender_map = load_json(MAPPINGS / "canonical_gender.json")
    gender_mappings = gender_map["gender_mappings"]
    gender_default = gender_map.get("default", "GENDER_NEUTRAL")
    branches_config = load_json(MAPPINGS / "canonical_branches.json")
    branch_abbrev = branches_config.get("branch_abbreviations", {})
    branch_aliases = branches_config.get("canonical_branches", {})

    # merged_jee_cutoff
    merged_path = CLEANED / "clean_merged_jee_cutoff_2018_2025.csv"
    if merged_path.exists():
        df = pd.read_csv(merged_path, low_memory=False)
        df["seat_type"] = apply_map(df["seat_type"], category_map)
        df["quota"] = apply_map(df["quota"], quota_map)
        df["gender"] = df["gender"].map(gender_mappings).fillna(gender_default)
        df["branch_canonical"] = _vectorized_branch(df["academic_program_name"], branch_abbrev, branch_aliases)
        df.to_csv(STANDARDIZED / "std_merged_cutoffs.csv", index=False)
        print(f"  standardized merged cutoffs: {len(df)} rows")

    # data.csv
    data_path = CLEANED / "clean_data.csv"
    if data_path.exists():
        df = pd.read_csv(data_path, low_memory=False)
        df["category"] = apply_map(df["category"], category_map)
        df["quota"] = apply_map(df["quota"], quota_map)
        if "pool" in df.columns:
            df["gender"] = df["pool"].map(gender_mappings).fillna(gender_default)
        df["branch_canonical"] = _vectorized_branch(df["program_name"], branch_abbrev, branch_aliases)
        df.to_csv(STANDARDIZED / "std_data.csv", index=False)
        print(f"  standardized data.csv: {len(df)} rows")

    # College metadata
    college_path = CLEANED / "clean_College_data.csv"
    if college_path.exists():
        df = pd.read_csv(college_path, low_memory=False)
        state_map = load_mapping("canonical_states.json")
        if "state" in df.columns:
            df["state"] = apply_map(df["state"], state_map)
        df.to_csv(STANDARDIZED / "std_college_data.csv", index=False)
        print(f"  standardized college data: {len(df)} rows")

    fees_path = CLEANED / "clean_Top_Indian_Colleges_Fees_Placement.csv"
    if fees_path.exists():
        df = pd.read_csv(fees_path, low_memory=False)
        df = strip_dataframe_strings(df)
        df.to_csv(STANDARDIZED / "std_fees_placement.csv", index=False)
        print(f"  copied fees/placement: {len(df)} rows")


def main() -> None:
    print("Standardizing columns...")
    standardize_cutoff_frames()
    print("Column standardization complete.")


if __name__ == "__main__":
    main()
