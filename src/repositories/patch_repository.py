"""
Repository for accessing Patch data in DynamoDB
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from boto3.dynamodb.conditions import Key, Attr

from src.utils import dynamodb
from src.models.database import PatchDbRecord

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get table name from environment or use default
PATCHES_TABLE = os.environ.get("PATCHES_TABLE_NAME", "LkmlAssistant-Patches")


def get_patch_by_id(patch_id: str) -> PatchDbRecord:
    """
    Get a patch by its ID
    """
    try:
        result = dynamodb.get_item(PATCHES_TABLE, {"id": patch_id})
        return result
    except dynamodb.ItemNotFoundError:
        logger.warning(f"Patch not found with ID: {patch_id}")
        raise
    except Exception as e:
        logger.error(f"Error getting patch {patch_id}: {str(e)}")
        raise


def save_patch(patch: PatchDbRecord) -> PatchDbRecord:
    """
    Save a patch to DynamoDB (create or update)
    """
    try:
        dynamodb.put_item(PATCHES_TABLE, patch)
        return patch
    except Exception as e:
        logger.error(f"Error saving patch {patch.get('id')}: {str(e)}")
        raise


def update_patch_status(patch_id: str, status: str) -> Dict[str, Any]:
    """
    Update the status of a patch
    """
    try:
        now = datetime.utcnow().isoformat()
        result = dynamodb.update_item(
            PATCHES_TABLE,
            {"id": patch_id},
            update_expression="SET #status = :status, lastUpdatedAt = :now, gsi3pk = :gsi3pk",
            expression_attribute_values={
                ":status": status,
                ":now": now,
                ":gsi3pk": f"STATUS#{status}",
            },
            expression_attribute_names={"#status": "status"},
        )
        return result
    except Exception as e:
        logger.error(f"Error updating status for patch {patch_id}: {str(e)}")
        raise


def update_discussion_count(patch_id: str, count: int) -> Dict[str, Any]:
    """
    Update the discussion count for a patch
    """
    try:
        now = datetime.utcnow().isoformat()
        result = dynamodb.update_item(
            PATCHES_TABLE,
            {"id": patch_id},
            update_expression="SET discussionCount = :count, lastUpdatedAt = :now",
            expression_attribute_values={":count": count, ":now": now},
        )
        return result
    except Exception as e:
        logger.error(f"Error updating discussion count for patch {patch_id}: {str(e)}")
        raise


def update_summary(patch_id: str, summary: str) -> Dict[str, Any]:
    """
    Update the summary for a patch
    """
    try:
        now = datetime.utcnow().isoformat()
        result = dynamodb.update_item(
            PATCHES_TABLE,
            {"id": patch_id},
            update_expression="SET summary = :summary, lastUpdatedAt = :now",
            expression_attribute_values={":summary": summary, ":now": now},
        )
        return result
    except Exception as e:
        logger.error(f"Error updating summary for patch {patch_id}: {str(e)}")
        raise


def get_patches_by_status(
    status: str, limit: int = 50, last_evaluated_key: Optional[Dict[str, Any]] = None
) -> Tuple[List[PatchDbRecord], Optional[Dict[str, Any]]]:
    """
    Get patches by status using the StatusIndex GSI
    """
    try:
        key_condition = Key("gsi3pk").eq(f"STATUS#{status}")

        params = {
            "table_name": PATCHES_TABLE,
            "index_name": "StatusIndex",
            "key_condition_expression": key_condition,
            "scan_index_forward": False,  # Sort by most recent first
            "limit": limit,
        }

        if last_evaluated_key:
            params["exclusive_start_key"] = last_evaluated_key

        response = dynamodb.query_items(**params)

        return response.get("Items", []), response.get("LastEvaluatedKey")
    except Exception as e:
        logger.error(f"Error querying patches by status {status}: {str(e)}")
        raise


def get_patches_by_submitter(
    submitter_id: str,
    limit: int = 50,
    last_evaluated_key: Optional[Dict[str, Any]] = None,
) -> Tuple[List[PatchDbRecord], Optional[Dict[str, Any]]]:
    """
    Get patches by submitter using the SubmitterIndex GSI
    """
    try:
        key_condition = Key("gsi1pk").eq(f"SUBMITTER#{submitter_id}")

        params = {
            "table_name": PATCHES_TABLE,
            "index_name": "SubmitterIndex",
            "key_condition_expression": key_condition,
            "scan_index_forward": False,  # Sort by most recent first
            "limit": limit,
        }

        if last_evaluated_key:
            params["exclusive_start_key"] = last_evaluated_key

        response = dynamodb.query_items(**params)

        return response.get("Items", []), response.get("LastEvaluatedKey")
    except Exception as e:
        logger.error(f"Error querying patches by submitter {submitter_id}: {str(e)}")
        raise


def get_patches_by_series(
    series_id: str, limit: int = 50, last_evaluated_key: Optional[Dict[str, Any]] = None
) -> Tuple[List[PatchDbRecord], Optional[Dict[str, Any]]]:
    """
    Get patches by series using the SeriesIndex GSI
    """
    try:
        key_condition = Key("gsi2pk").eq(f"SERIES#{series_id}")

        params = {
            "table_name": PATCHES_TABLE,
            "index_name": "SeriesIndex",
            "key_condition_expression": key_condition,
            "scan_index_forward": True,  # Sort by position or date
            "limit": limit,
        }

        if last_evaluated_key:
            params["exclusive_start_key"] = last_evaluated_key

        response = dynamodb.query_items(**params)

        return response.get("Items", []), response.get("LastEvaluatedKey")
    except Exception as e:
        logger.error(f"Error querying patches by series {series_id}: {str(e)}")
        raise


def get_recent_patches(
    limit: int = 20, last_evaluated_key: Optional[Dict[str, Any]] = None
) -> Tuple[List[PatchDbRecord], Optional[Dict[str, Any]]]:
    """
    Get recent patches using the StatusIndex GSI with the 'NEW' status
    """
    try:
        key_condition = Key("gsi3pk").eq("STATUS#NEW")

        params = {
            "table_name": PATCHES_TABLE,
            "index_name": "StatusIndex",
            "key_condition_expression": key_condition,
            "scan_index_forward": False,  # Sort by most recent first
            "limit": limit,
        }

        if last_evaluated_key:
            params["exclusive_start_key"] = last_evaluated_key

        response = dynamodb.query_items(**params)

        return response.get("Items", []), response.get("LastEvaluatedKey")
    except Exception as e:
        logger.error(f"Error querying recent patches: {str(e)}")
        raise


def delete_patch(patch_id: str) -> Dict[str, Any]:
    """
    Delete a patch by its ID
    """
    try:
        result = dynamodb.delete_item(PATCHES_TABLE, {"id": patch_id})
        return result
    except Exception as e:
        logger.error(f"Error deleting patch {patch_id}: {str(e)}")
        raise


def batch_get_patches(patch_ids: List[str]) -> List[PatchDbRecord]:
    """
    Batch get multiple patches by their IDs
    """
    if not patch_ids:
        return []

    try:
        # Split into batches of 100 (DynamoDB batch limit)
        batch_size = 100
        all_patches = []

        for i in range(0, len(patch_ids), batch_size):
            batch = patch_ids[i : i + batch_size]
            keys = [{"id": pid} for pid in batch]

            request_items = {PATCHES_TABLE: {"Keys": keys, "ConsistentRead": False}}

            response = dynamodb.batch_get_items(request_items)
            all_patches.extend(response.get("Responses", {}).get(PATCHES_TABLE, []))

        return all_patches
    except Exception as e:
        logger.error(f"Error batch getting patches: {str(e)}")
        raise
