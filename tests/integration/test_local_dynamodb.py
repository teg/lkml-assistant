import pytest
import boto3
import json
from datetime import datetime
from decimal import Decimal
import os

# We're working directly with DynamoDB here to avoid auth issues with Podman

# Utility functions for DynamoDB format conversion


def to_dynamodb_item(python_dict):
    """Convert a Python dictionary to DynamoDB format."""
    item = {}
    for key, value in python_dict.items():
        if isinstance(value, str):
            item[key] = {"S": value}
        elif isinstance(value, int):
            item[key] = {"N": str(value)}
        elif isinstance(value, float):
            item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            item[key] = {"NULL": True}
    return item


def from_dynamodb_item(dynamodb_item):
    """Convert a DynamoDB item to Python dictionary."""
    python_dict = {}
    for key, value in dynamodb_item.items():
        if "S" in value:
            python_dict[key] = value["S"]
        elif "N" in value:
            python_dict[key] = Decimal(value["N"])
        elif "NULL" in value:
            python_dict[key] = None
    return python_dict


def test_save_and_get_patch(dynamodb_client, patches_table, sample_patch_data):
    """
    Test saving and retrieving a patch in the local DynamoDB using the client directly.
    """
    # Convert Python types to DynamoDB format using the helper function
    item = to_dynamodb_item(sample_patch_data)

    # Save the patch directly to DynamoDB
    dynamodb_client.put_item(TableName=patches_table, Item=item)

    # Retrieve the patch
    response = dynamodb_client.get_item(
        TableName=patches_table, Key={"id": {"S": sample_patch_data["id"]}}
    )

    item = response.get("Item", {})

    # Convert DynamoDB format back to Python using the helper function
    patch = from_dynamodb_item(item)

    # Verify the patch data
    assert patch is not None
    assert patch["id"] == sample_patch_data["id"]
    assert patch["name"] == sample_patch_data["name"]
    assert patch["submitterName"] == sample_patch_data["submitterName"]
    assert patch["status"] == sample_patch_data["status"]


def test_save_and_get_discussion(
    dynamodb_client,
    discussions_table,
    patches_table,
    sample_patch_data,
    sample_discussion_data,
):
    """
    Test saving and retrieving a discussion in the local DynamoDB using the client directly.
    """
    # Save the related patch first
    patch_item = {}
    for key, value in sample_patch_data.items():
        if isinstance(value, str):
            patch_item[key] = {"S": value}
        elif isinstance(value, int):
            patch_item[key] = {"N": str(value)}
        elif isinstance(value, float):
            patch_item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            patch_item[key] = {"NULL": True}

    # Save the patch directly to DynamoDB
    dynamodb_client.put_item(TableName=patches_table, Item=patch_item)

    # Convert discussion data to DynamoDB format
    discussion_item = {}
    for key, value in sample_discussion_data.items():
        if isinstance(value, str):
            discussion_item[key] = {"S": value}
        elif isinstance(value, int):
            discussion_item[key] = {"N": str(value)}
        elif isinstance(value, float):
            discussion_item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            discussion_item[key] = {"NULL": True}

    # Save the discussion directly to DynamoDB
    dynamodb_client.put_item(TableName=discussions_table, Item=discussion_item)

    # Retrieve the discussion
    response = dynamodb_client.get_item(
        TableName=discussions_table,
        Key={
            "id": {"S": sample_discussion_data["id"]},
            "timestamp": {"S": sample_discussion_data["timestamp"]},
        },
    )

    item = response.get("Item", {})

    # Convert DynamoDB format back to Python
    discussion = {}
    for key, value in item.items():
        if "S" in value:
            discussion[key] = value["S"]
        elif "N" in value:
            discussion[key] = Decimal(value["N"])
        elif "NULL" in value:
            discussion[key] = None

    # Verify the discussion data
    assert discussion is not None
    assert discussion["id"] == sample_discussion_data["id"]
    assert discussion["patchId"] == sample_discussion_data["patchId"]
    assert discussion["subject"] == sample_discussion_data["subject"]
    assert discussion["author"] == sample_discussion_data["author"]


def test_query_patches_by_status(dynamodb_client, patches_table, sample_patch_data):
    """
    Test querying patches by status from the local DynamoDB using the client directly.
    """
    # Convert Python types to DynamoDB format
    item = {}
    for key, value in sample_patch_data.items():
        if isinstance(value, str):
            item[key] = {"S": value}
        elif isinstance(value, int):
            item[key] = {"N": str(value)}
        elif isinstance(value, float):
            item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            item[key] = {"NULL": True}

    # Save the patch directly to DynamoDB
    dynamodb_client.put_item(TableName=patches_table, Item=item)

    # Query patches by status index
    response = dynamodb_client.query(
        TableName=patches_table,
        IndexName="StatusIndex",
        KeyConditionExpression="#gsi3pk = :gsi3pk",
        ExpressionAttributeNames={"#gsi3pk": "gsi3pk"},
        ExpressionAttributeValues={":gsi3pk": {"S": "STATUS#NEW"}},
        Limit=10,
    )

    # Convert DynamoDB format back to Python
    patches = []
    for item in response.get("Items", []):
        patch = {}
        for key, value in item.items():
            if "S" in value:
                patch[key] = value["S"]
            elif "N" in value:
                patch[key] = Decimal(value["N"])
            elif "NULL" in value:
                patch[key] = None
        patches.append(patch)

    # Verify results
    assert len(patches) > 0
    assert any(p["id"] == sample_patch_data["id"] for p in patches)


def test_query_discussions_by_patch(
    dynamodb_client,
    discussions_table,
    patches_table,
    sample_patch_data,
    sample_discussion_data,
):
    """
    Test querying discussions for a specific patch using the client directly.
    """
    # Save the related patch first
    patch_item = {}
    for key, value in sample_patch_data.items():
        if isinstance(value, str):
            patch_item[key] = {"S": value}
        elif isinstance(value, int):
            patch_item[key] = {"N": str(value)}
        elif isinstance(value, float):
            patch_item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            patch_item[key] = {"NULL": True}

    # Save the patch directly to DynamoDB
    dynamodb_client.put_item(TableName=patches_table, Item=patch_item)

    # Convert discussion data to DynamoDB format
    discussion_item = {}
    for key, value in sample_discussion_data.items():
        if isinstance(value, str):
            discussion_item[key] = {"S": value}
        elif isinstance(value, int):
            discussion_item[key] = {"N": str(value)}
        elif isinstance(value, float):
            discussion_item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            discussion_item[key] = {"NULL": True}

    # Save the discussion directly to DynamoDB
    dynamodb_client.put_item(TableName=discussions_table, Item=discussion_item)

    # Query discussions for the patch using the PatchIndex
    response = dynamodb_client.query(
        TableName=discussions_table,
        IndexName="PatchIndex",
        KeyConditionExpression="#gsi1pk = :gsi1pk",
        ExpressionAttributeNames={"#gsi1pk": "gsi1pk"},
        ExpressionAttributeValues={":gsi1pk": {"S": f'PATCH#{sample_patch_data["id"]}'}},
    )

    # Convert DynamoDB format back to Python
    discussions = []
    for item in response.get("Items", []):
        discussion = {}
        for key, value in item.items():
            if "S" in value:
                discussion[key] = value["S"]
            elif "N" in value:
                discussion[key] = Decimal(value["N"])
            elif "NULL" in value:
                discussion[key] = None
        discussions.append(discussion)

    # Verify results
    assert len(discussions) > 0
    assert discussions[0]["patchId"] == sample_patch_data["id"]


def test_update_patch_status(dynamodb_client, patches_table, sample_patch_data):
    """
    Test updating a patch's status directly with DynamoDB client.
    """
    # Convert Python types to DynamoDB format
    item = {}
    for key, value in sample_patch_data.items():
        if isinstance(value, str):
            item[key] = {"S": value}
        elif isinstance(value, int):
            item[key] = {"N": str(value)}
        elif isinstance(value, float):
            item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            item[key] = {"NULL": True}

    # Save the patch directly to DynamoDB
    dynamodb_client.put_item(TableName=patches_table, Item=item)

    # Update the patch status
    new_status = "ACCEPTED"
    dynamodb_client.update_item(
        TableName=patches_table,
        Key={"id": {"S": sample_patch_data["id"]}},
        UpdateExpression="SET #status = :status, #gsi3pk = :gsi3pk",
        ExpressionAttributeNames={"#status": "status", "#gsi3pk": "gsi3pk"},
        ExpressionAttributeValues={
            ":status": {"S": new_status},
            ":gsi3pk": {"S": f"STATUS#{new_status}"},
        },
    )

    # Get the updated patch
    response = dynamodb_client.get_item(
        TableName=patches_table, Key={"id": {"S": sample_patch_data["id"]}}
    )

    item = response.get("Item", {})

    # Convert DynamoDB format back to Python
    updated_patch = {}
    for key, value in item.items():
        if "S" in value:
            updated_patch[key] = value["S"]
        elif "N" in value:
            updated_patch[key] = Decimal(value["N"])
        elif "NULL" in value:
            updated_patch[key] = None

    # Verify the status was updated
    assert updated_patch["status"] == new_status
    assert updated_patch["gsi3pk"] == f"STATUS#{new_status}"


def test_count_discussions_by_patch(
    dynamodb_client,
    discussions_table,
    patches_table,
    sample_patch_data,
    sample_discussion_data,
):
    """
    Test counting discussions for a patch using the client directly.
    """
    # Save the related patch first
    patch_item = {}
    for key, value in sample_patch_data.items():
        if isinstance(value, str):
            patch_item[key] = {"S": value}
        elif isinstance(value, int):
            patch_item[key] = {"N": str(value)}
        elif isinstance(value, float):
            patch_item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            patch_item[key] = {"NULL": True}

    # Save the patch directly to DynamoDB
    dynamodb_client.put_item(TableName=patches_table, Item=patch_item)

    # Convert discussion data to DynamoDB format
    discussion_item = {}
    for key, value in sample_discussion_data.items():
        if isinstance(value, str):
            discussion_item[key] = {"S": value}
        elif isinstance(value, int):
            discussion_item[key] = {"N": str(value)}
        elif isinstance(value, float):
            discussion_item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            discussion_item[key] = {"NULL": True}

    # Save the discussion directly to DynamoDB
    dynamodb_client.put_item(TableName=discussions_table, Item=discussion_item)

    # Create a second discussion
    second_discussion = sample_discussion_data.copy()
    second_discussion["id"] = "disc-67890"
    second_discussion["messageId"] = "second-discussion@example.com"

    # Convert second discussion to DynamoDB format
    second_discussion_item = {}
    for key, value in second_discussion.items():
        if isinstance(value, str):
            second_discussion_item[key] = {"S": value}
        elif isinstance(value, int):
            second_discussion_item[key] = {"N": str(value)}
        elif isinstance(value, float):
            second_discussion_item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            # Skip nested dicts for simplicity in this test
            continue
        elif value is None:
            second_discussion_item[key] = {"NULL": True}

    # Save the second discussion directly to DynamoDB
    dynamodb_client.put_item(TableName=discussions_table, Item=second_discussion_item)

    # Count discussions for the patch using the PatchIndex
    response = dynamodb_client.query(
        TableName=discussions_table,
        IndexName="PatchIndex",
        KeyConditionExpression="#gsi1pk = :gsi1pk",
        ExpressionAttributeNames={"#gsi1pk": "gsi1pk"},
        ExpressionAttributeValues={":gsi1pk": {"S": f'PATCH#{sample_patch_data["id"]}'}},
        Select="COUNT",
    )

    # Get the count from the response
    count = response.get("Count", 0)

    # Verify count
    assert count == 2
