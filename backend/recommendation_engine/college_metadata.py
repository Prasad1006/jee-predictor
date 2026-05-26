"""Infer institute category and state from canonical college names."""
from __future__ import annotations

import re

# Substrings in canonical names → Indian state (title case for UI)
_CITY_STATE: list[tuple[str, str]] = [
    ("Tiruchirappalli", "Tamil Nadu"),
    ("Trichy", "Tamil Nadu"),
    ("Chennai", "Tamil Nadu"),
    ("Sri City", "Andhra Pradesh"),
    ("Chittoor", "Andhra Pradesh"),
    ("Hyderabad", "Telangana"),
    ("Warangal", "Telangana"),
    ("Bangalore", "Karnataka"),
    ("Bengaluru", "Karnataka"),
    ("Mysore", "Karnataka"),
    ("Mysuru", "Karnataka"),
    ("Delhi", "Delhi"),
    ("Gwalior", "Madhya Pradesh"),
    ("Bhopal", "Madhya Pradesh"),
    ("Indore", "Madhya Pradesh"),
    ("Jabalpur", "Madhya Pradesh"),
    ("Kota", "Rajasthan"),
    ("Jaipur", "Rajasthan"),
    ("Udaipur", "Rajasthan"),
    ("Pune", "Maharashtra"),
    ("Mumbai", "Maharashtra"),
    ("Nagpur", "Maharashtra"),
    ("Kalyani", "West Bengal"),
    ("Kolkata", "West Bengal"),
    ("Guwahati", "Assam"),
    ("Agartala", "Tripura"),
    ("Raipur", "Chhattisgarh"),
    ("Bhubaneswar", "Odisha"),
    ("Ranchi", "Jharkhand"),
    ("Patna", "Bihar"),
    ("Allahabad", "Uttar Pradesh"),
    ("Prayagraj", "Uttar Pradesh"),
    ("Lucknow", "Uttar Pradesh"),
    ("Kanpur", "Uttar Pradesh"),
    ("Varanasi", "Uttar Pradesh"),
    ("Gorakhpur", "Uttar Pradesh"),
    ("Amritsar", "Punjab"),
    ("Chandigarh", "Chandigarh"),
    ("Shimla", "Himachal Pradesh"),
    ("Hamirpur", "Himachal Pradesh"),
    ("Srinagar", "Jammu and Kashmir"),
    ("Jammu", "Jammu and Kashmir"),
    ("Imphal", "Manipur"),
    ("Senapati", "Manipur"),
    ("Kottayam", "Kerala"),
    ("Thiruvananthapuram", "Kerala"),
    ("Palakkad", "Kerala"),
    ("Surat", "Gujarat"),
    ("Vadodara", "Gujarat"),
    ("Gandhinagar", "Gujarat"),
    ("Ahmedabad", "Gujarat"),
    ("Dharwad", "Karnataka"),
    ("Una", "Himachal Pradesh"),
    ("Sonepat", "Haryana"),
    ("Kurnool", "Andhra Pradesh"),
    ("Naya Raipur", "Chhattisgarh"),
    ("Bhopal", "Madhya Pradesh"),
    ("Nagaland", "Nagaland"),
    ("Meghalaya", "Meghalaya"),
    ("Shillong", "Meghalaya"),
    ("Manipur", "Manipur"),
    ("Tripura", "Tripura"),
    ("Sri Lanka", ""),  # skip false positives
]


def infer_college_category(name: str) -> str:
    """Return IIT | NIT | IIIT | GFTI | Deemed."""
    if not name or len(name.strip()) < 3:
        return "GFTI"
    u = name.upper()
    if (
        "INDIAN INSTITUTE OF TECHNOLOGY" in u
        or re.search(r"\bIIT[\s,(]", u)
        or u.startswith("IIT ")
    ):
        return "IIT"
    if (
        "NATIONAL INSTITUTE OF TECHNOLOGY" in u
        or re.search(r"\bNIT[\s,(]", u)
        or u.startswith("NIT ")
    ):
        return "NIT"
    if (
        "INDIAN INSTITUTE OF INFORMATION TECHNOLOGY" in u
        or re.search(r"\bIIIT[\s,(]", u)
        or re.search(r"\bIIIT\b", u)
        or u.startswith("IIIT ")
        or "IIIT)" in u
        or "(IIIT)" in u
    ):
        return "IIIT"
    if "DEEMED" in u or "BITS" in u:
        return "Deemed"
    return "GFTI"


def infer_college_state(name: str) -> str:
    """Best-effort state from city tokens in the institute name."""
    if not name:
        return ""
    for city, state in _CITY_STATE:
        if city.lower() in name.lower() and state:
            return state
    return ""
