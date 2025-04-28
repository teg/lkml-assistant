import sys

def fix_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    # Ensure there's a single newline at the end
    if not content.endswith('\n'):
        content += '\n'
    
    # Remove trailing whitespace on lines
    lines = content.split('\n')
    new_lines = [line.rstrip() for line in lines]
    new_content = '\n'.join(new_lines)
    
    # Ensure file ends with a single newline
    if not new_content.endswith('\n'):
        new_content += '\n'
    
    with open(filename, 'w') as f:
        f.write(new_content)

for file in sys.argv[1:]:
    fix_file(file)
