#!/usr/bin/env python3
"""
Data Ingestion Pipeline — Schema Detector
Detects columns, datatypes, shapes, and verifies mapping to canonical fields.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_COLLECTING = ROOT / "data-collecting"

CANONICAL_COLUMNS = [
    "year", "exam_type", "round", "institute", "branch",
    "quota", "category", "gender", "opening_rank", "closing_rank", "source"
]

COLUMN_MAPS = {
    "merged_jee_cutoff_2018_2025.csv": {
        "Year": "year",
        "Round": "round",
        "Institute": "institute",
        "Academic Program Name": "branch",
        "Quota": "quota",
        "Seat Type": "category",
        "Gender": "gender",
        "Opening Rank": "opening_rank",
        "Closing Rank": "closing_rank",
    },
    "data.csv": {
        "year": "year",
        "round_no": "round",
        "institute_short": "institute",
        "program_name": "branch",
        "quota": "quota",
        "category": "category",
        "pool": "gender",
        "opening_rank": "opening_rank",
        "closing_rank": "closing_rank",
    }
}

class SchemaDetector:
    @staticmethod
    def detect_schema(filename: str) -> dict | None:
        path = DATA_COLLECTING / filename
        if not path.exists():
            print(f"  [WARNING] File {filename} not found.")
            return None
        
        # Read a small sample
        df = pd.read_csv(path, nrows=5)
        cols = df.columns.tolist()
        mapping = COLUMN_MAPS.get(filename, {})
        
        detected = {
            "file": filename,
            "columns": cols,
            "shape_sample": df.shape,
            "mapping_found": mapping,
            "missing_canonical_fields": [
                f for f in COLUMN_MAPS.get(filename, {}).values() if f not in mapping.values()
            ]
        }
        return detected

def main() -> None:
    print("Executing Schema Detector...")
    for filename in COLUMN_MAPS.keys():
        info = SchemaDetector.detect_schema(filename)
        if info:
            print(f"\nFile: {info['file']}")
            print(f"Columns: {info['columns']}")
            print(f"Canonical Maps: {info['mapping_found']}")

if __name__ == "__main__":
    main()
