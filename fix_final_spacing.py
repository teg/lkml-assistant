import re

def fix_file(filename, line_num, needed_blank_lines):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Line numbers are 1-based in the error message, but 0-based in the list
    line_idx = line_num - 1
    
    # Add blank lines before the specified line
    for i in range(needed_blank_lines):
        lines.insert(line_idx, '\n')
    
    with open(filename, 'w') as f:
        f.writelines(lines)

# Fix the test_local_dynamodb.py file again
fix_file('/Users/teg/Code/lkml-assistant/tests/integration/test_local_dynamodb.py', 11, 1)

