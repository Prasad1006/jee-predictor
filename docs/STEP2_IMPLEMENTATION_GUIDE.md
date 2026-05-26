# STEP 2 - DATA CLEANING PIPELINE IMPLEMENTATION GUIDE

## Overview

This guide provides step-by-step instructions to build the data cleaning pipeline that will normalize all datasets into production-ready format.

**Estimated Duration**: 3-4 days  
**Output**: Cleaned, deduplicated, normalized datasets ready for PostgreSQL

---

## Phase 1: Auto-Populate College Mappings

### 1.1 Create College Auto-Mapping Script

**Objective**: Auto-generate canonical names for most colleges using pattern matching

**Script**: `auto_populate_colleges.py`

```python
#!/usr/bin/env python3
"""
Auto-populate college mappings using pattern matching and fuzzy matching
"""

import json
import re
from difflib import SequenceMatcher
import os

def extract_canonical_name(college_name):
    """Extract canonical name from various formats"""
    college = college_name.strip()
    
    # Remove extra spaces and punctuation
    college = re.sub(r'\s+', ' ', college)
    college = college.replace(',', '').replace('(', '').replace(')', '')
    
    # Apply substitutions for known patterns
    substitutions = {
        r'Indian Institute of Technology': 'IIT',
        r'National Institute of Technology': 'NIT',
        r'Indian Institute of Information Technology': 'IIIT',
        r',.*': '',  # Remove location suffix
    }
    
    for pattern, replacement in substitutions.items():
        college = re.sub(pattern, replacement, college, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    college = re.sub(r'\s+', ' ', college).strip()
    
    return college

def identify_category(college_name):
    """Identify college category"""
    college_lower = college_name.lower()
    
    if 'iit' in college_lower:
        return 'IIT'
    elif 'nit' in college_lower:
        return 'NIT'
    elif 'iiit' in college_lower:
        return 'IIIT'
    elif 'deemed' in college_lower or 'central' in college_lower:
        return 'Deemed'
    else:
        return 'Other'

# Main mapping function
mapping_file = r"c:\Users\prasa\OneDrive\Desktop\jee-predictor-copilot\data-pipeline\mappings\all_colleges_to_canonicalize.json"

with open(mapping_file, 'r') as f:
    colleges = json.load(f)

# Auto-populate
for college_name, mapping_data in colleges.items():
    canonical = extract_canonical_name(college_name)
    category = identify_category(college_name)
    
    mapping_data['canonical_name'] = canonical
    mapping_data['category'] = category
    
    # Try to extract state if present
    # (This requires a more sophisticated approach with state list matching)

# Save updated mappings
output_file = r"c:\Users\prasa\OneDrive\Desktop\jee-predictor-copilot\data-pipeline\mappings\colleges_auto_mapped.json"
with open(output_file, 'w') as f:
    json.dump(colleges, f, indent=2)

print(f"Mapped {len(colleges)} colleges")
print(f"Saved to: colleges_auto_mapped.json")
```

**To Execute**:
```bash
python data-pipeline/auto_populate_colleges.py
```

### 1.2 Extract IIT/NIT/IIIT State Mapping

Create `iit_nit_iiit_master_list.csv` with verified locations:

```csv
canonical_name,category,state,founded_year,location_city
IIT Bombay,IIT,Maharashtra,1958,Mumbai
IIT Madras,IIT,Tamil Nadu,1959,Chennai
IIT Kharagpur,IIT,West Bengal,1951,Kharagpur
IIT Delhi,IIT,Delhi,1961,Delhi
IIT Kanpur,IIT,Uttar Pradesh,1959,Kanpur
NIT Surathkal,NIT,Karnataka,1960,Mangalore
NIT Trichy,NIT,Tamil Nadu,1964,Trichy
IIIT Hyderabad,IIIT,Telangana,1998,Hyderabad
...
```

---

## Phase 2: Data Cleaning Scripts

### 2.1 Script: `clean_raw_data.py`

**Purpose**: Basic cleaning of raw datasets

```python
#!/usr/bin/env python3
import pandas as pd
import os

input_dir = r"c:\Users\prasa\OneDrive\Desktop\jee-predictor-copilot\data-collecting"
output_dir = r"c:\Users\prasa\OneDrive\Desktop\jee-predictor-copilot\data-pipeline\cleaned-data"

# Load datasets
data_files = {
    'data.csv': 'data_csv',
    'merged_jee_cutoff_2018_2025.csv': 'merged_csv',
    'College_data.csv': 'college_csv',
    'Top_Indian_Colleges_Fees_Placement.csv': 'fees_csv'
}

dfs = {}
for filename, key in data_files.items():
    filepath = os.path.join(input_dir, filename)
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        # Step 1: Strip whitespace
        df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
        # Step 2: Standardize column names to lowercase with underscores
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        dfs[key] = df
        print(f"Cleaned {filename}: {df.shape}")
        # Save
        output_file = os.path.join(output_dir, f"clean_{filename}")
        df.to_csv(output_file, index=False)

print("Raw data cleaning complete!")
```

### 2.2 Script: `standardize_categories.py`

**Purpose**: Apply canonical category mappings

```python
#!/usr/bin/env python3
import pandas as pd
import json
import os

# Load mapping
with open(r'data-pipeline/mappings/canonical_categories.json', 'r') as f:
    category_map = json.load(f)['category_mappings']

# Apply to datasets
input_dir = r"data-pipeline/cleaned-data"
output_dir = r"data-pipeline/standardized-data"

# For data.csv
df = pd.read_csv(os.path.join(input_dir, 'clean_data.csv'))
df['category'] = df['category'].map(category_map).fillna(df['category'])
df.to_csv(os.path.join(output_dir, 'std_data.csv'), index=False)

# For merged file
df2 = pd.read_csv(os.path.join(input_dir, 'clean_merged_jee_cutoff_2018_2025.csv'))
df2['seat_type'] = df2['seat_type'].map(category_map).fillna(df2['seat_type'])
df2.to_csv(os.path.join(output_dir, 'std_merged_cutoffs.csv'), index=False)

print("Category standardization complete!")
```

### 2.3 Script: `normalize_colleges.py`

**Purpose**: Apply college name canonicalization with fuzzy matching

```python
#!/usr/bin/env python3
import pandas as pd
import json
from difflib import SequenceMatcher
import os

def fuzzy_match(name, candidates, threshold=0.85):
    """Find best matching canonical name"""
    best_match = None
    best_score = 0
    
    for candidate in candidates:
        ratio = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
        if ratio > best_score:
            best_score = ratio
            best_match = candidate
    
    return best_match if best_score >= threshold else None

# Load college mapping
with open(r'data-pipeline/mappings/colleges_auto_mapped.json', 'r') as f:
    college_map = json.load(f)

# Create reverse mapping: original -> canonical
original_to_canonical = {k: v['canonical_name'] for k, v in college_map.items()}
all_canonicals = list(set(original_to_canonical.values()))

# Load and normalize each dataset
input_dir = r"data-pipeline/standardized-data"
output_dir = r"data-pipeline/normalized-data"

# Process data.csv
df = pd.read_csv(os.path.join(input_dir, 'std_data.csv'))
df['institute_canonical'] = df['institute_short'].apply(
    lambda x: original_to_canonical.get(x, fuzzy_match(x, all_canonicals)) if pd.notna(x) else None
)
df['match_confidence'] = df['institute_short'].apply(
    lambda x: 'EXACT' if x in original_to_canonical else 'FUZZY'
)
# Flag unmatched
df['needs_manual_review'] = df['institute_canonical'].isna()

df.to_csv(os.path.join(output_dir, 'data_with_colleges.csv'), index=False)

print(f"College normalization complete!")
print(f"Unmatched records: {df['needs_manual_review'].sum()}")
```

### 2.4 Script: `merge_and_deduplicate.py`

**Purpose**: Merge all datasets and remove duplicates

```python
#!/usr/bin/env python3
import pandas as pd
import os

input_dir = r"data-pipeline/normalized-data"
output_dir = r"data-pipeline/merged-data"

# Create master schema based on merged cutoffs
# Columns: college_id, program_id, year, round, category, quota, gender, opening_rank, closing_rank

# Load all datasets
dfs_to_merge = []

# Main dataset: merged_cutoffs
df_main = pd.read_csv(os.path.join(input_dir, 'std_merged_cutoffs.csv'))
dfs_to_merge.append(df_main)

# Backup dataset: data.csv
df_backup = pd.read_csv(os.path.join(input_dir, 'std_data.csv'))
dfs_to_merge.append(df_backup)

# Merge with priority: main dataset takes precedence
merged_df = pd.concat(dfs_to_merge, ignore_index=True)

# Define deduplication key
dup_cols = ['institute_canonical', 'program_name', 'year', 'round', 'category', 'quota', 'gender']

# Remove exact duplicates - keep first occurrence
merged_df_dedup = merged_df.drop_duplicates(subset=dup_cols, keep='first')

print(f"Records before dedup: {len(merged_df)}")
print(f"Records after dedup: {len(merged_df_dedup)}")
print(f"Duplicates removed: {len(merged_df) - len(merged_df_dedup)}")

# Save
merged_df_dedup.to_csv(os.path.join(output_dir, 'master_cutoffs_merged.csv'), index=False)

# Generate dedup report
dedup_report = {
    'total_records_before': len(merged_df),
    'total_records_after': len(merged_df_dedup),
    'duplicates_removed': len(merged_df) - len(merged_df_dedup),
    'dedup_ratio': (len(merged_df) - len(merged_df_dedup)) / len(merged_df) * 100
}

import json
with open(os.path.join(output_dir, 'dedup_report.json'), 'w') as f:
    json.dump(dedup_report, f, indent=2)

print("Merge and deduplication complete!")
```

### 2.5 Script: `validate_data.py`

**Purpose**: Validate data quality and generate quality report

```python
#!/usr/bin/env python3
import pandas as pd
import os
import json

input_file = r"data-pipeline/merged-data/master_cutoffs_merged.csv"
output_dir = r"data-pipeline/quality"

df = pd.read_csv(input_file)

# Quality checks
quality_report = {
    'total_records': len(df),
    'checks': {}
}

# Check 1: Valid rank ranges
valid_ranks = (df['opening_rank'] <= df['closing_rank']).sum()
quality_report['checks']['valid_rank_ranges'] = {
    'valid': int(valid_ranks),
    'invalid': len(df) - valid_ranks,
    'percentage_valid': valid_ranks / len(df) * 100
}

# Check 2: Year ranges
quality_report['checks']['year_range'] = {
    'min_year': int(df['year'].min()),
    'max_year': int(df['year'].max()),
    'valid_years': (df['year'] >= 2016) & (df['year'] <= 2025).sum()
}

# Check 3: Missing values
missing_cols = df.isnull().sum()
quality_report['checks']['missing_values'] = {
    col: {
        'count': int(missing_cols[col]),
        'percentage': float(missing_cols[col] / len(df) * 100)
    }
    for col in missing_cols[missing_cols > 0].index
}

# Check 4: Unmatched colleges
if 'needs_manual_review' in df.columns:
    unmatched = df['needs_manual_review'].sum()
    quality_report['checks']['unmatched_colleges'] = {
        'count': int(unmatched),
        'percentage': float(unmatched / len(df) * 100)
    }

# Save report
with open(os.path.join(output_dir, 'quality_report.json'), 'w') as f:
    json.dump(quality_report, f, indent=2)

print("Quality validation complete!")
print(json.dumps(quality_report, indent=2))
```

---

## Phase 3: Execution Checklist

- [ ] Create college auto-mapping script
- [ ] Extract IIT/NIT/IIIT master list
- [ ] Run raw data cleaning
- [ ] Apply category mappings
- [ ] Normalize college names (with fuzzy matching)
- [ ] Merge and deduplicate
- [ ] Run quality validation
- [ ] Manual review of flagged records
- [ ] Final approval and sign-off

---

## Phase 4: Output Deliverables

```
data-pipeline/
├── cleaned-data/
│   ├── clean_data.csv
│   ├── clean_merged_jee_cutoff_2018_2025.csv
│   ├── clean_college_data.csv
│   └── clean_Top_Indian_Colleges_Fees_Placement.csv
├── standardized-data/
│   ├── std_data.csv
│   ├── std_merged_cutoffs.csv
│   └── ...
├── normalized-data/
│   ├── data_with_colleges.csv
│   └── ...
├── merged-data/
│   ├── master_cutoffs_merged.csv
│   └── dedup_report.json
└── quality/
    ├── quality_report.json
    └── validation_errors.log
```

---

## Quality Gates (Must Pass)

| Metric | Threshold | Status |
|--------|-----------|--------|
| Valid rank ranges | 99%+ | TBD |
| Successfully matched colleges | 95%+ | TBD |
| Duplicates removed | >0 | TBD |
| Missing values (critical columns) | <1% | TBD |
| Manual review items | <100 | TBD |

---

## Next Step: Step 3 - PostgreSQL Database

Once data cleaning is complete:
1. Design master schema
2. Create PostgreSQL tables
3. Load cleaned data
4. Create indices
5. Run final validation queries

**Estimated Time for Step 3**: 1 day

---

**Implementation Started**: May 24, 2026  
**Target Completion**: May 28, 2026  
**Next Review**: Upon completion of Phase 2
