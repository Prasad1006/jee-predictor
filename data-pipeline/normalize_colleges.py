#!/usr/bin/env python3
"""Step 2c: Map institute names to canonical college names."""
from __future__ import annotations

import pandas as pd

from config import MAPPINGS, NORMALIZED, STANDARDIZED
from utils import fuzzy_match, load_json


def load_college_lookup() -> tuple[dict[str, str], list[str]]:
    mapped_path = MAPPINGS / "colleges_auto_mapped.json"
    if not mapped_path.exists():
        raise FileNotFoundError("Run auto_populate_colleges.py first.")

    colleges = load_json(mapped_path)
    exact: dict[str, str] = {}
    for original, meta in colleges.items():
        canonical = meta.get("canonical_name") or original
        exact[original.strip()] = canonical
        exact[canonical.strip()] = canonical

    sample_path = MAPPINGS / "college_names_sample.json"
    if sample_path.exists():
        for original, meta in load_json(sample_path).items():
            canonical = meta.get("canonical_name") or original
            exact[original.strip()] = canonical

    canonical_names = sorted(set(exact.values()))
    return exact, canonical_names


def build_resolution_map(
    unique_names: list[str], exact: dict[str, str], canonical_names: list[str]
) -> dict[str, tuple[str | None, str]]:
    """Resolve each unique institute name once (exact then fuzzy)."""
    resolution: dict[str, tuple[str | None, str]] = {}
    for name in unique_names:
        key = name.strip()
        if key in exact:
            resolution[name] = (exact[key], "EXACT")
            continue
        match, _ = fuzzy_match(key, canonical_names)
        if match:
            resolution[name] = (match, "FUZZY")
        else:
            resolution[name] = (None, "UNMATCHED")
    return resolution


def attach_canonical(
    df: pd.DataFrame, institute_col: str, exact: dict[str, str], canonical_names: list[str]
) -> pd.DataFrame:
    out = df.copy()
    unique_names = [
        str(v).strip()
        for v in out[institute_col].dropna().unique()
        if str(v).strip() and str(v).strip().lower() != "nan"
    ]
    resolution = build_resolution_map(unique_names, exact, canonical_names)

    def resolve(name: object) -> str | None:
        if pd.isna(name):
            return None
        key = str(name).strip()
        return resolution.get(key, (None, "UNMATCHED"))[0]

    def match_type(name: object) -> str:
        if pd.isna(name):
            return "UNMATCHED"
        key = str(name).strip()
        return resolution.get(key, (None, "UNMATCHED"))[1]

    out["institute_canonical"] = out[institute_col].apply(resolve)
    out["match_type"] = out[institute_col].apply(match_type)
    out["needs_manual_review"] = out["institute_canonical"].isna()
    return out


def main() -> None:
    print("Normalizing college names...")
    exact, canonical_names = load_college_lookup()

    merged_path = STANDARDIZED / "std_merged_cutoffs.csv"
    if merged_path.exists():
        df = pd.read_csv(merged_path, low_memory=False)
        df = attach_canonical(df, "institute", exact, canonical_names)
        df.to_csv(NORMALIZED / "merged_cutoffs_normalized.csv", index=False)
        unmatched = int(df["needs_manual_review"].sum())
        print(f"  merged cutoffs: {unmatched} unmatched ({unmatched/len(df)*100:.2f}%)")

    data_path = STANDARDIZED / "std_data.csv"
    if data_path.exists():
        df = pd.read_csv(data_path, low_memory=False)
        df = attach_canonical(df, "institute_short", exact, canonical_names)
        df.to_csv(NORMALIZED / "data_normalized.csv", index=False)
        unmatched = int(df["needs_manual_review"].sum())
        print(f"  data.csv: {unmatched} unmatched ({unmatched/len(df)*100:.2f}%)")

    college_path = STANDARDIZED / "std_college_data.csv"
    if college_path.exists():
        df = pd.read_csv(college_path, low_memory=False)
        col = "college_name" if "college_name" in df.columns else df.columns[0]
        df = attach_canonical(df, col, exact, canonical_names)
        df.to_csv(NORMALIZED / "college_data_normalized.csv", index=False)
        print(f"  college metadata normalized: {len(df)} rows")

    print("College normalization complete.")


if __name__ == "__main__":
    main()
