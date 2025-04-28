"""
Unit tests for repository functions
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.repositories import patch_repository, discussion_repository
from src.utils import dynamodb


class TestPatchRepository(unittest.TestCase):
    """Test the patch repository functions"""

    @patch("src.utils.dynamodb.get_item")
    def test_get_patch_by_id(self, mock_get_item):
        """Test getting a patch by ID"""
        # Setup mock
        mock_patch = {"id": "123", "name": "Test Patch"}
        mock_get_item.return_value = mock_patch

        # Execute
        result = patch_repository.get_patch_by_id("123")

        # Assert
        mock_get_item.assert_called_once_with(patch_repository.PATCHES_TABLE, {"id": "123"})
        self.assertEqual(result, mock_patch)

    @patch("src.utils.dynamodb.put_item")
    def test_save_patch(self, mock_put_item):
        """Test saving a patch"""
        # Setup
        patch_data = {
            "id": "123",
            "name": "Test Patch",
            "submitterId": "456",
            "status": "NEW",
        }

        # Execute
        result = patch_repository.save_patch(patch_data)

        # Assert
        mock_put_item.assert_called_once_with(patch_repository.PATCHES_TABLE, patch_data)
        self.assertEqual(result, patch_data)

    @patch("src.utils.dynamodb.update_item")
    def test_update_patch_status(self, mock_update_item):
        """Test updating a patch status"""
        # Setup
        mock_update_item.return_value = {"Attributes": {"status": "ACCEPTED"}}

        # Execute
        result = patch_repository.update_patch_status("123", "ACCEPTED")

        # Assert
        mock_update_item.assert_called_once()
        self.assertEqual(result, {"Attributes": {"status": "ACCEPTED"}})

    @patch("src.utils.dynamodb.query_items")
    def test_get_patches_by_status(self, mock_query_items):
        """Test getting patches by status"""
        # Setup
        mock_items = [{"id": "123"}, {"id": "456"}]
        mock_query_items.return_value = {"Items": mock_items}

        # Execute
        result, last_key = patch_repository.get_patches_by_status("NEW")

        # Assert
        mock_query_items.assert_called_once()
        self.assertEqual(result, mock_items)
        self.assertIsNone(last_key)


class TestDiscussionRepository(unittest.TestCase):
    """Test the discussion repository functions"""

    @patch("src.utils.dynamodb.get_item")
    def test_get_discussion_by_id(self, mock_get_item):
        """Test getting a discussion by ID"""
        # Setup
        mock_discussion = {"id": "123", "timestamp": "2023-01-01", "content": "Test"}
        mock_get_item.return_value = mock_discussion

        # Execute
        result = discussion_repository.get_discussion_by_id("123", "2023-01-01")

        # Assert
        mock_get_item.assert_called_once_with(
            discussion_repository.DISCUSSIONS_TABLE,
            {"id": "123", "timestamp": "2023-01-01"},
        )
        self.assertEqual(result, mock_discussion)

    @patch("src.utils.dynamodb.put_item")
    def test_save_discussion(self, mock_put_item):
        """Test saving a discussion"""
        # Setup
        discussion_data = {
            "id": "123",
            "timestamp": "2023-01-01",
            "patchId": "456",
            "content": "Test content",
        }

        # Execute
        result = discussion_repository.save_discussion(discussion_data)

        # Assert
        mock_put_item.assert_called_once_with(
            discussion_repository.DISCUSSIONS_TABLE, discussion_data
        )
        self.assertEqual(result, discussion_data)

    @patch("src.utils.dynamodb.query_items")
    def test_get_discussions_by_patch(self, mock_query_items):
        """Test getting discussions by patch ID"""
        # Setup
        mock_items = [{"id": "123"}, {"id": "456"}]
        mock_query_items.return_value = {"Items": mock_items}

        # Execute
        result, last_key = discussion_repository.get_discussions_by_patch("123")

        # Assert
        mock_query_items.assert_called_once()
        self.assertEqual(result, mock_items)
        self.assertIsNone(last_key)

    @patch("src.utils.dynamodb.query_items")
    def test_count_discussions_by_patch(self, mock_query_items):
        """Test counting discussions by patch ID"""
        # Setup
        mock_query_items.return_value = {"Count": 5}

        # Execute
        result = discussion_repository.count_discussions_by_patch("123")

        # Assert
        mock_query_items.assert_called_once()
        self.assertEqual(result, 5)


class TestDynamoDbUtils(unittest.TestCase):
    """Test the DynamoDB utility functions"""

    @patch("boto3.resource")
    def test_get_item(self, mock_resource):
        """Test the get_item function"""
        # Setup
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_table.get_item.return_value = {"Item": {"id": "123"}}

        # Execute
        with patch.object(dynamodb, "dynamodb", mock_resource.return_value):
            result = dynamodb.get_item("TestTable", {"id": "123"})

        # Assert
        mock_resource.return_value.Table.assert_called_once_with("TestTable")
        mock_table.get_item.assert_called_once_with(Key={"id": "123"})
        self.assertEqual(result, {"id": "123"})

    @patch("boto3.resource")
    def test_query_items(self, mock_resource):
        """Test the query_items function"""
        # Setup
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_table.query.return_value = {"Items": [{"id": "123"}]}

        # Execute
        with patch.object(dynamodb, "dynamodb", mock_resource.return_value):
            from boto3.dynamodb.conditions import Key

            result = dynamodb.query_items("TestTable", Key("id").eq("123"))

        # Assert
        mock_resource.return_value.Table.assert_called_once_with("TestTable")
        mock_table.query.assert_called_once()
        self.assertEqual(result, {"Items": [{"id": "123"}]})

    @patch("boto3.resource")
    def test_batch_get_items(self, mock_resource):
        """Test the batch_get_items function"""
        # Setup
        mock_resource.return_value.batch_get_item.return_value = {
            "Responses": {"TestTable": [{"id": "123"}]}
        }

        # Execute
        with patch.object(dynamodb, "dynamodb", mock_resource.return_value):
            result = dynamodb.batch_get_items({"TestTable": {"Keys": [{"id": "123"}]}})

        # Assert
        mock_resource.return_value.batch_get_item.assert_called_once()
        self.assertEqual(result, {"Responses": {"TestTable": [{"id": "123"}]}})


if __name__ == "__main__":
    unittest.main()
