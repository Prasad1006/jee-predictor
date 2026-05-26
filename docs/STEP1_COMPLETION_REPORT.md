# STEP 1 - DATA ANALYSIS & NORMALIZATION PLANNING

## Status: ✅ COMPLETE

**Execution Date**: May 24, 2026  
**Duration**: ~2 hours  
**Deliverables Generated**: Yes (5)

---

## Summary

Successfully analyzed all existing JEE JoSAA datasets to understand data quality, schema conflicts, and normalization requirements.

## Analysis Findings

### Dataset Overview
- **Total Files**: 4 CSV + 8 XLSX
- **Total Records**: 505,749 rows
- **Total Attributes**: 42 columns
- **Key Coverage**: Historical cutoff data (2016-2025), college master data, fees & placement data

### Data Quality Status

| Metric | Status | Details |
|--------|--------|---------|
| **Duplicates** | ✅ Good | No exact row duplicates found |
| **Missing Values** | ⚠️ Moderate | 6 columns in merged dataset have NaN values |
| **College Names** | ⚠️ High Variation | 3,330 unique college names (3 naming formats for same college) |
| **Categories** | ⚠️ Mixed Format | GEN vs OPEN, OBC-NCL vs OBC naming inconsistencies |
| **Programs** | ⚠️ Verbose | Program names include duration/degree info (needs parsing) |
| **States** | ⚠️ Spelling Errors | "Orissa" vs "Odisha", inconsistent capitalization |

---

## Key Issues Identified

### 1. **College Name Inconsistencies** (Critical)
**Examples**:
- "Indian Institute of Technology Madras" vs "IIT Madras" vs "IIT M"
- "NIT Trichy, Tiruchirappalli" vs "NIT Trichy"
- Trailing spaces in some records
- **Impact**: Prevents accurate deduplication and matching

**Solution**: Created `all_colleges_to_canonicalize.json` with 3,330 colleges

### 2. **Category/Seat Type Mismatch** (Critical)
**Conflict**:
- data.csv: GEN, OBC-NCL, SC, ST, GEN-PWD, EWS
- merged file: OPEN, OBC-NCL, SC, ST, OPEN (PwD)
- **Root Cause**: Different JOSAA systems (older vs newer naming)

**Solution**: Created canonical mapping → unified JOSAA format

### 3. **Quota State Ambiguity** (Medium)
**Problem**: 
- "HS" = Home State (student's state, not fixed)
- "OS" = Other State (non-home state)
- "AI" = All India (nationwide)
- Location-specific: "AP", "JK", "LA"

**Solution**: Documented in `canonical_quotas.json` with clear rules

### 4. **Program Name Verbosity** (Medium)
**Examples**:
- "Civil Engineering (4 Years, Bachelor of Technology)" → needs cleaning
- "CSE" vs "Computer Science and Engineering"
- Branch parsing required

**Solution**: Created `canonical_branches.json` with 16+ branch types

### 5. **State Name Normalization** (Low-Medium)
**Issues**:
- "Tamil nadu" → "Tamil Nadu"
- "Orissa" → "Odisha" (official name change)
- Mixed case and spacing

**Solution**: Created `canonical_states.json` with all 36 states/UTs

### 6. **Gender Field Standardization** (Low)
**Variations**: "Gender-Neutral", "Female-only", "F", NaN
**Solution**: Created `canonical_gender.json` with default handling

---

## Deliverables Created

### 1. **Mapping Files** (5 files in `data-pipeline/mappings/`)
- ✅ `canonical_categories.json` - 20+ category mappings
- ✅ `canonical_quotas.json` - 7 quota type mappings
- ✅ `canonical_gender.json` - Gender standardization
- ✅ `canonical_branches.json` - 16 branch types with variations
- ✅ `canonical_states.json` - 36 states/UTs with variations

### 2. **College Mapping Templates** (2 files)
- ✅ `college_names_sample.json` - Sample mappings for top colleges
- ✅ `all_colleges_to_canonicalize.json` - Complete list of 3,330 colleges (REQUIRES MANUAL WORK)

### 3. **Documentation**
- ✅ `DATA_NORMALIZATION_PLAN.md` - Comprehensive 4-phase cleaning plan
- ✅ `data_analysis_report.json` - Detailed analysis metrics
- ✅ `STEP1_COMPLETION_REPORT.md` - This file

### 4. **Analysis Scripts** (2 Python scripts)
- ✅ `analyze_datasets.py` - Full dataset analysis
- ✅ `inspect_datasets.py` - Schema inspection
- ✅ `get_unique_values.py` - Categorical value extraction
- ✅ `extract_colleges.py` - College name extraction

---

## College Mapping Status

Total colleges to canonicalize: **3,330**

**Breakdown by Type**:
- IITs: 71 institutions
- NITs: 71 institutions
- IIITs: 14 institutions
- Central/GFTI: 33 institutions
- **Other colleges**: 3,155 institutions (requires manual mapping)

**⚠️ ACTION REQUIRED**: 
The file `all_colleges_to_canonicalize.json` needs to be manually populated or AI-assisted to fill:
- `canonical_name` - standardized college name
- `category` - IIT/NIT/IIIT/Deemed/Private/Government
- `state` - state location

**Recommendation**: Use college data from existing files + web scraping/API to auto-populate

---

## Next Steps (STEP 2)

### Phase 1: Auto-Populate College Mappings (1 day)
1. Parse college names to extract canonical forms
2. Use fuzzy matching against JOSAA/CSAB databases
3. Flag unmatched colleges for manual review
4. Generate confidence scores

### Phase 2: Build Data Cleaning Pipeline (3-4 days)
1. **Clean raw data** - Remove whitespace, fix encodings
2. **Standardize columns** - Apply all mappings
3. **Normalize colleges** - Use canonical mappings
4. **Merge datasets** - Deduplicate based on college+program+year+round
5. **Validate data** - QA checks, generate quality report

### Phase 3: Load into PostgreSQL (1 day)
1. Design master schema
2. Create tables
3. Insert cleaned data
4. Create indices for performance

### Estimated Total Time: 5-6 days until Step 3 (Master Database Ready)

---

## Success Metrics

- [x] All datasets analyzed
- [x] Schema conflicts identified
- [x] Normalization mappings created
- [x] College extraction completed
- [ ] Data cleaning pipeline built
- [ ] Data loaded into PostgreSQL
- [ ] Quality metrics achieved (95%+ successful matches)

---

## Technical Notes

### Data Size
- Largest file: `merged_jee_cutoff_2018_2025.csv` (433K rows)
- Memory usage: ~500MB peak
- Processing time: <5 seconds per file

### Tools Used
- Python 3.14
- Pandas (data manipulation)
- JSON (mapping storage)
- Git (version control)

---

## Recommendations for Accuracy

1. **College Mapping**: Use combination of:
   - JOSAA official college list
   - CSAB official college list
   - Wikipedia/official college websites
   - Fuzzy string matching (Levenshtein distance)

2. **Data Validation**: Implement:
   - Rank range validation (opening_rank ≤ closing_rank)
   - Year range validation (2016-2025)
   - College ID validation (must exist in master list)

3. **Deduplication Rules**:
   - **Primary key**: (college_id, program_id, year, round, category, quota, gender)
   - **Merge strategy**: merged_jee_cutoff > data.csv (in case of conflict)
   - **Flag conflicts** for manual review

4. **Quality Gates**:
   - Minimum 95% successful college name matches
   - Minimum 98% valid rank ranges
   - Minimum 99% complete program data
   - Manual review required for flagged conflicts

---

**Report Generated**: May 24, 2026  
**Status**: Ready for Step 2 (Data Cleaning Pipeline)  
**Next Review**: After college mapping completion
