#!/usr/bin/env python3
import csv
import argparse
import os
import sys

def clean_csv(input_file, output_file, columns_to_remove):
    """
    Removes specified columns from a CSV file
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path for the cleaned CSV file
        columns_to_remove: List of column names to remove
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found.")
            return False
        
        # Read input CSV
        with open(input_file, 'r', encoding='utf-8') as csv_in:
            reader = csv.DictReader(csv_in)
            
            # Get all fieldnames from the original file
            all_fields = reader.fieldnames
            if not all_fields:
                print("Error: Could not determine columns in the input file.")
                return False
            
            # Create new fieldnames list by excluding columns_to_remove
            new_fields = [field for field in all_fields if field not in columns_to_remove]
            
            # Prepare rows to write
            rows = []
            for row in reader:
                # Create a new row with only the desired columns
                new_row = {field: row[field] for field in new_fields}
                rows.append(new_row)
                
        # Write to output CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csv_out:
            writer = csv.DictWriter(csv_out, fieldnames=new_fields)
            writer.writeheader()
            writer.writerows(rows)
            
        print(f"Successfully processed CSV file:")
        print(f"- Input: {input_file}")
        print(f"- Output: {output_file}")
        print(f"- Removed columns: {', '.join(columns_to_remove)}")
        print(f"- Processed {len(rows)} rows")
        return True
        
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Remove specific columns from a CSV file')
    parser.add_argument('input_file', help='Input CSV file to process')
    parser.add_argument('--output', '-o', help='Output file path (default: adds "_cleaned" suffix)')
    parser.add_argument('--columns', '-c', nargs='+', 
                        default=['user_name', 'dislikes', 'creation_timestamp', 'time_str'],
                        help='Columns to remove (default: user_name dislikes creation_timestamp time_str)')
    parser.add_argument('--backup', '-b', action='store_true', 
                        help='Create a backup of the input file before overwriting')
    args = parser.parse_args()
    
    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        # Split the input filename and add "_cleaned" before the extension
        base, ext = os.path.splitext(args.input_file)
        output_file = f"{base}_cleaned{ext}"
    
    # Check if output file exists
    if os.path.exists(output_file) and output_file != args.input_file:
        response = input(f"Output file '{output_file}' already exists. Overwrite? (y/n): ")
        if response.lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            return
    
    # Create backup if requested and we're overwriting the input file
    if args.backup and output_file == args.input_file:
        backup_file = f"{args.input_file}.bak"
        try:
            import shutil
            shutil.copy2(args.input_file, backup_file)
            print(f"Created backup: {backup_file}")
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
    
    # Process the file
    if clean_csv(args.input_file, output_file, args.columns):
        print("CSV cleanup completed successfully.")
    else:
        print("CSV cleanup failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())