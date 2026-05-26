"""Shared helpers for data pipeline scripts."""
from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pandas as pd

from config import MAPPINGS


def load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def load_mapping(name: str) -> dict[str, str]:
    """Load a flat string->string mapping from mappings/*.json."""
    data = load_json(MAPPINGS / name)
    for key in ("category_mappings", "quota_mappings", "gender_mappings", "state_mappings"):
        if key in data:
            return data[key]
    return data


def strip_dataframe_strings(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.select_dtypes(include=["object"]).columns:
        out[col] = out[col].astype(str).str.strip()
        out[col] = out[col].replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
    return out


def snake_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [
        re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", col.lower())).strip("_")
        for col in out.columns
    ]
    return out


def extract_canonical_college_name(college_name: str) -> str:
    """Heuristic canonical name for IIT/NIT/IIIT and general institutes."""
    if not college_name or pd.isna(college_name):
        return ""
    college = str(college_name).strip()
    college = re.sub(r"\s+", " ", college)

    replacements = [
        (r"Indian Institute of Technology", "IIT"),
        (r"National Institute of Technology", "NIT"),
        (r"Indian Institute of Information Technology", "IIIT"),
    ]
    for pattern, replacement in replacements:
        college = re.sub(pattern, replacement, college, flags=re.IGNORECASE)

    # Drop trailing location clause after comma for long official names
    if college.count(",") >= 1 and len(college) > 40:
        college = college.split(",")[0].strip()

    college = re.sub(r"\s+", " ", college).strip()
    return college


def identify_college_category(college_name: str) -> str:
    lower = college_name.lower()
    if "iit" in lower and "iiit" not in lower:
        return "IIT"
    if "nit" in lower or "national institute of technology" in lower:
        return "NIT"
    if "iiit" in lower:
        return "IIIT"
    if "deemed" in lower:
        return "Deemed"
    if "university" in lower or "college" in lower:
        return "Other"
    return "Other"


def fuzzy_match(name: str, candidates: list[str], threshold: float = 0.88) -> tuple[str | None, float]:
    if not name:
        return None, 0.0
    best_match: str | None = None
    best_score = 0.0
    name_lower = name.lower()
    for candidate in candidates:
        score = SequenceMatcher(None, name_lower, candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate
    if best_score >= threshold:
        return best_match, best_score
    return None, best_score


_BRANCH_ALIASES: list[tuple[str, str]] | None = None


def _branch_alias_pairs(branch_map: dict[str, str]) -> list[tuple[str, str]]:
    global _BRANCH_ALIASES
    if _BRANCH_ALIASES is None:
        pairs: list[tuple[str, str]] = [(abbrev.upper(), canon) for abbrev, canon in branch_map.items()]
        for canonical, aliases in load_json(MAPPINGS / "canonical_branches.json").get(
            "canonical_branches", {}
        ).items():
            for alias in aliases:
                pairs.append((alias.upper(), canonical))
        _BRANCH_ALIASES = pairs
    return _BRANCH_ALIASES


def normalize_branch(program_name: str, branch_map: dict[str, str]) -> str:
    """Map verbose program string to canonical branch code if possible."""
    if not program_name or pd.isna(program_name):
        return ""
    text = str(program_name).upper()
    for abbrev, canonical in branch_map.items():
        if re.search(rf"\b{re.escape(abbrev)}\b", text):
            return canonical
    for alias, canonical in _branch_alias_pairs(branch_map):
        if alias in text:
            return canonical
    return ""
