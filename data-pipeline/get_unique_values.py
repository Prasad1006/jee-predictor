#!/usr/bin/env python3
"""
Unique Values Analysis
Get all unique values for categorical columns to identify inconsistencies
"""

import os
import pandas as pd
import sys

data_dir = r"c:\Users\prasa\OneDrive\Desktop\jee-predictor-copilot\data-collecting"

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 100)
print("UNIQUE VALUES IN KEY COLUMNS")
print("=" * 100)

# data.csv - JEE Cutoff Data
print("\n\n[data.csv] - Unique Values")
print("-" * 100)
df = pd.read_csv(os.path.join(data_dir, 'data.csv'))
print(f"\nInstitute Types: {df['institute_type'].unique().tolist()}")
print(f"Quotas: {df['quota'].unique().tolist()}")
print(f"Categories: {df['category'].unique().tolist()}")
print(f"Programs (first 20): {df['program_name'].unique()[:20].tolist()}")
print(f"Degrees: {df['degree_short'].unique().tolist()}")
print(f"Years: {df['year'].unique().tolist()}")

# merged_jee_cutoff_2018_2025.csv
print("\n\n📊 merged_jee_cutoff_2018_2025.csv - Unique Values")
print("-" * 100)
df2 = pd.read_csv(os.path.join(data_dir, 'merged_jee_cutoff_2018_2025.csv'))
print(f"\nQuotas: {df2['Quota'].unique().tolist()}")
print(f"Seat Types: {df2['Seat Type'].unique().tolist()}")
print(f"Gender: {df2['Gender'].unique().tolist()}")
print(f"Programs (first 20): {df2['Academic Program Name'].unique()[:20].tolist()}")
print(f"Years: {sorted(df2['Year'].unique().tolist())}")
print(f"Institutes (count): {df2['Institute'].nunique()}")
print(f"Institutes (samples): {df2['Institute'].unique()[:10].tolist()}")

# College_data.csv
print("\n\n📊 College_data.csv - Unique Values")
print("-" * 100)
df3 = pd.read_csv(os.path.join(data_dir, 'College_data.csv'))
print(f"\nStates: {df3['State'].unique().tolist()}")
print(f"Streams: {df3['Stream'].unique().tolist()}")
print(f"Colleges (count): {df3['College_Name'].nunique()}")
print(f"Colleges (samples): {df3['College_Name'].unique()[:10].tolist()}")

# Top_Indian_Colleges_Fees_Placement.csv
print("\n\n📊 Top_Indian_Colleges_Fees_Placement.csv - Unique Values")
print("-" * 100)
df4 = pd.read_csv(os.path.join(data_dir, 'Top_Indian_Colleges_Fees_Placement.csv'))
print(f"\nCollege Programs (count): {df4['Program'].nunique()}")
print(f"Colleges: {df4['College'].unique().tolist()}")
print(f"Branches: {df4['Branch'].unique().tolist()}")
print(f"Locations: {df4['Location'].unique().tolist()}")

print("\n" + "=" * 100)

# Check for the XLSX files
print("\n\nChecking XLSX Files...")
print("=" * 100)
for filename in os.listdir(data_dir):
    if filename.endswith('.xlsx'):
        print(f"\n📊 {filename}")
        try:
            xl = pd.ExcelFile(os.path.join(data_dir, filename))
            print(f"Sheets: {xl.sheet_names}")
            for sheet in xl.sheet_names:
                df = pd.read_excel(os.path.join(data_dir, filename), sheet_name=sheet)
                print(f"\n  Sheet '{sheet}': {df.shape}")
                print(f"  Columns: {list(df.columns)}")
                if len(df.columns) <= 10:
                    for col in df.columns:
                        unique_count = df[col].nunique()
                        if df[col].dtype == 'object' and unique_count <= 10:
                            print(f"    - {col}: {df[col].unique().tolist()}")
        except Exception as e:
            print(f"Error: {e}")

print("\n" + "=" * 100)
