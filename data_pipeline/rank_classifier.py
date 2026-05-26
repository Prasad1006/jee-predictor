#!/usr/bin/env python3
"""
Data Ingestion Pipeline — Rank Classifier
Deterministically classifies JoSAA cutoffs into exact rank list types:
- JEE_MAIN_CRL / JEE_MAIN_OBC / JEE_MAIN_SC / JEE_MAIN_ST / JEE_MAIN_EWS
- JEE_ADVANCED_CRL / JEE_ADVANCED_OBC / JEE_ADVANCED_SC / JEE_ADVANCED_ST / JEE_ADVANCED_EWS
"""
from __future__ import annotations

def classify_exam_type(institute_name: str) -> str:
    """IITs use JEE Advanced; NITs, IIITs, GFTIs use JEE Main."""
    name_upper = institute_name.upper()
    if (
        "INDIAN INSTITUTE OF TECHNOLOGY" in name_upper
        or name_upper.startswith("IIT ")
        or name_upper.startswith("IIT,")
    ):
        return "JEE_ADVANCED"
    return "JEE_MAIN"

def classify_rank_type(exam_type: str, category: str) -> str:
    """
    Ranks for OPEN seats are CRL.
    Ranks for specific category seats are category-specific ranks.
    """
    cat_upper = category.strip().upper()
    
    # Map category string to suffix
    if cat_upper in ("OPEN", "GENERAL", "GEN-EWS"):
        if "EWS" in cat_upper:
            suffix = "EWS"
        else:
            suffix = "CRL"
    elif "OBC" in cat_upper:
        suffix = "OBC"
    elif "SC" in cat_upper:
        suffix = "SC"
    elif "ST" in cat_upper:
        suffix = "ST"
    elif "EWS" in cat_upper:
        suffix = "EWS"
    else:
        suffix = "CRL"
        
    return f"{exam_type}_{suffix}"

def main() -> None:
    print("Testing Rank Classifier...")
    test_cases = [
        ("Indian Institute of Technology Bombay", "OPEN"),
        ("Indian Institute of Technology Bombay", "OBC-NCL"),
        ("National Institute of Technology Trichy", "OPEN"),
        ("National Institute of Technology Trichy", "SC"),
    ]
    for inst, cat in test_cases:
        exam = classify_exam_type(inst)
        rank = classify_rank_type(exam, cat)
        print(f"Institute: {inst} | Cat: {cat} -> Exam: {exam} | Rank Type: {rank}")

if __name__ == "__main__":
    main()
