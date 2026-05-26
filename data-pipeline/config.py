"""Paths and directories for the data cleaning pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_COLLECTING = ROOT / "data-collecting"
PIPELINE = ROOT / "data-pipeline"
MAPPINGS = PIPELINE / "mappings"

CLEANED = PIPELINE / "cleaned-data"
STANDARDIZED = PIPELINE / "standardized-data"
NORMALIZED = PIPELINE / "normalized-data"
MERGED = PIPELINE / "merged-data"
QUALITY = PIPELINE / "quality"

for directory in (CLEANED, STANDARDIZED, NORMALIZED, MERGED, QUALITY):
    directory.mkdir(parents=True, exist_ok=True)

PRIMARY_CSV_FILES = [
    "merged_jee_cutoff_2018_2025.csv",
    "data.csv",
    "College_data.csv",
    "Top_Indian_Colleges_Fees_Placement.csv",
]
