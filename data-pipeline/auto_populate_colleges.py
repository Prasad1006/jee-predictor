#!/usr/bin/env python3
"""Auto-populate canonical college names in mapping JSON."""
from __future__ import annotations

import json

from config import MAPPINGS
from utils import extract_canonical_college_name, identify_college_category, load_json


def main() -> None:
    source = MAPPINGS / "all_colleges_to_canonicalize.json"
    colleges = load_json(source)
    state_map = load_json(MAPPINGS / "canonical_states.json").get("state_mappings", {})

    updated = 0
    for name, entry in colleges.items():
        if not entry.get("canonical_name"):
            entry["canonical_name"] = extract_canonical_college_name(name)
            updated += 1
        if not entry.get("category"):
            entry["category"] = identify_college_category(name)

        # Try to infer state from substring in college name
        if not entry.get("state"):
            for variant, canonical_state in state_map.items():
                if len(variant) > 3 and variant.lower() in name.lower():
                    entry["state"] = canonical_state
                    break

    output = MAPPINGS / "colleges_auto_mapped.json"
    with open(output, "w", encoding="utf-8") as file:
        json.dump(colleges, file, indent=2, ensure_ascii=False)

    print(f"Auto-mapped {updated} colleges -> {output}")


if __name__ == "__main__":
    main()
