#!/usr/bin/env python3
"""
Extract data from MySQL dump file and save each table to separate CSV files
"""

import re
import csv
import os
from pathlib import Path

def parse_sql_inserts(sql_file_path, output_dir):
    """
    Parse SQL dump file and extract INSERT statements to CSV files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    current_table = None
    current_columns = []

    print(f"Reading SQL file: {sql_file_path}")
    print(f"Output directory: {output_dir}")

    with open(sql_file_path, 'r', encoding='utf-8', errors='replace') as f:
        table_count = 0
        row_count = 0
        current_writer = None
        current_file = None

        for line_num, line in enumerate(f, 1):
            if line_num % 10000 == 0:
                print(f"Processing line {line_num:,}...")

            # Detect table name from CREATE TABLE
            create_match = re.match(r'CREATE TABLE `(\w+)`', line)
            if create_match:
                # Close previous file if open
                if current_file:
                    current_file.close()
                    print(f"  Saved {row_count:,} rows to {current_table}.csv")

                current_table = create_match.group(1)
                table_count += 1
                row_count = 0
                current_columns = []
                current_writer = None
                current_file = None
                print(f"\nFound table: {current_table}")
                continue

            # Extract column names from CREATE TABLE
            if current_table and line.strip().startswith('`'):
                col_match = re.match(r'\s+`(\w+)`', line)
                if col_match and not line.strip().startswith('PRIMARY') and not line.strip().startswith('KEY'):
                    if col_match.group(1) not in current_columns:
                        current_columns.append(col_match.group(1))

            # Detect INSERT statements
            if current_table and line.startswith('INSERT INTO'):
                # Create CSV writer if not exists
                if not current_writer:
                    csv_file = output_path / f"{current_table}.csv"
                    current_file = open(csv_file, 'w', newline='', encoding='utf-8')
                    current_writer = csv.writer(current_file, quoting=csv.QUOTE_ALL)
                    # Write header
                    if current_columns:
                        current_writer.writerow(current_columns)

                # Extract VALUES portion
                values_match = re.search(r'VALUES\s+(.+);?\s*$', line, re.DOTALL)
                if values_match:
                    values_str = values_match.group(1).rstrip(';')

                    # Parse individual row tuples
                    # This regex finds complete tuples (...)
                    tuple_pattern = r'\(([^()]*(?:\([^()]*\)[^()]*)*)\)'
                    tuples = re.findall(tuple_pattern, values_str)

                    for tuple_str in tuples:
                        # Parse individual values
                        row_values = parse_sql_values(tuple_str)
                        if row_values:
                            current_writer.writerow(row_values)
                            row_count += 1

        # Close last file
        if current_file:
            current_file.close()
            print(f"  Saved {row_count:,} rows to {current_table}.csv")

    print(f"\n{'='*60}")
    print(f"Extraction complete!")
    print(f"Total tables processed: {table_count}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}")

def parse_sql_values(values_str):
    """
    Parse a SQL VALUES tuple string into a list of values
    Handles NULL, quoted strings, numbers, etc.
    """
    values = []
    current_value = ''
    in_quote = False
    quote_char = None
    i = 0

    while i < len(values_str):
        char = values_str[i]

        if not in_quote:
            if char in ("'", '"'):
                in_quote = True
                quote_char = char
                i += 1
                continue
            elif char == ',' :
                # End of value
                value = current_value.strip()
                if value.upper() == 'NULL':
                    values.append('')
                else:
                    values.append(value)
                current_value = ''
                i += 1
                continue
        else:
            # Inside quoted string
            if char == quote_char:
                # Check if it's escaped
                if i + 1 < len(values_str) and values_str[i + 1] == quote_char:
                    # Escaped quote
                    current_value += char
                    i += 2
                    continue
                elif char == '\\' and i + 1 < len(values_str):
                    # Backslash escape
                    i += 1
                    if i < len(values_str):
                        escaped_char = values_str[i]
                        if escaped_char == 'n':
                            current_value += '\n'
                        elif escaped_char == 't':
                            current_value += '\t'
                        elif escaped_char == 'r':
                            current_value += '\r'
                        else:
                            current_value += escaped_char
                    i += 1
                    continue
                else:
                    # End of quoted string
                    in_quote = False
                    quote_char = None
                    i += 1
                    continue

        current_value += char
        i += 1

    # Add last value
    if current_value or not values:
        value = current_value.strip()
        if value.upper() == 'NULL':
            values.append('')
        else:
            values.append(value)

    return values

if __name__ == "__main__":
    sql_file = "Organics RD Sept 16 2025.sql"
    output_directory = "../sql_raw"

    parse_sql_inserts(sql_file, output_directory)
