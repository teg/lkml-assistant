import json
import os
import boto3
import logging
import sys

# Add project root to Python path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import datetime
from typing import Dict, List, Any, Optional

# Fix imports for AWS Lambda environment
try:
    # Try standard import pattern first (for local development)
    from src.repositories import patch_repository
    from src.utils import patchwork_api
    from src.functions.fetch_patches import test_mode_handler
except ImportError:
    # Fall back to relative imports (for AWS Lambda)
    import repositories.patch_repository as patch_repository
    import utils.patchwork_api as patchwork_api
    import test_mode_handler

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Lambda client for invoking other functions
# Allow custom endpoint for testing
aws_endpoint_url = os.environ.get("AWS_ENDPOINT_URL")
if aws_endpoint_url:
    lambda_client = boto3.client("lambda", endpoint_url=aws_endpoint_url)
else:
    lambda_client = boto3.client("lambda")

# Name of the fetch discussions Lambda function
FETCH_DISCUSSIONS_LAMBDA = os.environ.get(
    "FETCH_DISCUSSIONS_LAMBDA", "LkmlAssistant-FetchDiscussions"
)


def create_patch_record(patch_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Patchwork API data into our database schema
    """
    now = datetime.utcnow().isoformat()
    patch_id = str(patch_data["id"])

    # Extract submitter info
    submitter = patch_data.get("submitter", {})
    submitter_id = str(submitter.get("id", "0"))
    submitter_name = submitter.get("name", "Unknown")
    submitter_email = submitter.get("email", "")

    # Extract series info if available
    series_data = patch_data.get("series", [])
    series_id = None
    series_name = None
    series_version = None

    if series_data and len(series_data) > 0:
        first_series = series_data[0]
        series_id = str(first_series.get("id"))
        series_name = first_series.get("name")
        series_version = first_series.get("version")

    # Create DynamoDB item
    patch_item = {
        # Primary key
        "id": patch_id,
        # Metadata fields
        "name": patch_data.get("name", ""),
        "submitterId": submitter_id,
        "submitterName": submitter_name,
        "submitterEmail": submitter_email,
        "submittedAt": patch_data.get("date", now),
        "lastUpdatedAt": now,
        "status": "NEW",  # Default status
        # URL references
        "url": patch_data.get("url", ""),
        "webUrl": patch_data.get("web_url", ""),
        "mboxUrl": patch_data.get("mbox", ""),
        # Email threading
        "messageId": patch_data.get("msgid", ""),
        # Content
        "commitRef": patch_data.get("commit_ref"),
        "pullUrl": patch_data.get("pull_url"),
        "hash": patch_data.get("hash", ""),
        "content": patch_data.get("content", ""),
        # Tracking
        "discussionCount": 0,
        # GSI fields - for querying by submitter
        "gsi1pk": f"SUBMITTER#{submitter_id}",
        "gsi1sk": f"DATE#{patch_data.get('date', now)}",
        # GSI fields - for querying by status
        "gsi3pk": "STATUS#NEW",
        "gsi3sk": f"DATE#{patch_data.get('date', now)}",
    }

    # Add series fields if available
    if series_id:
        patch_item["seriesId"] = series_id
        patch_item["seriesName"] = series_name
        patch_item["seriesVersion"] = series_version
        patch_item["gsi2pk"] = f"SERIES#{series_id}"
        patch_item["gsi2sk"] = f"DATE#{patch_data.get('date', now)}"

    return patch_item


def get_patches(page: int = 1, per_page: int = 20, event: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Get patches from Patchwork API with pagination and retry
    """
    # Check if we're in test mode with mock data
    if event and event.get("test_mode", False):
        try:
            data = test_mode_handler.process_test_data(event)
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Error processing test data: {str(e)}")
            return []

    try:
        # Use the patchwork_api module which handles retries
        data = patchwork_api.fetch_patches(page=page, per_page=per_page, order="-date")
        return data.get("results", [])
    except patchwork_api.PatchworkAPIError as e:
        logger.error(f"Error fetching patches: {str(e)}")
        return []


def trigger_discussions_fetch(patch_id: str, message_id: str) -> None:
    """
    Trigger the fetch-discussions Lambda for a patch
    """
    if not message_id:
        logger.warning(f"No message ID for patch {patch_id}, skipping discussion fetch")
        return

    try:
        payload = {"patch_id": patch_id, "message_id": message_id}

        # Invoke the fetch-discussions Lambda asynchronously
        response = lambda_client.invoke(
            FunctionName=FETCH_DISCUSSIONS_LAMBDA,
            InvocationType="Event",  # Asynchronous
            Payload=json.dumps(payload),
        )

        status_code = response.get("StatusCode")
        if status_code == 202:  # 202 Accepted
            logger.info(f"Successfully triggered discussion fetch for patch {patch_id}")
        else:
            logger.warning(
                f"Unexpected status code {status_code} when triggering discussion fetch for patch {patch_id}"
            )

    except Exception as e:
        logger.error(
            f"Error triggering discussion fetch for patch {patch_id}: {str(e)}"
        )


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to fetch patches from Patchwork API and store in DynamoDB
    """
    try:
        logger.info(f"Starting fetch patches lambda at {datetime.utcnow().isoformat()}")

        # Get configuration from event or use defaults
        page = event.get("page", 1)
        per_page = event.get("per_page", 20)
        fetch_discussions = event.get("fetch_discussions", True)

        # Get patches from Patchwork
        patches = get_patches(page, per_page, event)
        logger.info(f"Retrieved {len(patches)} patches from Patchwork API")

        # Process and store patches
        for patch in patches:
            patch_item = create_patch_record(patch)
            patch_id = patch_item["id"]
            message_id = patch_item["messageId"]

            # Store in DynamoDB using the repository
            patch_repository.save_patch(patch_item)
            logger.info(f"Stored patch {patch_id} in DynamoDB")

            # Trigger discussion fetch for this patch if requested
            if fetch_discussions and message_id:
                trigger_discussions_fetch(patch_id, message_id)

        # Check if we need to process more pages
        if len(patches) == per_page and event.get("process_all_pages", False):
            # For now, just log that we should process more pages
            # In a more complete implementation, we would use Step Functions or EventBridge
            logger.info(f"More pages available, should process page {page + 1}")

            # For demo purposes, we'll recursively invoke ourselves for the next page
            # Note: In production, this would be better handled by Step Functions
            if page < 2:  # Limit to 2 pages for development (previously 5)
                try:
                    next_event = event.copy()
                    next_event["page"] = page + 1

                    lambda_client.invoke(
                        FunctionName=context.function_name,
                        InvocationType="Event",
                        Payload=json.dumps(next_event),
                    )
                    logger.info(f"Scheduled processing for page {page + 1}")
                except Exception as e:
                    logger.error(f"Error scheduling next page: {str(e)}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Successfully processed {len(patches)} patches",
                    "count": len(patches),
                    "page": page,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")

        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error fetching patches: {str(e)}"}),
        }