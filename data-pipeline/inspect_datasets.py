#!/usr/bin/env python3
"""
Detailed Column Inspection - Step 1 Phase 2
Inspects specific columns and sample data from each dataset
"""

import os
import pandas as pd
import json

data_dir = r"c:\Users\prasa\OneDrive\Desktop\jee-predictor-copilot\data-collecting"

print("=" * 80)
print("DETAILED DATASET INSPECTION")
print("=" * 80)

# Inspect CSV files
csv_files = {
    'College_data.csv': 'College Master Data',
    'data.csv': 'JEE Cutoff Data',
    'merged_jee_cutoff_2018_2025.csv': 'Merged Historical Cutoffs',
    'Top_Indian_Colleges_Fees_Placement.csv': 'Colleges Fees & Placement'
}

for filename, description in csv_files.items():
    filepath = os.path.join(data_dir, filename)
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath, nrows=100)  # Load only first 100 rows for inspection
            print(f"\n{'='*80}")
            print(f"📄 {filename}")
            print(f"Description: {description}")
            print(f"{'='*80}")
            print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"\nColumns:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i}. {col} ({df[col].dtype})")
            
            print(f"\nSample Data (First Row):")
            print(df.iloc[0].to_string())
            
            print(f"\nData Types Summary:")
            print(df.dtypes)
            
            print(f"\nUnique Values for Categorical Columns:")
            for col in df.columns:
                if df[col].dtype == 'object':
                    unique_count = df[col].nunique()
                    if unique_count <= 20:
                        print(f"  - {col}: {df[col].unique().tolist()}")
                    else:
                        print(f"  - {col}: {unique_count} unique values (samples: {df[col].unique()[:5].tolist()})")
        except Exception as e:
            print(f"Error reading {filename}: {e}")

# Check XLSX files
xlsx_dir = data_dir
for filename in os.listdir(xlsx_dir):
    if filename.endswith('.xlsx'):
        filepath = os.path.join(xlsx_dir, filename)
        try:
            xl = pd.ExcelFile(filepath)
            print(f"\n{'='*80}")
            print(f"📊 {filename}")
            print(f"{'='*80}")
            print(f"Sheet names: {xl.sheet_names}")
            
            for sheet in xl.sheet_names[:1]:  # Check first sheet only
                df = pd.read_excel(filepath, sheet_name=sheet, nrows=50)
                print(f"\nSheet: {sheet}")
                print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
                print(f"Columns: {list(df.columns)}")
                print(f"\nFirst few rows:")
                print(df.head(2))
        except Exception as e:
            print(f"Error reading {filename}: {e}")

print("\n" + "="*80)
print("INSPECTION COMPLETE")
print("="*80)
