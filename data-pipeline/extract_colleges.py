#!/usr/bin/env python3
"""
Extract all unique college names from datasets for canonicalization
"""

import os
import pandas as pd
import json

data_dir = r"c:\Users\prasa\OneDrive\Desktop\jee-predictor-copilot\data-collecting"

# Extract all unique college names
all_colleges = set()

# From data.csv
df1 = pd.read_csv(os.path.join(data_dir, 'data.csv'))
if 'institute_short' in df1.columns:
    all_colleges.update(df1['institute_short'].dropna().unique())

# From merged_jee_cutoff_2018_2025.csv
df2 = pd.read_csv(os.path.join(data_dir, 'merged_jee_cutoff_2018_2025.csv'))
if 'Institute' in df2.columns:
    all_colleges.update(df2['Institute'].dropna().unique())

# From College_data.csv
df3 = pd.read_csv(os.path.join(data_dir, 'College_data.csv'))
if 'College_Name' in df3.columns:
    all_colleges.update(df3['College_Name'].dropna().str.strip().unique())

print(f"Total unique colleges found: {len(all_colleges)}\n")

# Identify main institute types
iits = sorted([c for c in all_colleges if 'IIT' in c or 'Indian Institute of Technology' in c])
nits = sorted([c for c in all_colleges if 'NIT' in c or 'National Institute of Technology' in c])
iiits = sorted([c for c in all_colleges if 'IIIT' in c])
gfti = sorted([c for c in all_colleges if 'GFTI' in c or 'Deemed' in c or 'Central' in c])
others = sorted([c for c in all_colleges if c not in iits and c not in nits and c not in iiits and c not in gfti])

print(f"IITs: {len(iits)}")
print(f"NITs: {len(nits)}")
print(f"IIITs: {len(iiits)}")
print(f"Central/GFTI: {len(gfti)}")
print(f"Others: {len(others)}")

# Create a mapping template
college_mapping = {}

for college_list, category in [(iits, 'IIT'), (nits, 'NIT'), (iiits, 'IIIT'), (gfti, 'Central/Deemed'), (others, 'Other')]:
    for college in college_list[:5]:  # Show first 5 of each category
        canonical = college.strip()
        if 'Indian Institute of Technology' in canonical:
            canonical = canonical.replace('Indian Institute of Technology', 'IIT').strip()
        elif 'National Institute of Technology' in canonical:
            canonical = canonical.replace('National Institute of Technology', 'NIT').strip()
        
        college_mapping[college] = {
            'canonical_name': canonical,
            'category': category,
            'state': 'TO_BE_FILLED',
            'short_name': canonical[:20]
        }

# Save sample mapping
output = os.path.join(data_dir, '..', 'data-pipeline', 'mappings', 'college_names_sample.json')
with open(output, 'w') as f:
    json.dump(college_mapping, f, indent=2)

print(f"\nSample mapping saved to: college_names_sample.json")

# Save complete list for manual work
college_list_file = os.path.join(data_dir, '..', 'data-pipeline', 'mappings', 'all_colleges_to_canonicalize.json')
college_list_dict = {college: {'canonical_name': '', 'category': '', 'state': ''} for college in sorted(all_colleges)}

with open(college_list_file, 'w') as f:
    json.dump(college_list_dict, f, indent=2)

print(f"Complete college list saved to: all_colleges_to_canonicalize.json")
print(f"Total colleges to canonicalize: {len(all_colleges)}")
