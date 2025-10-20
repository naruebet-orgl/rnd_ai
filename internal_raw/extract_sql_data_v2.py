#!/usr/bin/env python3
"""
Extract data from MySQL dump file and save each table to separate CSV files
Version 2 - Improved SQL parsing with better handling of escapes and quotes
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
            if current_table and not current_columns:
                col_match = re.match(r'\s+`(\w+)`', line)
                if col_match and not line.strip().startswith('PRIMARY') and not line.strip().startswith('KEY'):
                    current_columns.append(col_match.group(1))

            # Detect INSERT statements
            if current_table and line.startswith('INSERT INTO'):
                # Create CSV writer if not exists
                if not current_writer:
                    csv_file = output_path / f"{current_table}.csv"
                    current_file = open(csv_file, 'w', newline='', encoding='utf-8')
                    current_writer = csv.writer(current_file, quoting=csv.QUOTE_ALL, escapechar='\\')
                    # Write header
                    if current_columns:
                        current_writer.writerow(current_columns)

                # Extract VALUES portion
                values_match = re.search(r'VALUES\s+(.+);?\s*$', line, re.DOTALL)
                if values_match:
                    values_str = values_match.group(1).rstrip(';')

                    # Parse rows from INSERT statement
                    rows = parse_sql_rows(values_str, len(current_columns))

                    for row in rows:
                        if len(row) == len(current_columns):
                            current_writer.writerow(row)
                            row_count += 1
                        else:
                            print(f"  Warning: Row has {len(row)} fields, expected {len(current_columns)}")

        # Close last file
        if current_file:
            current_file.close()
            print(f"  Saved {row_count:,} rows to {current_table}.csv")

    print(f"\n{'='*60}")
    print(f"Extraction complete!")
    print(f"Total tables processed: {table_count}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}")

def parse_sql_rows(values_str, expected_cols):
    """
    Parse SQL VALUES string into rows
    Properly handles quoted strings with commas, escapes, etc.
    """
    rows = []
    i = 0

    while i < len(values_str):
        # Skip whitespace and commas between rows
        while i < len(values_str) and values_str[i] in ' \t\n\r,':
            i += 1

        if i >= len(values_str):
            break

        # Expect opening parenthesis
        if values_str[i] != '(':
            i += 1
            continue

        i += 1  # Skip '('

        # Parse values in this row
        row = []
        while i < len(values_str) and values_str[i] != ')':
            # Skip whitespace
            while i < len(values_str) and values_str[i] in ' \t\n\r':
                i += 1

            if i >= len(values_str) or values_str[i] == ')':
                break

            # Parse one value
            value, i = parse_one_value(values_str, i)
            row.append(value)

            # Skip whitespace
            while i < len(values_str) and values_str[i] in ' \t\n\r':
                i += 1

            # Skip comma if present
            if i < len(values_str) and values_str[i] == ',':
                i += 1

        if i < len(values_str) and values_str[i] == ')':
            i += 1  # Skip ')'

        if len(row) == expected_cols:
            rows.append(row)

    return rows

def parse_one_value(text, start_pos):
    """
    Parse a single SQL value starting at start_pos
    Returns (value, new_position)
    """
    i = start_pos

    # Skip leading whitespace
    while i < len(text) and text[i] in ' \t\n\r':
        i += 1

    if i >= len(text):
        return ('', i)

    # Check for NULL
    if text[i:i+4].upper() == 'NULL':
        return ('', i + 4)

    # Check for quoted string
    if text[i] in ("'", '"'):
        quote_char = text[i]
        i += 1
        value = ''

        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                # Handle escape sequences
                next_char = text[i + 1]
                if next_char == 'n':
                    value += '\n'
                elif next_char == 't':
                    value += '\t'
                elif next_char == 'r':
                    value += '\r'
                elif next_char == '\\':
                    value += '\\'
                elif next_char == quote_char:
                    value += quote_char
                elif next_char == '0':
                    value += '\0'
                else:
                    value += next_char
                i += 2
            elif text[i] == quote_char:
                # Check for doubled quote (SQL escape)
                if i + 1 < len(text) and text[i + 1] == quote_char:
                    value += quote_char
                    i += 2
                else:
                    # End of string
                    i += 1
                    break
            else:
                value += text[i]
                i += 1

        return (value, i)

    # Unquoted value (number, etc.)
    value = ''
    while i < len(text) and text[i] not in ',)':
        value += text[i]
        i += 1

    return (value.strip(), i)

if __name__ == "__main__":
    sql_file = "Organics RD Sept 16 2025.sql"
    output_directory = "../sql_raw"

    parse_sql_inserts(sql_file, output_directory)
