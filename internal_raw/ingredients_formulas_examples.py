#!/usr/bin/env python3
"""
Examples of how to work with ingredients and formula data as DataFrames
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

def load_data_from_database():
    """
    Load data from MySQL database into DataFrames
    """
    # Update these credentials for your database
    engine = create_engine('mysql://username:password@localhost/organics_rd')
    
    # Load the main tables
    ingredients_df = pd.read_sql('SELECT * FROM rm_lines', engine)
    formulas_df = pd.read_sql('SELECT * FROM rd_formulas', engine)
    formula_ingredients_df = pd.read_sql('SELECT * FROM rd_formula_lines', engine)
    
    return ingredients_df, formulas_df, formula_ingredients_df

def example_1_basic_analysis(ingredients_df, formulas_df, formula_ingredients_df):
    """
    Example 1: Basic analysis of ingredients and formulas
    """
    print("🔍 EXAMPLE 1: BASIC ANALYSIS")
    print("="*40)
    
    # Ingredients analysis
    print(f"Total ingredients: {len(ingredients_df)}")
    print(f"Unique suppliers: {ingredients_df['supplier'].nunique()}")
    print(f"Unique INCI names: {ingredients_df['inci_name'].nunique()}")
    
    # Top suppliers
    print("\nTop 5 suppliers:")
    print(ingredients_df['supplier'].value_counts().head())
    
    # Formulas analysis
    print(f"\nTotal formulas: {len(formulas_df)}")
    print(f"Unique customers: {formulas_df['customer_name'].nunique()}")
    
    # Formula ingredients analysis
    print(f"\nTotal formula-ingredient combinations: {len(formula_ingredients_df)}")
    print(f"Average ingredients per formula: {len(formula_ingredients_df) / len(formulas_df):.1f}")

def example_2_find_ingredients_by_type(ingredients_df):
    """
    Example 2: Find ingredients by type or name pattern
    """
    print("\n🔍 EXAMPLE 2: FIND INGREDIENTS BY TYPE")
    print("="*40)
    
    # Find all ingredients containing "oil"
    oil_ingredients = ingredients_df[
        ingredients_df['trade_name'].str.contains('oil', case=False, na=False)
    ]
    print(f"Ingredients containing 'oil': {len(oil_ingredients)}")
    print(oil_ingredients[['rm_code', 'trade_name', 'inci_name']].head())
    
    # Find all ingredients containing "acid"
    acid_ingredients = ingredients_df[
        ingredients_df['inci_name'].str.contains('acid', case=False, na=False)
    ]
    print(f"\nIngredients containing 'acid': {len(acid_ingredients)}")
    print(acid_ingredients[['rm_code', 'trade_name', 'inci_name']].head())

def example_3_formula_analysis(formulas_df, formula_ingredients_df):
    """
    Example 3: Analyze specific formulas
    """
    print("\n🔍 EXAMPLE 3: FORMULA ANALYSIS")
    print("="*40)
    
    # Get a specific formula and its ingredients
    sample_formula_id = formulas_df['rd_formula_id'].iloc[0]
    print(f"Analyzing formula: {sample_formula_id}")
    
    # Get formula details
    formula_details = formulas_df[formulas_df['rd_formula_id'] == sample_formula_id]
    print(f"Product: {formula_details['product_name'].iloc[0]}")
    print(f"Customer: {formula_details['customer_name'].iloc[0]}")
    
    # Get ingredients for this formula
    formula_ingredients = formula_ingredients_df[
        formula_ingredients_df['rd_formula_id'] == sample_formula_id
    ]
    print(f"\nIngredients in this formula ({len(formula_ingredients)} total):")
    print(formula_ingredients[['rmit_name', 'rmit_inci_name', 'master_formula']].head(10))

def example_4_cost_analysis(ingredients_df, formula_ingredients_df):
    """
    Example 4: Cost analysis
    """
    print("\n🔍 EXAMPLE 4: COST ANALYSIS")
    print("="*40)
    
    # Ingredients with cost information
    ingredients_with_cost = ingredients_df[ingredients_df['rm_cost'].notna()]
    print(f"Ingredients with cost data: {len(ingredients_with_cost)}")
    
    if len(ingredients_with_cost) > 0:
        print(f"Average ingredient cost: {ingredients_with_cost['rm_cost'].mean():.2f}")
        print(f"Most expensive ingredient: {ingredients_with_cost.loc[ingredients_with_cost['rm_cost'].idxmax(), 'trade_name']}")
        print(f"Cost: {ingredients_with_cost['rm_cost'].max():.2f}")
    
    # Formula cost analysis (if available)
    formula_ingredients_with_cost = formula_ingredients_df[
        formula_ingredients_df['rm_price'].notna()
    ]
    if len(formula_ingredients_with_cost) > 0:
        print(f"\nFormula ingredients with price data: {len(formula_ingredients_with_cost)}")
        print(f"Average ingredient price in formulas: {formula_ingredients_with_cost['rm_price'].mean():.2f}")

def example_5_create_custom_views(ingredients_df, formulas_df, formula_ingredients_df):
    """
    Example 5: Create custom views and combinations
    """
    print("\n🔍 EXAMPLE 5: CUSTOM VIEWS")
    print("="*40)
    
    # Create a comprehensive formula view
    formula_view = pd.merge(
        formulas_df[['rd_formula_id', 'product_name', 'customer_name', 'rd_formula_date']],
        formula_ingredients_df[['rd_formula_id', 'rmit_name', 'rmit_inci_name', 'master_formula', 'supplier_name_en']],
        on='rd_formula_id',
        how='left'
    )
    
    print("Formula view created with ingredients:")
    print(formula_view.head())
    
    # Create ingredient usage summary
    ingredient_usage = formula_ingredients_df.groupby('rmit_name').agg({
        'rd_formula_id': 'count',
        'master_formula': 'mean'
    }).rename(columns={'rd_formula_id': 'usage_count', 'master_formula': 'avg_percentage'})
    
    print(f"\nMost used ingredients:")
    print(ingredient_usage.sort_values('usage_count', ascending=False).head(10))
    
    # Create supplier analysis
    supplier_analysis = formula_ingredients_df.groupby('supplier_name_en').agg({
        'rd_formula_id': 'nunique',
        'rmit_name': 'nunique'
    }).rename(columns={'rd_formula_id': 'formulas_count', 'rmit_name': 'unique_ingredients'})
    
    print(f"\nSupplier analysis:")
    print(supplier_analysis.sort_values('formulas_count', ascending=False).head())

def example_6_export_data(ingredients_df, formulas_df, formula_ingredients_df):
    """
    Example 6: Export data to different formats
    """
    print("\n🔍 EXAMPLE 6: EXPORT DATA")
    print("="*40)
    
    # Export to CSV
    ingredients_df.to_csv('ingredients.csv', index=False)
    formulas_df.to_csv('formulas.csv', index=False)
    formula_ingredients_df.to_csv('formula_ingredients.csv', index=False)
    print("Data exported to CSV files")
    
    # Export to Excel with multiple sheets
    with pd.ExcelWriter('ingredients_formulas.xlsx') as writer:
        ingredients_df.to_excel(writer, sheet_name='Ingredients', index=False)
        formulas_df.to_excel(writer, sheet_name='Formulas', index=False)
        formula_ingredients_df.to_excel(writer, sheet_name='Formula_Ingredients', index=False)
    print("Data exported to Excel file with multiple sheets")
    
    # Export specific subsets
    # Only active ingredients
    active_ingredients = ingredients_df[ingredients_df['record_status'] == 1]
    active_ingredients.to_csv('active_ingredients.csv', index=False)
    print(f"Active ingredients exported: {len(active_ingredients)} records")

def main():
    """
    Main function to run all examples
    """
    print("🧪 INGREDIENTS & FORMULAS DATAFRAME EXAMPLES")
    print("="*60)
    
    try:
        # Load data
        print("Loading data from database...")
        ingredients_df, formulas_df, formula_ingredients_df = load_data_from_database()
        
        # Run examples
        example_1_basic_analysis(ingredients_df, formulas_df, formula_ingredients_df)
        example_2_find_ingredients_by_type(ingredients_df)
        example_3_formula_analysis(formulas_df, formula_ingredients_df)
        example_4_cost_analysis(ingredients_df, formula_ingredients_df)
        example_5_create_custom_views(ingredients_df, formulas_df, formula_ingredients_df)
        example_6_export_data(ingredients_df, formulas_df, formula_ingredients_df)
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTo use this script:")
        print("1. Import the SQL file into MySQL:")
        print("   mysql -u username -p organics_rd < 'Organics RD Sept 16 2025.sql'")
        print("2. Update database credentials in the script")
        print("3. Install required packages: pip install pandas sqlalchemy pymysql")

if __name__ == "__main__":
    main()
