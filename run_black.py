#!/usr/bin/env python3
"""
Script to run Black formatter on Python files.
"""

import os
import subprocess
from pathlib import Path

def main():
    """Run black on Python files in src and tests directories."""
    files_to_format = [
        "src/functions/fetch-patches/test_mode_handler.py",
        "src/functions/fetch_patches/test_mode_handler.py",
        "src/functions/fetch-patches/index.py",
        "src/functions/fetch_patches/index.py",
        "tests/integration/direct_lambda_invoker.py",
        "src/utils/dynamodb.py",
        "tests/integration/test_local_lambda.py",
        "tests/integration/conftest.py",
        "tests/integration/test_local_dynamodb.py",
    ]
    
    # Install black if not available
    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing black formatter...")
        subprocess.run(["pip", "install", "black"], check=True)
    
    print("Running black formatter...")
    for file_path in files_to_format:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            print(f"Formatting {file_path}...")
            subprocess.run(["black", full_path], check=True)
        else:
            print(f"Warning: File not found - {file_path}")
    
    print("Black formatting complete!")

if __name__ == "__main__":
    main()