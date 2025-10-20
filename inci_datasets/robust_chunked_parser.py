#!/usr/bin/env python3
"""
Robust chunked parser with multiprocessing for COSING data
Handles the specific HTML structure in the file
"""

import pandas as pd
import re
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import os

def extract_headers_robust(file_path):
    """Extract headers using multiple approaches"""
    
    # Try different approaches to find headers
    with open(file_path, 'r', encoding='utf-16') as f:
        # Read first 50KB to find headers
        sample = f.read(50*1024)
    
    # Method 1: Look for the specific pattern we saw
    patterns = [
        r'<tr\s+bgcolor="#CCCCCC"[^>]*>(.*?)</tr>',
        r'<tr[^>]*bgcolor="#CCCCCC"[^>]*>(.*?)</tr>',
        r'<tr[^>]*>(.*?COSING Ref No.*?)</tr>',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sample, re.DOTALL | re.IGNORECASE)
        if match:
            header_content = match.group(1)
            
            # Extract individual header cells
            cell_patterns = [
                r'<td[^>]*>.*?<strong[^>]*>(.*?)</strong>.*?</td>',
                r'<td[^>]*>(.*?)</td>',
            ]
            
            for cell_pattern in cell_patterns:
                cells = re.findall(cell_pattern, header_content, re.DOTALL)
                if len(cells) >= 5:  # We expect at least 5 columns
                    headers = [cell.strip() for cell in cells]
                    print(f"Found headers using pattern: {headers}")
                    return headers
    
    # Method 2: Look for the specific headers we know exist
    known_headers = [
        'COSING Ref No',
        'INCI name', 
        'INN name',
        'Ph. Eur. Name',
        'CAS No',
        'EC No',
        'Chem/IUPAC Name / Description',
        'Restriction',
        'Function',
        'Update Date'
    ]
    
    # Check if these headers exist in the sample
    sample_lower = sample.lower()
    found_headers = []
    for header in known_headers:
        if header.lower() in sample_lower:
            found_headers.append(header)
    
    if len(found_headers) >= 5:
        print(f"Found headers by content matching: {found_headers}")
        return found_headers
    
    # Method 3: Manual extraction based on what we saw in the file
    manual_headers = [
        'COSING Ref No',
        'INCI name',
        'INN name', 
        'Ph. Eur. Name',
        'CAS No',
        'EC No',
        'Chem/IUPAC Name / Description',
        'Restriction',
        'Function',
        'Update Date'
    ]
    
    print(f"Using manual headers: {manual_headers}")
    return manual_headers

def parse_chunk_robust(chunk_data):
    """Robust chunk parsing"""
    chunk, headers = chunk_data
    
    # More flexible row patterns
    row_patterns = [
        r'<tr[^>]*>(.*?)</tr>',
        r'<tr[^>]*valign="top"[^>]*>(.*?)</tr>',
    ]
    
    all_rows = []
    
    for row_pattern in row_patterns:
        rows = re.findall(row_pattern, chunk, re.DOTALL)
        
        for row in rows:
            # Skip header rows
            if any(keyword in row.lower() for keyword in ['bgcolor="#cccccc"', 'cosing ref no', '<strong>']):
                continue
            
            # Extract cells with multiple patterns
            cell_patterns = [
                r'<td[^>]*>(.*?)</td>',
                r'<td[^>]*valign="top"[^>]*>(.*?)</td>',
            ]
            
            cells = []
            for cell_pattern in cell_patterns:
                cells = re.findall(cell_pattern, row, re.DOTALL)
                if len(cells) >= len(headers):
                    break
            
            if len(cells) >= len(headers):
                # Clean up cell content
                clean_cells = []
                for cell in cells[:len(headers)]:  # Take only the number of headers we have
                    # Remove HTML tags
                    clean_cell = re.sub(r'<[^>]+>', '', cell)
                    # Clean up whitespace
                    clean_cell = re.sub(r'\s+', ' ', clean_cell).strip()
                    # Remove HTML entities
                    clean_cell = clean_cell.replace('&nbsp;', '').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                    clean_cells.append(clean_cell)
                
                all_rows.append(clean_cells)
    
    return all_rows

def chunk_file_efficient(file_path, chunk_size=1024*256):  # 256KB chunks
    """Efficiently chunk the file"""
    chunks = []
    
    with open(file_path, 'r', encoding='utf-16') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
    
    return chunks

def robust_chunked_parse(file_path, num_workers=4):
    """Robust chunked parsing with multiprocessing"""
    
    print(f"=== Robust Chunked Parser ===")
    print(f"File: {file_path}")
    print(f"Workers: {num_workers}")
    
    # Get file size
    file_size = os.path.getsize(file_path) / (1024*1024)
    print(f"File size: {file_size:.1f} MB")
    
    # Extract headers
    print("Extracting headers...")
    headers = extract_headers_robust(file_path)
    
    if not headers:
        print("Failed to extract headers")
        return None
    
    # Create chunks
    print("Creating chunks...")
    chunks = chunk_file_efficient(file_path)
    print(f"Created {len(chunks)} chunks")
    
    # Prepare data for workers
    chunk_data = [(chunk, headers) for chunk in chunks]
    
    # Process with workers
    print("Processing chunks with workers...")
    all_rows = []
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_chunk = {executor.submit(parse_chunk_robust, data): i for i, data in enumerate(chunk_data)}
        
        for future in tqdm(as_completed(future_to_chunk), total=len(chunk_data), desc="Processing"):
            try:
                rows = future.result()
                all_rows.extend(rows)
            except Exception as e:
                chunk_idx = future_to_chunk[future]
                print(f"Error in chunk {chunk_idx}: {e}")
    
    print(f"Total rows extracted: {len(all_rows)}")
    
    if all_rows:
        # Create DataFrame
        print("Creating DataFrame...")
        df = pd.DataFrame(all_rows, columns=headers)
        
        # Clean data
        print("Cleaning data...")
        df = df.replace('', pd.NA)
        df = df.replace(' ', pd.NA)
        df = df.dropna(how='all')
        df = df.reset_index(drop=True)
        
        # Remove duplicate rows
        initial_len = len(df)
        df = df.drop_duplicates()
        final_len = len(df)
        if initial_len != final_len:
            print(f"Removed {initial_len - final_len} duplicate rows")
        
        print(f"Final DataFrame shape: {df.shape}")
        return df
    
    return None

def main():
    file_path = "/Users/naruebet.orgl/Workspace/Labs/rnd_ai/inci_datasets/COSING_Ingredients-Fragrance%20Inventory_v2.xls"
    
    # Parse with robust chunked approach
    df = robust_chunked_parse(file_path, num_workers=4)
    
    if df is not None:
        # Save results
        csv_file = "cosing_ingredients_robust.csv"
        excel_file = "cosing_ingredients_robust.xlsx"
        
        df.to_csv(csv_file, index=False)
        df.to_excel(excel_file, index=False)
        
        print(f"\n=== Success! ===")
        print(f"✓ Parsed {len(df)} cosmetic ingredients")
        print(f"✓ Saved to: {csv_file}")
        print(f"✓ Saved to: {excel_file}")
        
        # Quick stats
        print(f"\nColumns: {df.columns.tolist()}")
        print(f"Shape: {df.shape}")
        
        # Show sample data
        print(f"\nSample data:")
        print(df.head(2))
        
    else:
        print("✗ Failed to parse data")

if __name__ == "__main__":
    main()
