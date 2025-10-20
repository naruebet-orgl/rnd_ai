#!/usr/bin/env python3
"""
Load all SQL CSV files into dataframes dynamically
Creates variables like df_activity_log, df_bmr_master, etc.
"""

import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def load_all_tables(sql_raw_path='/Users/naruebet.orgl/Workspace/Labs/rnd_ai/internal_raw/sql_raw'):
    """
    Load all CSV files from sql_raw directory and create dataframes

    Returns:
        dict: Dictionary with table names as keys and dataframes as values
    """
    sql_raw_path = Path(sql_raw_path)
    csv_files = sorted(sql_raw_path.glob('*.csv'))

    tables = {}

    print(f"Loading {len(csv_files)} tables...\n")

    for csv_file in csv_files:
        table_name = csv_file.stem
        df_name = f"df_{table_name}"

        try:
            # Try normal read first
            df = pd.read_csv(csv_file)
            tables[df_name] = df
            print(f"✓ {df_name:35} → {df.shape[0]:>6,} rows × {df.shape[1]:>3} cols")
        except:
            try:
                # Try with error handling for problematic files
                df = pd.read_csv(csv_file, on_bad_lines='skip', engine='python')
                tables[df_name] = df
                print(f"⚠ {df_name:35} → {df.shape[0]:>6,} rows × {df.shape[1]:>3} cols (some lines skipped)")
            except Exception as e:
                print(f"✗ {df_name:35} → Failed to load: {e}")

    print(f"\n{'='*70}")
    print(f"Loaded {len(tables)} tables successfully!")
    print(f"{'='*70}")

    return tables


def inject_into_globals(tables_dict):
    """
    Inject all dataframes into the global namespace

    Usage:
        tables = load_all_tables()
        inject_into_globals(tables)
        # Now you can use df_activity_log, df_bmr_master, etc. directly
    """
    import inspect
    frame = inspect.currentframe().f_back
    frame.f_globals.update(tables_dict)
    print(f"\nInjected {len(tables_dict)} dataframes into global namespace")
    print("You can now use: df_activity_log, df_bmr_master, etc.")


if __name__ == "__main__":
    # Load all tables
    tables = load_all_tables()

    # Show summary
    print("\nAvailable dataframes:")
    for name in sorted(tables.keys()):
        print(f"  - {name}")
