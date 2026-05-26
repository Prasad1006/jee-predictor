#!/usr/bin/env python3
"""
Data Ingestion Pipeline — Normalization
Standardizes raw college names, branch names, seat categories, quotas, and genders using mapped JSON assets.
"""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MAPPINGS = ROOT / "data-pipeline" / "mappings"

class PipelineNormalizer:
    def __init__(self) -> None:
        self.category_map = self._load_mapping("canonical_categories.json")
        self.quota_map = self._load_mapping("canonical_quotas.json")
        self.gender_map = self._load_json("canonical_gender.json")
        self.college_map = self._load_json("colleges_auto_mapped.json")
        self.branches_config = self._load_json("canonical_branches.json")

    def _load_mapping(self, filename: str) -> dict:
        path = MAPPINGS / filename
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
            # Standard mappings in the app are key-value
            if isinstance(raw, list):
                return {x[0]: x[1] for x in raw if len(x) >= 2}
            return raw

    def _load_json(self, filename: str) -> dict:
        path = MAPPINGS / filename
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def normalize_college(self, raw_name: str) -> str:
        name = str(raw_name).strip()
        if name in self.college_map:
            return self.college_map[name].get("canonical_name", name)
        return name

    def normalize_branch(self, program_name: str) -> str:
        """Tag canonical branch based on search rules in branches config."""
        import re
        text = str(program_name).upper()
        
        branch_abbrev = self.branches_config.get("branch_abbreviations", {})
        branch_aliases = self.branches_config.get("canonical_branches", {})
        
        for abbrev, canonical in branch_abbrev.items():
            if re.search(rf"\b{re.escape(abbrev)}\b", text):
                return canonical
                
        alias_pairs = [(a.upper(), c) for c, aliases in branch_aliases.items() for a in aliases]
        for alias, canonical in alias_pairs:
            if alias in text:
                return canonical
                
        return ""

    def normalize_category(self, raw_cat: str) -> str:
        cat = str(raw_cat).strip().upper()
        mapped = self.category_map.get(cat, cat)
        # Standardize representation to common values
        if "OBC" in mapped:
            return "OBC"
        if "EWS" in mapped:
            return "EWS"
        if "SC" in mapped:
            return "SC"
        if "ST" in mapped:
            return "ST"
        if mapped in ("OPEN", "GENERAL", "GEN"):
            return "GENERAL"
        return mapped

    def normalize_quota(self, raw_quota: str) -> str:
        quota = str(raw_quota).strip().upper()
        return self.quota_map.get(quota, quota)

    def normalize_gender(self, raw_gender: str) -> str:
        gender = str(raw_gender).strip().upper()
        gender_mappings = self.gender_map.get("gender_mappings", {})
        gender_default = self.gender_map.get("default", "GENDER_NEUTRAL")
        return gender_mappings.get(gender, gender_default)

def main() -> None:
    print("Normalization pipeline loaded.")

if __name__ == "__main__":
    main()
