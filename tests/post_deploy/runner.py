#!/usr/bin/env python3
"""
Post-Deployment Test Runner

This script runs post-deployment tests against a specific environment.
It can be used manually or integrated into CI/CD pipelines.
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime

# Add project root to path to ensure imports work correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Try to import pytest, installing if needed
try:
    import pytest
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-html"])
    import pytest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("post_deploy_runner")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run post-deployment tests against a specific environment")
    
    parser.add_argument(
        "--env", 
        choices=["dev", "staging", "prod"], 
        default="dev",
        help="Environment to test (default: dev)"
    )
    
    parser.add_argument(
        "--profile", 
        help="AWS profile to use"
    )
    
    parser.add_argument(
        "--region", 
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    
    parser.add_argument(
        "--test-file", 
        help="Specific test file to run"
    )
    
    parser.add_argument(
        "--report-dir", 
        default="test-reports",
        help="Directory to store test reports"
    )
    
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Verbose output"
    )
    
    return parser.parse_args()


def run_tests(args):
    """Run the post-deployment tests."""
    # Set environment variables for tests
    os.environ["TEST_ENVIRONMENT"] = args.env
    os.environ["AWS_REGION"] = args.region
    if args.profile:
        logger.info(f"Using AWS profile: {args.profile}")
        os.environ["AWS_PROFILE"] = args.profile
        # Also set boto3 config environment variables
        os.environ["AWS_DEFAULT_PROFILE"] = args.profile
    
    # Set up pytest arguments
    pytest_args = ["-xvs" if args.verbose else "-v"]
    
    # Add specific test file if provided
    if args.test_file:
        pytest_args.append(args.test_file)
    else:
        # Otherwise run all post-deployment tests
        pytest_args.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Set up test reporting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(args.report_dir, f"{args.env}_{timestamp}")
    os.makedirs(report_dir, exist_ok=True)
    
    # Add JUnit XML reporting
    junit_report = os.path.join(report_dir, "junit-report.xml")
    pytest_args.extend(["--junitxml", junit_report])
    
    # Add HTML reporting
    html_report = os.path.join(report_dir, "html-report.html")
    pytest_args.extend(["--html", html_report, "--self-contained-html"])
    
    logger.info(f"Running post-deployment tests for {args.env} environment")
    logger.info(f"Test reports will be saved to {report_dir}")
    
    start_time = time.time()
    exit_code = pytest.main(pytest_args)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Tests completed in {elapsed_time:.2f} seconds with exit code {exit_code}")
    logger.info(f"Test reports saved to {report_dir}")
    
    return exit_code


if __name__ == "__main__":
    args = parse_args()
    sys.exit(run_tests(args))