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
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("post_deploy_runner")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run post-deployment tests against a specific environment"
    )

    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Environment to test (default: dev)",
    )

    parser.add_argument("--profile", help="AWS profile to use")

    parser.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")

    parser.add_argument("--test-file", help="Specific test file to run")

    parser.add_argument(
        "--report-dir", default="test-reports", help="Directory to store test reports"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument(
        "--no-metrics", action="store_true", help="Disable CloudWatch metrics reporting"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Run tests without making AWS API calls"
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

    # Generate summary text file for CI integration
    summary_file = os.path.join(report_dir, "summary.txt")
    generate_summary(junit_report, summary_file, args.env, elapsed_time, exit_code)

    # Record metrics to CloudWatch if AWS credentials are available
    if not args.no_metrics and not args.dry_run:
        try:
            record_cloudwatch_metrics(args.env, exit_code, elapsed_time)
        except Exception as e:
            logger.warning(f"Failed to record CloudWatch metrics: {e}")

    return exit_code


def generate_summary(junit_report, summary_file, environment, elapsed_time, exit_code):
    """Generate a summary text file from JUnit XML report."""
    import xml.etree.ElementTree as ET

    try:
        tree = ET.parse(junit_report)
        root = tree.getroot()

        # Extract test counts
        tests = int(root.attrib.get("tests", 0))
        failures = int(root.attrib.get("failures", 0))
        errors = int(root.attrib.get("errors", 0))
        skipped = int(root.attrib.get("skipped", 0))
        passed = tests - failures - errors - skipped

        # Calculate pass rate
        pass_rate = (passed / tests * 100) if tests > 0 else 0

        # Write summary to file
        with open(summary_file, "w") as f:
            f.write(f"# Post-Deployment Test Results for {environment} environment\n\n")
            f.write(f"## Summary\n")
            f.write(f"- **Status**: {'✅ PASSED' if exit_code == 0 else '❌ FAILED'}\n")
            f.write(f"- **Pass rate**: {pass_rate:.1f}%\n")
            f.write(f"- **Duration**: {elapsed_time:.2f} seconds\n\n")

            f.write(f"## Test counts\n")
            f.write(f"- **Total**: {tests}\n")
            f.write(f"- **Passed**: {passed}\n")
            f.write(f"- **Failed**: {failures}\n")
            f.write(f"- **Errors**: {errors}\n")
            f.write(f"- **Skipped**: {skipped}\n\n")

            # List failed tests if any
            if failures > 0 or errors > 0:
                f.write(f"## Failed tests\n")
                for testcase in root.findall(".//testcase"):
                    for failure in testcase.findall("./failure"):
                        f.write(
                            f"- **{testcase.attrib.get('name')}**: {failure.attrib.get('message')}\n"
                        )
                    for error in testcase.findall("./error"):
                        f.write(
                            f"- **{testcase.attrib.get('name')}**: {error.attrib.get('message')}\n"
                        )

        logger.info(f"Test summary saved to {summary_file}")
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        # Create a basic summary if XML parsing fails
        with open(summary_file, "w") as f:
            f.write(f"# Post-Deployment Test Results for {environment} environment\n\n")
            f.write(f"## Summary\n")
            f.write(f"- **Status**: {'✅ PASSED' if exit_code == 0 else '❌ FAILED'}\n")
            f.write(f"- **Duration**: {elapsed_time:.2f} seconds\n")


def record_cloudwatch_metrics(environment, exit_code, elapsed_time):
    """Record test metrics to CloudWatch."""
    import boto3
    from datetime import datetime

    try:
        # Initialize CloudWatch client
        cw = boto3.client("cloudwatch")

        # Record test execution metrics
        cw.put_metric_data(
            Namespace="LkmlAssistant/PostDeployTests",
            MetricData=[
                {
                    "MetricName": "TestRun",
                    "Dimensions": [
                        {"Name": "Environment", "Value": environment},
                    ],
                    "Value": 1,
                    "Unit": "Count",
                    "Timestamp": datetime.now(),
                },
                {
                    "MetricName": "TestSuccess",
                    "Dimensions": [
                        {"Name": "Environment", "Value": environment},
                    ],
                    "Value": 1 if exit_code == 0 else 0,
                    "Unit": "Count",
                    "Timestamp": datetime.now(),
                },
                {
                    "MetricName": "TestDuration",
                    "Dimensions": [
                        {"Name": "Environment", "Value": environment},
                    ],
                    "Value": elapsed_time,
                    "Unit": "Seconds",
                    "Timestamp": datetime.now(),
                },
            ],
        )

        logger.info("CloudWatch metrics recorded successfully")
    except Exception as e:
        logger.warning(f"Failed to record CloudWatch metrics: {e}")
        raise


if __name__ == "__main__":
    args = parse_args()
    sys.exit(run_tests(args))
