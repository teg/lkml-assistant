#!/usr/bin/env python3
"""
Script to completely fix blank lines after function decorators.
E304: blank lines found after function decorator
"""

import os
import re

def fix_file(file_path):
    """Fix decorator spacing issues in the given file."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    output_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this is a decorator line
        if line.strip().startswith('@'):
            # Add this line to output
            output_lines.append(line)
            
            # Skip any blank lines after decorator
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            
            # If we found a def after skipping blanks, we need to fix
            if j < len(lines) and (lines[j].strip().startswith('def ') or lines[j].strip().startswith('class ')):
                # Add the function/class definition immediately after decorator
                output_lines.append(lines[j])
                i = j  # Move past the function def
            else:
                # Not a function decorator or already correct
                # Just add the next line
                if j < len(lines):
                    output_lines.append(lines[j])
                i = j
        else:
            # Not a decorator line, just add it
            output_lines.append(line)
        i += 1
    
    # Write back to the file
    with open(file_path, 'w') as f:
        f.writelines(output_lines)
    
    print(f"Fixed {file_path}")

def main():
    """Fix decorator spacing issues in Python files."""
    file_paths = [
        "src/utils/api.py",
        "src/utils/dynamodb.py",
        "src/utils/patchwork_api.py",
        "tests/integration/conftest.py"
    ]
    
    for file_path in file_paths:
        fix_file(file_path)

if __name__ == "__main__":
    main()