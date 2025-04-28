import pytest
import boto3
import json
from datetime import datetime
from src.repositories import patch_repository, discussion_repository


def test_save_and_get_patch(patches_table, sample_patch_data):
    """
    Test saving and retrieving a patch in the local DynamoDB.
    """
    # Save the patch
    patch_repository.save_patch(sample_patch_data)
    
    # Retrieve the patch
    patch = patch_repository.get_patch_by_id(sample_patch_data["id"])
    
    # Verify the patch data
    assert patch is not None
    assert patch["id"] == sample_patch_data["id"]
    assert patch["name"] == sample_patch_data["name"]
    assert patch["submitterName"] == sample_patch_data["submitterName"]
    assert patch["status"] == sample_patch_data["status"]


def test_save_and_get_discussion(discussions_table, patches_table, sample_patch_data, sample_discussion_data):
    """
    Test saving and retrieving a discussion in the local DynamoDB.
    """
    # Save the related patch first
    patch_repository.save_patch(sample_patch_data)
    
    # Save the discussion
    discussion_repository.save_discussion(sample_discussion_data)
    
    # Retrieve the discussion
    discussion = discussion_repository.get_discussion_by_id(
        sample_discussion_data["id"], 
        sample_discussion_data["timestamp"]
    )
    
    # Verify the discussion data
    assert discussion is not None
    assert discussion["id"] == sample_discussion_data["id"]
    assert discussion["patchId"] == sample_discussion_data["patchId"]
    assert discussion["subject"] == sample_discussion_data["subject"]
    assert discussion["author"] == sample_discussion_data["author"]


def test_query_patches_by_status(patches_table, sample_patch_data):
    """
    Test querying patches by status from the local DynamoDB.
    """
    # Save the patch
    patch_repository.save_patch(sample_patch_data)
    
    # Query patches by status
    patches = patch_repository.get_patches_by_status("NEW", limit=10)
    
    # Verify results
    assert len(patches) > 0
    assert any(p["id"] == sample_patch_data["id"] for p in patches)


def test_query_discussions_by_patch(discussions_table, patches_table, sample_patch_data, sample_discussion_data):
    """
    Test querying discussions for a specific patch.
    """
    # Save the related patch first
    patch_repository.save_patch(sample_patch_data)
    
    # Save the discussion
    discussion_repository.save_discussion(sample_discussion_data)
    
    # Query discussions for the patch
    discussions = discussion_repository.get_discussions_by_patch(sample_patch_data["id"])
    
    # Verify results
    assert len(discussions) > 0
    assert discussions[0]["patchId"] == sample_patch_data["id"]


def test_update_patch_status(patches_table, sample_patch_data):
    """
    Test updating a patch's status.
    """
    # Save the patch
    patch_repository.save_patch(sample_patch_data)
    
    # Update the patch status
    new_status = "ACCEPTED"
    patch_repository.update_patch_status(sample_patch_data["id"], new_status)
    
    # Get the updated patch
    updated_patch = patch_repository.get_patch_by_id(sample_patch_data["id"])
    
    # Verify the status was updated
    assert updated_patch["status"] == new_status
    assert updated_patch["gsi3pk"] == f"STATUS#{new_status}"


def test_count_discussions_by_patch(discussions_table, patches_table, sample_patch_data, sample_discussion_data):
    """
    Test counting discussions for a patch.
    """
    # Save the related patch first
    patch_repository.save_patch(sample_patch_data)
    
    # Save multiple discussions for the same patch
    discussion_repository.save_discussion(sample_discussion_data)
    
    # Create a second discussion
    second_discussion = sample_discussion_data.copy()
    second_discussion["id"] = "disc-67890"
    second_discussion["messageId"] = "second-discussion@example.com"
    discussion_repository.save_discussion(second_discussion)
    
    # Count discussions
    count = discussion_repository.count_discussions_by_patch(sample_patch_data["id"])
    
    # Verify count
    assert count == 2