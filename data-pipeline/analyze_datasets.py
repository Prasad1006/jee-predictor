#!/usr/bin/env python3
"""
Data Analysis Script - Step 1
Analyzes all existing JEE JoSAA datasets for schema conflicts, duplicates, and inconsistencies
"""

import os
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import Counter
import warnings

warnings.filterwarnings('ignore')

class DatasetAnalyzer:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.datasets = {}
        self.report = {
            'schema': {},
            'conflicts': [],
            'inconsistencies': [],
            'naming_issues': [],
            'duplicates': {},
            'missing_values': {},
            'category_variations': {},
            'quota_variations': {},
            'branch_variations': {},
            'college_variations': {},
            'recommendations': []
        }
    
    def load_all_files(self):
        """Load all CSV and XLSX files from the data directory"""
        print("📂 Loading datasets...")
        for file in os.listdir(self.data_dir):
            if file.startswith('.'):
                continue
            filepath = os.path.join(self.data_dir, file)
            try:
                if file.endswith('.csv'):
                    df = pd.read_csv(filepath)
                    self.datasets[file] = df
                    print(f"  ✓ {file} ({len(df)} rows, {len(df.columns)} cols)")
                elif file.endswith('.xlsx'):
                    xl = pd.ExcelFile(filepath)
                    for sheet in xl.sheet_names:
                        df = pd.read_excel(filepath, sheet_name=sheet)
                        key = f"{file}[{sheet}]"
                        self.datasets[key] = df
                        print(f"  ✓ {key} ({len(df)} rows, {len(df.columns)} cols)")
            except Exception as e:
                print(f"  ✗ Error loading {file}: {e}")
    
    def analyze_schemas(self):
        """Analyze schema of each dataset"""
        print("\n📋 Analyzing schemas...")
        for name, df in self.datasets.items():
            self.report['schema'][name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'column_types': {col: str(df[col].dtype) for col in df.columns},
                'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024**2, 2)
            }
    
    def detect_naming_inconsistencies(self):
        """Detect inconsistencies in college, branch, and category names"""
        print("\n🔍 Detecting naming inconsistencies...")
        
        college_names = set()
        branch_names = set()
        category_names = set()
        quota_names = set()
        
        for name, df in self.datasets.items():
            # College names
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['college', 'institute', 'institution', 'iit', 'nit', 'iiit']):
                    college_names.update(df[col].dropna().unique().astype(str))
            
            # Branch names
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['branch', 'stream', 'course', 'program', 'specialization']):
                    branch_names.update(df[col].dropna().unique().astype(str))
            
            # Category/Quota names
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['category', 'quota', 'gen', 'obc', 'sc', 'st']):
                    category_names.update(df[col].dropna().unique().astype(str))
        
        # Find variations
        self._find_name_variations(college_names, 'college')
        self._find_name_variations(branch_names, 'branch')
        self._find_name_variations(category_names, 'category')
    
    def _find_name_variations(self, names: Set[str], entity_type: str):
        """Find variations of entity names"""
        variations = {}
        names_lower = {n.lower(): n for n in names}
        
        for name_lower, name_original in names_lower.items():
            # Find similar names
            similar = [n for n in names_lower.keys() if entity_type in name_lower or name_lower in n]
            if len(similar) > 1:
                variations[name_original] = similar
        
        if entity_type == 'college':
            self.report['college_variations'] = variations
        elif entity_type == 'branch':
            self.report['branch_variations'] = variations
        elif entity_type == 'category':
            self.report['category_variations'] = variations
    
    def analyze_missing_values(self):
        """Analyze missing values in each dataset"""
        print("\n⚠️  Analyzing missing values...")
        for name, df in self.datasets.items():
            missing = df.isnull().sum()
            missing_pct = (missing / len(df) * 100).round(2)
            if missing.sum() > 0:
                self.report['missing_values'][name] = {
                    col: {'count': int(missing[col]), 'percentage': float(missing_pct[col])}
                    for col in df.columns if missing[col] > 0
                }
    
    def analyze_columns(self):
        """Analyze and categorize columns"""
        print("\n📊 Analyzing column categories...")
        
        rank_cols = []
        college_cols = []
        branch_cols = []
        category_cols = []
        quota_cols = []
        cutoff_cols = []
        fees_cols = []
        placement_cols = []
        
        for name, df in self.datasets.items():
            for col in df.columns:
                col_lower = col.lower()
                
                if any(k in col_lower for k in ['rank', 'rank_', 'crl', 'all_india']):
                    rank_cols.append((name, col))
                if any(k in col_lower for k in ['college', 'institute', 'iit', 'nit', 'iiit', 'gfti']):
                    college_cols.append((name, col))
                if any(k in col_lower for k in ['branch', 'stream', 'course', 'program']):
                    branch_cols.append((name, col))
                if any(k in col_lower for k in ['category', 'gen', 'obc', 'sc', 'st']):
                    category_cols.append((name, col))
                if any(k in col_lower for k in ['quota', 'home_state', 'state']):
                    quota_cols.append((name, col))
                if any(k in col_lower for k in ['cutoff', 'closing']):
                    cutoff_cols.append((name, col))
                if any(k in col_lower for k in ['fee', 'cost', 'tuition']):
                    fees_cols.append((name, col))
                if any(k in col_lower for k in ['placement', 'package', 'salary']):
                    placement_cols.append((name, col))
        
        print(f"  Rank columns: {len(rank_cols)}")
        print(f"  College columns: {len(college_cols)}")
        print(f"  Branch columns: {len(branch_cols)}")
        print(f"  Category columns: {len(category_cols)}")
        print(f"  Quota columns: {len(quota_cols)}")
        print(f"  Cutoff columns: {len(cutoff_cols)}")
        print(f"  Fees columns: {len(fees_cols)}")
        print(f"  Placement columns: {len(placement_cols)}")
        
        self.report['column_mapping'] = {
            'rank': rank_cols,
            'college': college_cols,
            'branch': branch_cols,
            'category': category_cols,
            'quota': quota_cols,
            'cutoff': cutoff_cols,
            'fees': fees_cols,
            'placement': placement_cols
        }
    
    def detect_duplicates(self):
        """Detect potential duplicate records"""
        print("\n🔄 Detecting potential duplicates...")
        for name, df in self.datasets.items():
            if 'College Name' in df.columns or 'college' in [c.lower() for c in df.columns]:
                dup_count = df.duplicated().sum()
                if dup_count > 0:
                    self.report['duplicates'][name] = {
                        'exact_duplicates': int(dup_count),
                        'percentage': round(dup_count / len(df) * 100, 2)
                    }
    
    def generate_report(self, output_file: str = 'data_analysis_report.json'):
        """Generate comprehensive analysis report"""
        print("\n📝 Generating report...")
        
        # Add recommendations
        self.report['recommendations'] = [
            "✓ Standardize college names (e.g., 'NIT Trichy' → 'NIT Tiruchirappalli')",
            "✓ Standardize branch names (e.g., 'CSE' → 'Computer Science')",
            "✓ Standardize quota/category naming (e.g., 'OS' → 'Other State')",
            "✓ Handle missing values appropriately",
            "✓ Resolve duplicate records",
            "✓ Create canonical mappings for colleges and branches",
            "✓ Merge datasets into unified master schema",
            "✓ Validate data integrity after cleaning"
        ]
        
        output_path = os.path.join(self.data_dir, output_file)
        with open(output_path, 'w') as f:
            json.dump(self.report, f, indent=2, default=str)
        
        print(f"  ✓ Report saved to {output_file}")
        return output_path
    
    def print_summary(self):
        """Print summary of analysis"""
        print("\n" + "="*60)
        print("DATASET ANALYSIS SUMMARY")
        print("="*60)
        print(f"\n📦 Total files analyzed: {len(self.datasets)}")
        print(f"📊 Total rows across all datasets: {sum(df.shape[0] for df in self.datasets.values())}")
        print(f"📋 Total columns across all datasets: {sum(df.shape[1] for df in self.datasets.values())}")
        
        print("\n🏫 College Variations Found:")
        for college, variations in list(self.report['college_variations'].items())[:5]:
            print(f"  - {college}: {len(variations)} variations")
        
        print("\n🔧 Branch Variations Found:")
        for branch, variations in list(self.report['branch_variations'].items())[:5]:
            print(f"  - {branch}: {len(variations)} variations")
        
        print("\n⚙️  Category Variations Found:")
        for cat, variations in list(self.report['category_variations'].items())[:5]:
            print(f"  - {cat}: {len(variations)} variations")
        
        print("\n⚠️  Datasets with Missing Values:")
        for dataset, missing_cols in list(self.report['missing_values'].items())[:5]:
            print(f"  - {dataset}: {len(missing_cols)} columns with missing data")
        
        print("\n🔄 Duplicate Records Found:")
        for dataset, dup_info in self.report['duplicates'].items():
            print(f"  - {dataset}: {dup_info['exact_duplicates']} duplicates ({dup_info['percentage']}%)")
        
        print("\n" + "="*60)

def main():
    data_dir = r"c:\Users\prasa\OneDrive\Desktop\jee-predictor-copilot\data-collecting"
    
    analyzer = DatasetAnalyzer(data_dir)
    analyzer.load_all_files()
    analyzer.analyze_schemas()
    analyzer.detect_naming_inconsistencies()
    analyzer.analyze_missing_values()
    analyzer.analyze_columns()
    analyzer.detect_duplicates()
    analyzer.generate_report()
    analyzer.print_summary()

if __name__ == "__main__":
    main()
