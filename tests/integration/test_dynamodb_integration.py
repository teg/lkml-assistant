"""
Integration tests for DynamoDB repositories
"""
import os
import sys
import unittest
import boto3
import uuid
from unittest import mock
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import repositories
from src.repositories import patch_repository, discussion_repository
from src.utils import dynamodb

# Mock environment variables
os.environ['PATCHES_TABLE_NAME'] = 'LkmlAssistant-Patches-test'
os.environ['DISCUSSIONS_TABLE_NAME'] = 'LkmlAssistant-Discussions-test'

# Use moto to mock AWS services
try:
    from moto import mock_dynamodb
except ImportError:
    print("Moto library is required for integration tests. Install it with: pip install moto")
    sys.exit(1)

@mock_dynamodb
class TestDynamoDBIntegration(unittest.TestCase):
    """Integration tests for DynamoDB operations"""
    
    def setUp(self):
        """Set up test environment"""
        # Create the mock DynamoDB tables
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create patches table
        self.patches_table = self.dynamodb.create_table(
            TableName='LkmlAssistant-Patches-test',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi2pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi2sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi3pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi3sk', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'SubmitterIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi1pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi1sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'SeriesIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi2pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi2sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi3pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi3sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create discussions table
        self.discussions_table = self.dynamodb.create_table(
            TableName='LkmlAssistant-Discussions-test',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi2pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi2sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi3pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi3sk', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'PatchIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi1pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi1sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'ThreadIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi2pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi2sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'AuthorIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi3pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi3sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.patches_table.delete()
        self.discussions_table.delete()
    
    def test_patch_repository_crud(self):
        """Test CRUD operations with patch repository"""
        # Create a test patch
        patch_id = str(uuid.uuid4())
        test_patch = {
            'id': patch_id,
            'name': 'Test Patch',
            'submitterId': '123',
            'submitterName': 'Test User',
            'submitterEmail': 'test@example.com',
            'submittedAt': datetime.utcnow().isoformat(),
            'lastUpdatedAt': datetime.utcnow().isoformat(),
            'status': 'NEW',
            'url': 'https://example.com/patch',
            'webUrl': 'https://example.com/patch',
            'mboxUrl': 'https://example.com/patch.mbox',
            'messageId': 'test-message-id',
            'content': 'Test content',
            'discussionCount': 0,
            'gsi1pk': 'SUBMITTER#123',
            'gsi1sk': f"DATE#{datetime.utcnow().isoformat()}",
            'gsi3pk': 'STATUS#NEW',
            'gsi3sk': f"DATE#{datetime.utcnow().isoformat()}"
        }
        
        # 1. Test save_patch
        saved_patch = patch_repository.save_patch(test_patch)
        self.assertEqual(saved_patch['id'], patch_id)
        
        # 2. Test get_patch_by_id
        retrieved_patch = patch_repository.get_patch_by_id(patch_id)
        self.assertEqual(retrieved_patch['id'], patch_id)
        self.assertEqual(retrieved_patch['name'], 'Test Patch')
        
        # 3. Test update_patch_status
        patch_repository.update_patch_status(patch_id, 'ACCEPTED')
        updated_patch = patch_repository.get_patch_by_id(patch_id)
        self.assertEqual(updated_patch['status'], 'ACCEPTED')
        
        # 4. Test get_patches_by_status
        patches, _ = patch_repository.get_patches_by_status('ACCEPTED')
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]['id'], patch_id)
        
        # 5. Test update_discussion_count
        patch_repository.update_discussion_count(patch_id, 5)
        updated_patch = patch_repository.get_patch_by_id(patch_id)
        self.assertEqual(updated_patch['discussionCount'], 5)
        
        # 6. Test get_patches_by_submitter
        patches, _ = patch_repository.get_patches_by_submitter('123')
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]['id'], patch_id)
        
        # 7. Test delete_patch
        patch_repository.delete_patch(patch_id)
        with self.assertRaises(dynamodb.ItemNotFoundError):
            patch_repository.get_patch_by_id(patch_id)
    
    def test_discussion_repository_crud(self):
        """Test CRUD operations with discussion repository"""
        # Create a test patch first
        patch_id = str(uuid.uuid4())
        test_patch = {
            'id': patch_id,
            'name': 'Test Patch',
            'submitterId': '123',
            'submitterName': 'Test User',
            'submitterEmail': 'test@example.com',
            'submittedAt': datetime.utcnow().isoformat(),
            'lastUpdatedAt': datetime.utcnow().isoformat(),
            'status': 'NEW',
            'discussionCount': 0
        }
        patch_repository.save_patch(test_patch)
        
        # Create a test discussion
        discussion_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        test_discussion = {
            'id': discussion_id,
            'timestamp': timestamp,
            'patchId': patch_id,
            'authorName': 'Test Author',
            'authorEmail': 'author@example.com',
            'messageId': 'test-message-id',
            'threadId': 'test-thread-id',
            'subject': 'Test Subject',
            'content': 'Test content',
            'isReview': False,
            'gsi1pk': f"PATCH#{patch_id}",
            'gsi1sk': f"DATE#{timestamp}",
            'gsi2pk': 'THREAD#test-thread-id',
            'gsi2sk': f"DATE#{timestamp}",
            'gsi3pk': 'AUTHOR#author@example.com',
            'gsi3sk': f"DATE#{timestamp}"
        }
        
        # 1. Test save_discussion
        saved_discussion = discussion_repository.save_discussion(test_discussion)
        self.assertEqual(saved_discussion['id'], discussion_id)
        
        # 2. Test get_discussion_by_id
        retrieved_discussion = discussion_repository.get_discussion_by_id(discussion_id, timestamp)
        self.assertEqual(retrieved_discussion['id'], discussion_id)
        self.assertEqual(retrieved_discussion['subject'], 'Test Subject')
        
        # 3. Test update_discussion_summary
        discussion_repository.update_discussion_summary(discussion_id, timestamp, 'Updated summary')
        updated_discussion = discussion_repository.get_discussion_by_id(discussion_id, timestamp)
        self.assertEqual(updated_discussion['summary'], 'Updated summary')
        
        # 4. Test get_discussions_by_patch
        discussions, _ = discussion_repository.get_discussions_by_patch(patch_id)
        self.assertEqual(len(discussions), 1)
        self.assertEqual(discussions[0]['id'], discussion_id)
        
        # 5. Test get_discussions_by_thread
        discussions, _ = discussion_repository.get_discussions_by_thread('test-thread-id')
        self.assertEqual(len(discussions), 1)
        self.assertEqual(discussions[0]['id'], discussion_id)
        
        # 6. Test get_discussions_by_author
        discussions, _ = discussion_repository.get_discussions_by_author('author@example.com')
        self.assertEqual(len(discussions), 1)
        self.assertEqual(discussions[0]['id'], discussion_id)
        
        # 7. Test count_discussions_by_patch
        count = discussion_repository.count_discussions_by_patch(patch_id)
        self.assertEqual(count, 1)
        
        # 8. Test delete_discussion
        discussion_repository.delete_discussion(discussion_id, timestamp)
        with self.assertRaises(dynamodb.ItemNotFoundError):
            discussion_repository.get_discussion_by_id(discussion_id, timestamp)

if __name__ == '__main__':
    unittest.main()