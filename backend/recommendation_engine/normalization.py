"""Canonical mappings for categories, branches, and states."""
from __future__ import annotations

# User input -> substrings to match in branch_canonical or program_name
BRANCH_SEARCH_TERMS: dict[str, list[str]] = {
    "CSE": ["COMPUTER_SCIENCE", "COMPUTER SCIENCE", "CSE"],
    "CS": ["COMPUTER_SCIENCE", "COMPUTER SCIENCE", " CSE"],
    "IT": ["INFORMATION_TECHNOLOGY", "INFORMATION TECHNOLOGY", " IT"],
    "ECE": ["ELECTRONICS_AND_COMMUNICATION", "ELECTRONICS AND COMMUNICATION", "ECE"],
    "EEE": ["ELECTRICAL_AND_ELECTRONICS", "ELECTRICAL AND ELECTRONICS", "EEE"],
    "EE": ["ELECTRICAL_ENGINEERING", "ELECTRICAL ENGINEERING", " EE"],
    "ME": ["MECHANICAL_ENGINEERING", "MECHANICAL ENGINEERING", "MECH"],
    "MECH": ["MECHANICAL"],
    "CE": ["CIVIL_ENGINEERING", "CIVIL ENGINEERING", " CIVIL"],
    "CIVIL": ["CIVIL"],
    "CHE": ["CHEMICAL"],
    "AE": ["AEROSPACE"],
    "BT": ["BIOTECH"],
    "BIO": ["BIOTECH"],
    "AI": ["ARTIFICIAL_INTELLIGENCE", "ARTIFICIAL INTELLIGENCE", " AI "],
    "DS": ["DATA_SCIENCE", "DATA SCIENCE"],
    "MATH": ["MATHEMATICS", "MATH"],
    "MCA": ["MCA", "COMPUTER APPLICATIONS"],
}

RANK_TYPE_JEE_MAIN = "JEE_MAIN"  # NIT, IIIT, GFTI — JoSAA uses JEE Main CRL
RANK_TYPE_JEE_ADVANCED = "JEE_ADVANCED"  # IIT only — JoSAA uses JEE Advanced CRL

RANK_TYPE_ALIASES: dict[str, str] = {
    "JEE_MAIN": RANK_TYPE_JEE_MAIN,
    "MAIN": RANK_TYPE_JEE_MAIN,
    "MAINS": RANK_TYPE_JEE_MAIN,
    "JEE_MAINS": RANK_TYPE_JEE_MAIN,
    "JEE_ADVANCED": RANK_TYPE_JEE_ADVANCED,
    "ADVANCED": RANK_TYPE_JEE_ADVANCED,
    "JEE_ADV": RANK_TYPE_JEE_ADVANCED,
    "ADV": RANK_TYPE_JEE_ADVANCED,
}

CATEGORY_ALIASES: dict[str, str] = {
    "GEN": "GENERAL",
    "OPEN": "GENERAL",
    "GENERAL": "GENERAL",
    "OBC": "OBC",
    "OBC-NCL": "OBC",
    "OBC-NCL": "OBC",
    "SC": "SC",
    "ST": "ST",
    "EWS": "EWS",
}

STATE_ALIASES: dict[str, str] = {
    "AP": "Andhra Pradesh",
    "ANDHRA": "Andhra Pradesh",
    "ANDHRA PRADESH": "Andhra Pradesh",
    "TS": "Telangana",
    "TELANGANA": "Telangana",
    "TN": "Tamil Nadu",
    "TAMIL NADU": "Tamil Nadu",
    "KA": "Karnataka",
    "KARNATAKA": "Karnataka",
    "MH": "Maharashtra",
    "MAHARASHTRA": "Maharashtra",
    "UP": "Uttar Pradesh",
    "DELHI": "Delhi",
    "WB": "West Bengal",
    "WEST BENGAL": "West Bengal",
    "KL": "Kerala",
    "KERALA": "Kerala",
    "RJ": "Rajasthan",
    "RAJASTHAN": "Rajasthan",
    "GJ": "Gujarat",
    "GUJARAT": "Gujarat",
}


def normalize_category(raw: str) -> str:
    key = raw.strip().upper()
    return CATEGORY_ALIASES.get(key, key)


def normalize_rank_type(raw: str | None) -> str:
    """JEE_MAIN (NIT/IIIT/GFTI) or JEE_ADVANCED (IIT only)."""
    if not raw:
        return RANK_TYPE_JEE_MAIN
    key = raw.strip().upper().replace("-", "_").replace(" ", "_")
    return RANK_TYPE_ALIASES.get(key, RANK_TYPE_JEE_MAIN)


def rank_type_label(rank_type: str) -> str:
    if rank_type == RANK_TYPE_JEE_ADVANCED:
        return "JEE Advanced rank (IIT)"
    return "JEE Main rank (NIT / IIIT / GFTI)"


def normalize_state(raw: str) -> str:
    if not raw:
        return ""
    key = raw.strip().upper()
    return STATE_ALIASES.get(key, raw.strip().title())


def expand_branch_preferences(preferences: list[str] | None) -> list[str]:
    """Return unique search terms for OR matching on program/branch fields."""
    if not preferences:
        return []
    terms: set[str] = set()
    for pref in preferences:
        key = pref.strip().upper()
        if key in BRANCH_SEARCH_TERMS:
            terms.update(BRANCH_SEARCH_TERMS[key])
        else:
            terms.add(key)
            terms.add(key.replace(" ", "_"))
    return list(terms)


def parse_rank_from_text(text: str) -> int | None:
    """Parse ranks like 20k, 18k rank, 20000."""
    import re

    lower = text.lower()
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*k\b", lower)
    if m:
        return int(float(m.group(1)) * 1000)
    m = re.search(r"\b(\d{1,6})\s*(?:rank|rl)\b", lower, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d{4,6})\b", lower)
    if m and int(m.group(1)) >= 500:
        return int(m.group(1))
    return None


def get_correct_branch_canonical(program_name: str) -> str:
    name = program_name.upper()
    if "COMPUTER SCIENCE" in name or "COMPUTER ENGINEERING" in name or "CSE" in name:
        return "COMPUTER_SCIENCE_AND_ENGINEERING"
    if "ELECTRONICS" in name or "ECE" in name or "TELECOMMUNICATION" in name:
        if "ELECTRICAL AND ELECTRONICS" in name or "ELECTRICAL & ELECTRONICS" in name or "EEE" in name:
            return "ELECTRICAL_AND_ELECTRONICS_ENGINEERING"
        return "ELECTRONICS_AND_COMMUNICATION_ENGINEERING"
    if "ELECTRICAL" in name or "EE " in name or " EE" in name:
        if "ELECTRICAL AND ELECTRONICS" in name or "ELECTRICAL & ELECTRONICS" in name or "EEE" in name:
            return "ELECTRICAL_AND_ELECTRONICS_ENGINEERING"
        return "ELECTRICAL_ENGINEERING"
    if "MECHANICAL" in name or "MECH" in name or "ME " in name or " ME" in name:
        return "MECHANICAL_ENGINEERING"
    if "CIVIL" in name or "CE " in name or " CE" in name:
        return "CIVIL_ENGINEERING"
    if "CHEMICAL" in name or "CHE " in name or " CHE" in name:
        return "CHEMICAL_ENGINEERING"
    if "BIOTECH" in name or "BIO" in name:
        return "BIOTECHNOLOGY"
    if "ARCHITECT" in name or "B.ARCH" in name:
        return "ARCHITECTURE"
    if "DESIGN" in name:
        return "DESIGN"
    if "INFORMATION TECHNOLOGY" in name or "IT " in name or " IT" in name:
        return "INFORMATION_TECHNOLOGY"
    if "MATHEMATICS" in name or "COMPUTING" in name:
        return "MATHEMATICS_AND_COMPUTING"
    if "AEROSPACE" in name or "AERONAUTICAL" in name:
        return "AEROSPACE_ENGINEERING"
    return "OTHER"
