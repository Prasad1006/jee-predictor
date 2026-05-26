#!/usr/bin/env python3
"""Step 2e: Quality checks on master cutoff file."""
from __future__ import annotations

import json

import pandas as pd

from config import MERGED, QUALITY


def main() -> None:
    input_file = MERGED / "master_cutoffs_merged.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Missing {input_file}. Run merge_and_deduplicate.py first.")

    df = pd.read_csv(input_file, low_memory=False)
    total = len(df)

    valid_rank_mask = (df["opening_rank"] <= df["closing_rank"]) | df["opening_rank"].isna()
    valid_ranks = int(valid_rank_mask.sum())

    year_numeric = pd.to_numeric(df["year"], errors="coerce")
    valid_years = int(((year_numeric >= 2016) & (year_numeric <= 2026)).sum())

    unmatched = int(df["needs_manual_review"].sum()) if "needs_manual_review" in df.columns else 0
    matched = total - unmatched

    missing = df.isnull().sum()
    critical_cols = ["institute_canonical", "closing_rank", "year", "category"]
    critical_complete = all(
        (total - int(missing.get(col, 0))) / total >= 0.99 for col in critical_cols if col in df.columns
    )

    quality_report = {
        "total_records": total,
        "checks": {
            "valid_rank_ranges": {
                "valid": valid_ranks,
                "invalid": total - valid_ranks,
                "percentage_valid": round(valid_ranks / total * 100, 2) if total else 0,
            },
            "year_range": {
                "min_year": int(year_numeric.min()) if year_numeric.notna().any() else None,
                "max_year": int(year_numeric.max()) if year_numeric.notna().any() else None,
                "valid_years_count": valid_years,
            },
            "college_match": {
                "matched": matched,
                "unmatched": unmatched,
                "percentage_matched": round(matched / total * 100, 2) if total else 0,
            },
            "critical_columns_complete_99pct": critical_complete,
            "missing_values": {
                col: {
                    "count": int(missing[col]),
                    "percentage": round(float(missing[col] / total * 100), 2),
                }
                for col in missing.index
                if missing[col] > 0
            },
        },
        "quality_gates_passed": {
            "valid_rank_ranges_99": valid_ranks / total >= 0.99 if total else False,
            "college_match_95": matched / total >= 0.95 if total else False,
            "unmatched_under_100_unique": True,  # filled below
        },
    }

    if "institute_raw" in df.columns and unmatched:
        unmatched_df = df[df["needs_manual_review"] == True][["institute_raw"]].drop_duplicates()  # noqa: E712
        quality_report["quality_gates_passed"]["unmatched_under_100_unique"] = len(unmatched_df) < 100
        unmatched_df.to_csv(QUALITY / "unmatched_colleges.csv", index=False)

    report_path = QUALITY / "quality_report.json"
    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(quality_report, file, indent=2)

    print("Quality validation complete.")
    print(json.dumps(quality_report["checks"], indent=2))
    print("Gates:", quality_report["quality_gates_passed"])
    print(f"Report -> {report_path}")


if __name__ == "__main__":
    main()
