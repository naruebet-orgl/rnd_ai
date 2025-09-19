#!/usr/bin/env python3
"""
Script to extract ingredients and formula data from MySQL dump file
and convert to pandas DataFrames
"""

import pandas as pd
import re
import mysql.connector
from sqlalchemy import create_engine
import json

def extract_data_from_sql_dump(sql_file_path):
    """
    Extract ingredients and formula data from SQL dump file
    """
    print("Reading SQL dump file...")
    
    with open(sql_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extract data for each table
    tables_data = {}
    
    # 1. Extract rm_lines (ingredients) data
    print("Extracting ingredients data...")
    rm_lines_pattern = r"-- Dumping data for table `rm_lines`\s*\n(.*?)(?=\n-- Dumping data for table|$)"
    rm_match = re.search(rm_lines_pattern, content, re.DOTALL)
    
    if rm_match:
        rm_data = rm_match.group(1)
        # Find INSERT statements
        insert_pattern = r"INSERT INTO `rm_lines` VALUES\s*(.*?);"
        insert_matches = re.findall(insert_pattern, rm_data, re.DOTALL)
        
        if insert_matches:
            # Parse the values (simplified - you might need more robust parsing)
            print(f"Found {len(insert_matches)} INSERT statements for rm_lines")
            tables_data['rm_lines'] = insert_matches[0]  # Store raw data for now
    
    # 2. Extract rd_formulas data
    print("Extracting formula data...")
    rd_formulas_pattern = r"-- Dumping data for table `rd_formulas`\s*\n(.*?)(?=\n-- Dumping data for table|$)"
    rd_formulas_match = re.search(rd_formulas_pattern, content, re.DOTALL)
    
    if rd_formulas_match:
        rd_formulas_data = rd_formulas_match.group(1)
        insert_pattern = r"INSERT INTO `rd_formulas` VALUES\s*(.*?);"
        insert_matches = re.findall(insert_pattern, rd_formulas_data, re.DOTALL)
        
        if insert_matches:
            print(f"Found {len(insert_matches)} INSERT statements for rd_formulas")
            tables_data['rd_formulas'] = insert_matches[0]
    
    # 3. Extract rd_formula_lines data
    print("Extracting formula ingredients data...")
    rd_formula_lines_pattern = r"-- Dumping data for table `rd_formula_lines`\s*\n(.*?)(?=\n-- Dumping data for table|$)"
    rd_formula_lines_match = re.search(rd_formula_lines_pattern, content, re.DOTALL)
    
    if rd_formula_lines_match:
        rd_formula_lines_data = rd_formula_lines_match.group(1)
        insert_pattern = r"INSERT INTO `rd_formula_lines` VALUES\s*(.*?);"
        insert_matches = re.findall(insert_pattern, rd_formula_lines_data, re.DOTALL)
        
        if insert_matches:
            print(f"Found {len(insert_matches)} INSERT statements for rd_formula_lines")
            tables_data['rd_formula_lines'] = insert_matches[0]
    
    return tables_data

def create_dataframes_from_database():
    """
    Alternative method: Import SQL dump to database and create DataFrames
    """
    print("Creating DataFrames from database...")
    
    # Database connection (update these credentials)
    try:
        engine = create_engine('mysql://username:password@localhost/organics_rd')
        
        # Create DataFrames for each table
        dataframes = {}
        
        # 1. Ingredients (Raw Materials)
        print("Loading ingredients data...")
        rm_lines_df = pd.read_sql('SELECT * FROM rm_lines', engine)
        dataframes['ingredients'] = rm_lines_df
        print(f"Ingredients DataFrame: {rm_lines_df.shape[0]} rows, {rm_lines_df.shape[1]} columns")
        
        # 2. Formulas
        print("Loading formulas data...")
        rd_formulas_df = pd.read_sql('SELECT * FROM rd_formulas', engine)
        dataframes['formulas'] = rd_formulas_df
        print(f"Formulas DataFrame: {rd_formulas_df.shape[0]} rows, {rd_formulas_df.shape[1]} columns")
        
        # 3. Formula Ingredients (Formula Lines)
        print("Loading formula ingredients data...")
        rd_formula_lines_df = pd.read_sql('SELECT * FROM rd_formula_lines', engine)
        dataframes['formula_ingredients'] = rd_formula_lines_df
        print(f"Formula Ingredients DataFrame: {rd_formula_lines_df.shape[0]} rows, {rd_formula_lines_df.shape[1]} columns")
        
        # 4. Combined view: Formulas with their ingredients
        print("Creating combined formula-ingredients view...")
        combined_df = pd.merge(
            rd_formulas_df[['rd_formula_id', 'product_name', 'customer_name', 'rd_formula_date']],
            rd_formula_lines_df[['rd_formula_id', 'rmit_code', 'rmit_name', 'rmit_trade_name', 
                                'rmit_inci_name', 'master_formula', 'supplier_name_en']],
            on='rd_formula_id',
            how='left'
        )
        dataframes['formulas_with_ingredients'] = combined_df
        print(f"Combined DataFrame: {combined_df.shape[0]} rows, {combined_df.shape[1]} columns")
        
        return dataframes
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Please make sure to:")
        print("1. Import the SQL file into MySQL: mysql -u username -p organics_rd < 'Organics RD Sept 16 2025.sql'")
        print("2. Update the database credentials in this script")
        return None

def analyze_ingredients_and_formulas(dataframes):
    """
    Analyze the extracted data
    """
    if not dataframes:
        return
    
    print("\n" + "="*50)
    print("INGREDIENTS AND FORMULAS ANALYSIS")
    print("="*50)
    
    # Ingredients analysis
    ingredients_df = dataframes['ingredients']
    print(f"\n📊 INGREDIENTS SUMMARY:")
    print(f"Total ingredients: {len(ingredients_df)}")
    print(f"Unique suppliers: {ingredients_df['supplier'].nunique()}")
    print(f"Unique INCI names: {ingredients_df['inci_name'].nunique()}")
    
    print(f"\nTop 10 ingredients by trade name:")
    print(ingredients_df['trade_name'].value_counts().head(10))
    
    # Formulas analysis
    formulas_df = dataframes['formulas']
    print(f"\n📊 FORMULAS SUMMARY:")
    print(f"Total formulas: {len(formulas_df)}")
    print(f"Unique customers: {formulas_df['customer_name'].nunique()}")
    print(f"Date range: {formulas_df['rd_formula_date'].min()} to {formulas_df['rd_formula_date'].max()}")
    
    # Formula ingredients analysis
    formula_ingredients_df = dataframes['formula_ingredients']
    print(f"\n📊 FORMULA INGREDIENTS SUMMARY:")
    print(f"Total formula-ingredient combinations: {len(formula_ingredients_df)}")
    print(f"Average ingredients per formula: {len(formula_ingredients_df) / len(formulas_df):.1f}")
    
    # Show sample data
    print(f"\n📋 SAMPLE INGREDIENTS:")
    print(ingredients_df[['rm_code', 'trade_name', 'inci_name', 'supplier']].head())
    
    print(f"\n📋 SAMPLE FORMULAS:")
    print(formulas_df[['rd_formula_id', 'product_name', 'customer_name', 'rd_formula_date']].head())
    
    print(f"\n📋 SAMPLE FORMULA INGREDIENTS:")
    print(formula_ingredients_df[['rd_formula_id', 'rmit_name', 'rmit_inci_name', 'master_formula']].head())

def main():
    """
    Main function to extract and analyze ingredients and formulas
    """
    sql_file_path = "Organics RD Sept 16 2025.sql"
    
    print("🧪 INGREDIENTS & FORMULAS DATA EXTRACTOR")
    print("="*50)
    
    # Method 1: Try database method first
    print("\nMethod 1: Loading from database...")
    dataframes = create_dataframes_from_database()
    
    if dataframes:
        analyze_ingredients_and_formulas(dataframes)
        
        # Save to CSV files
        print(f"\n💾 Saving DataFrames to CSV files...")
        for name, df in dataframes.items():
            filename = f"{name}_data.csv"
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Saved {filename}: {df.shape[0]} rows")
        
        return dataframes
    else:
        print("\nMethod 2: Parsing SQL file directly...")
        # Method 2: Parse SQL file directly (more complex)
        tables_data = extract_data_from_sql_dump(sql_file_path)
        print("Raw data extracted. You may need to implement more sophisticated parsing.")
        return None

if __name__ == "__main__":
    dataframes = main()
