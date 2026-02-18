#!/usr/bin/env python3
"""
Script to remove duplicate layout code from dash_app_testing_addis.py
Keeps lines 1-521 and lines 2007+ (removes lines 522-2006)
"""

input_file = "dash_app_testing_addis.py"
output_file = "dash_app_testing_addis_cleaned.py"

with open(input_file, 'r', encoding='utf-8') as f:
    all_lines = f.readlines()

# Keep lines 1-506 (indices 0-505) and lines 2009+ (indices 2008+)
keep_lines = all_lines[:506] + all_lines[2008:]

with open(output_file, 'w', encoding='utf-8') as f:
    f.writelines(keep_lines)

print(f"Original file: {len(all_lines)} lines")
print(f"Cleaned file: {len(keep_lines)} lines")
print(f"Removed: {len(all_lines) - len(keep_lines)} lines")
print(f"\nCreated {output_file}")
print("Review the file, then rename it to replace the original if correct.")
