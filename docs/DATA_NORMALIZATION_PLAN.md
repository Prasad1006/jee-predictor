# JEE JoSAA Data Normalization & Cleaning Plan

## Executive Summary

**Current State**: 
- 4 CSV files + multiple XLSX files
- ~506K records across multiple sources
- Significant naming inconsistencies, missing values, and schema conflicts
- **Primary Challenge**: Unifying college names, categories, quotas, and programs

**Goal**: Create production-ready master database with canonical mappings

---

## Phase 1: Canonicalization Mappings

### 1.1 College Name Canonicalization

**Problem**: 
- "Indian Institute of Technology Madras" vs "IIT Madras" vs "IIT M"
- Trailing spaces: "NIT Trichy, Tiruchirappalli " vs "NIT Trichy"
- "Vellore Institute of Technology" vs "VIT"

**Solution**:
Create mapping file: `canonical_colleges.csv`
```csv
original_name,canonical_name,short_name,category,state,founding_year
Indian Institute of Technology Madras,IIT Madras,IIT M,IIT,Tamil Nadu,1959
Indian Institute of Technology Bombay,IIT Bombay,IIT B,IIT,Maharashtra,1958
NIT Trichy,NIT Trichy,NIT T,NIT,Tamil Nadu,1964
```

**Implementation**:
- Extract all unique college names from all datasets
- Manually create canonical mapping (AI-assisted matching)
- Store in: `datasets/canonical_colleges.csv`

### 1.2 Category/Seat Type Standardization

**Problem**: 
- "GEN" vs "OPEN"
- "OBC-NCL" vs "OBC"
- Multiple PWD variations

**Solution**:
Standardize to: **JOSAA Format**
```
GEN          → GENERAL
OBC-NCL      → OBC
SC           → SC
ST           → ST
GEN-PWD      → GENERAL-PWD
OBC-NCL-PWD  → OBC-PWD
SC-PWD       → SC-PWD
ST-PWD       → ST-PWD
GEN-EWS      → EWS
GEN-EWS-PWD  → EWS-PWD
OPEN         → GENERAL
EWS          → EWS
```

**Implementation**:
- Create mapping: `canonical_categories.json`
- Apply with automatic replacement during cleaning

### 1.3 Quota (State) Standardization

**Problem**:
- "AI" = All India (doesn't map to state)
- "HS", "OS", "GO", "AP", "JK", "LA" = state abbreviations
- Inconsistent mapping

**Solution**:
```
AI  → ALL_INDIA
HS  → HOME_STATE
OS  → OTHER_STATE
GO  → GOA
AP  → ANDHRA_PRADESH
JK  → JAMMU_KASHMIR
LA  → LADAKH
```

**Implementation**:
- Create mapping: `canonical_quotas.json`
- Document the exact JoSAA quota system rules
- Handle NULL values appropriately

### 1.4 Gender Standardization

**Problem**:
- "Gender-Neutral", "Female-only (including Supernumerary)", "F", NaN

**Solution**:
```
Gender-Neutral              → GENDER_NEUTRAL
Female-only (supernumerary) → FEMALE_ONLY
F                           → FEMALE_ONLY
M                           → MALE (if appears)
NaN                         → GENDER_NEUTRAL (default)
```

**Implementation**:
- Create mapping: `canonical_gender.json`
- Apply with default handling for NaN

### 1.5 Program/Branch Standardization

**Problem**:
- "Civil Engineering (4 Years, Bachelor of Technology)" (verbose)
- "CSE" vs "Computer Science and Engineering" vs "Computer Science Engineering"
- Mixed case, extra spaces, punctuation

**Solution**:
Create extraction pipeline:
1. Extract core branch name (before parenthesis)
2. Normalize common abbreviations:
   ```
   CSE  → COMPUTER_SCIENCE_AND_ENGINEERING
   ECE  → ELECTRONICS_AND_COMMUNICATION_ENGINEERING
   ME   → MECHANICAL_ENGINEERING
   CE   → CIVIL_ENGINEERING
   EE   → ELECTRICAL_ENGINEERING
   ```
3. Standardize formatting

**Implementation**:
- Parse program_name column
- Extract branch using regex
- Create mapping: `canonical_branches.json`

### 1.6 State Name Standardization

**Problem**:
- "Tamil nadu" vs "Tamil Nadu"
- "Orissa" (old name) vs "Odisha" (current)
- Mixed case, inconsistent spacing

**Solution**:
Standardize to proper case with current official names:
```
Tamil nadu      → Tamil Nadu
Orissa          → Odisha
Delhi ncr       → Delhi
Uttar pradesh   → Uttar Pradesh
Madhya pradesh  → Madhya Pradesh
```

**Implementation**:
- Create mapping: `canonical_states.json`
- Apply to all state/location fields

---

## Phase 2: Data Cleaning Scripts

### 2.1 Raw Data Cleaning

**Script**: `clean_raw_data.py`

Tasks:
1. Load all CSV/XLSX files
2. Strip whitespace from all string columns
3. Handle NaN/NULL values
4. Convert data types
5. Remove duplicates
6. Save to: `data-pipeline/cleaned-data/`

### 2.2 Column Standardization

**Script**: `standardize_columns.py`

Tasks:
1. Rename columns to standard names
2. Apply category mappings
3. Apply quota mappings
4. Apply gender mappings
5. Standardize program names
6. Output: Each dataset with standardized columns

### 2.3 College Name Normalization

**Script**: `normalize_colleges.py`

Tasks:
1. Load college canonicalization map
2. Match college names (fuzzy matching for close matches)
3. Flag unmatched colleges for manual review
4. Add college_id to all records
5. Output: All datasets with standardized college names

### 2.4 Merge & Deduplicate

**Script**: `merge_datasets.py`

Tasks:
1. Load all cleaned datasets
2. Identify overlapping records (same college, program, year, round, category, quota)
3. Deduplicate with priority rules:
   - Prefer merged_jee_cutoff (most comprehensive)
   - Use data.csv as backup
   - Flag conflicts for manual review
4. Output: Single unified dataset

### 2.5 Validation & Quality Checks

**Script**: `validate_cleaned_data.py`

Tasks:
1. Check all required columns present
2. Validate rank ranges (opening_rank <= closing_rank)
3. Check for orphaned records (college_id not in master list)
4. Validate date/year ranges
5. Generate quality report
6. Output: `data-pipeline/quality_report.json`

---

## Phase 3: Master Database Schema

### Master Cutoff Table

```sql
CREATE TABLE master_cutoffs (
    id SERIAL PRIMARY KEY,
    college_id INT,
    program_id INT,
    year INT,
    round INT,
    category VARCHAR(50),
    quota VARCHAR(50),
    gender VARCHAR(50),
    seat_type VARCHAR(50),
    opening_rank INT,
    closing_rank INT,
    pool VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP,
    UNIQUE(college_id, program_id, year, round, category, quota, gender)
);
```

### Master College Table

```sql
CREATE TABLE master_colleges (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(255),
    short_name VARCHAR(100),
    category VARCHAR(50),
    state VARCHAR(100),
    location VARCHAR(255),
    founding_year INT,
    website VARCHAR(255),
    nirf_rank INT,
    created_at TIMESTAMP
);
```

### Master Program Table

```sql
CREATE TABLE master_programs (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(255),
    category VARCHAR(50),
    duration_years INT,
    degree VARCHAR(50),
    created_at TIMESTAMP
);
```

---

## Phase 4: Data Quality Metrics

Track:
- % of records successfully matched to canonical colleges
- % of records with valid ranks (opening < closing)
- % missing values by column
- # of manual review required records
- Deduplication ratio

---

## Execution Timeline

| Phase | Task | Duration |
|-------|------|----------|
| Phase 1 | Create canonical mappings | 2-3 days |
| Phase 2 | Build cleaning scripts | 3-4 days |
| Phase 3 | Run cleaning pipeline | 1 day |
| Phase 4 | Validate & QA | 1-2 days |
| **Total** | | **7-10 days** |

---

## Output Structure

```
data-pipeline/
├── cleaned-data/
│   ├── cleaned_data.csv
│   ├── cleaned_merged_cutoffs.csv
│   ├── cleaned_college_data.csv
│   └── cleaned_fees_placement.csv
├── normalized-data/
│   ├── master_cutoffs.csv
│   ├── master_colleges.csv
│   ├── master_programs.csv
│   └── dedup_report.json
├── mappings/
│   ├── canonical_colleges.csv
│   ├── canonical_categories.json
│   ├── canonical_quotas.json
│   ├── canonical_gender.json
│   ├── canonical_branches.json
│   └── canonical_states.json
└── quality/
    ├── quality_report.json
    └── data_validation_errors.log
```

---

## Next Steps

1. **Create canonical mappings** (manual work + AI assistance)
2. **Implement cleaning scripts** (Python + Pandas)
3. **Run full cleaning pipeline**
4. **Validate & document** findings
5. **Load into PostgreSQL** for backend use
6. **Generate SEO embeddings** for RAG system
