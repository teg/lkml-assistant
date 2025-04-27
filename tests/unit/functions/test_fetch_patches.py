"""
Unit tests for the fetch-patches Lambda function
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the Lambda function code
from src.functions.fetch_patches.index import handler, create_patch_record, trigger_discussions_fetch

# Mock environment variables
os.environ['PATCHES_TABLE_NAME'] = 'test-patches-table'
os.environ['FETCH_DISCUSSIONS_LAMBDA'] = 'test-fetch-discussions'

class TestFetchPatches(unittest.TestCase):
    """Test the fetch-patches Lambda function"""
    
    @patch('src.functions.fetch_patches.index.patchwork_api.fetch_patches')
    @patch('src.functions.fetch_patches.index.patch_repository.save_patch')
    @patch('src.functions.fetch_patches.index.trigger_discussions_fetch')
    def test_handler_success(self, mock_trigger, mock_save, mock_fetch):
        """Test the handler function in the happy path"""
        # Setup mocks
        mock_patch_data = {
            'id': 123,
            'name': 'Test Patch',
            'submitter': {
                'id': 456,
                'name': 'Test User',
                'email': 'test@example.com'
            },
            'date': '2023-01-01T12:00:00Z',
            'url': 'https://example.com/patch/123',
            'web_url': 'https://example.com/patch/123',
            'mbox': 'https://example.com/patch/123.mbox',
            'msgid': 'test-message-id',
            'content': 'Test content'
        }
        
        # Mock the API response
        mock_fetch.return_value = {
            'results': [mock_patch_data],
            'count': 1
        }
        
        # Mock the save operation
        mock_save.return_value = {'id': '123'}
        
        # Run the Lambda handler
        event = {
            'page': 1,
            'per_page': 10,
            'fetch_discussions': True
        }
        context = MagicMock()
        
        response = handler(event, context)
        
        # Verify function calls
        mock_fetch.assert_called_once_with(page=1, per_page=10, order='-date')
        mock_save.assert_called_once()
        mock_trigger.assert_called_once_with('123', 'test-message-id')
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        
        # Parse the response body
        body = json.loads(response['body'])
        self.assertEqual(body['count'], 1)
        self.assertEqual(body['page'], 1)
    
    def test_create_patch_record(self):
        """Test creating a patch record from API data"""
        # Test data
        patch_data = {
            'id': 123,
            'name': 'Test Patch',
            'submitter': {
                'id': 456,
                'name': 'Test User',
                'email': 'test@example.com'
            },
            'date': '2023-01-01T12:00:00Z',
            'url': 'https://example.com/patch/123',
            'web_url': 'https://example.com/patch/123',
            'mbox': 'https://example.com/patch/123.mbox',
            'msgid': 'test-message-id',
            'content': 'Test content',
            'hash': 'abcd1234',
            'series': [
                {
                    'id': 789,
                    'name': 'Test Series',
                    'version': 1
                }
            ]
        }
        
        # Create the record
        record = create_patch_record(patch_data)
        
        # Verify record fields
        self.assertEqual(record['id'], '123')
        self.assertEqual(record['name'], 'Test Patch')
        self.assertEqual(record['submitterId'], '456')
        self.assertEqual(record['submitterName'], 'Test User')
        self.assertEqual(record['submitterEmail'], 'test@example.com')
        self.assertEqual(record['submittedAt'], '2023-01-01T12:00:00Z')
        self.assertEqual(record['messageId'], 'test-message-id')
        self.assertEqual(record['url'], 'https://example.com/patch/123')
        self.assertEqual(record['status'], 'NEW')
        self.assertEqual(record['discussionCount'], 0)
        
        # Check GSI fields
        self.assertEqual(record['gsi1pk'], 'SUBMITTER#456')
        self.assertEqual(record['gsi3pk'], 'STATUS#NEW')
        
        # Check series fields
        self.assertEqual(record['seriesId'], '789')
        self.assertEqual(record['seriesName'], 'Test Series')
        self.assertEqual(record['seriesVersion'], 1)
        self.assertEqual(record['gsi2pk'], 'SERIES#789')
    
    @patch('src.functions.fetch_patches.index.lambda_client.invoke')
    def test_trigger_discussions_fetch(self, mock_invoke):
        """Test triggering the fetch-discussions Lambda"""
        # Setup mock
        mock_invoke.return_value = {'StatusCode': 202}
        
        # Call the function
        trigger_discussions_fetch('123', 'test-message-id')
        
        # Verify Lambda invoke
        mock_invoke.assert_called_once()
        args, kwargs = mock_invoke.call_args
        
        # Check function name
        self.assertEqual(kwargs['FunctionName'], 'test-fetch-discussions')
        
        # Check invocation type
        self.assertEqual(kwargs['InvocationType'], 'Event')
        
        # Parse payload
        payload = json.loads(kwargs['Payload'])
        self.assertEqual(payload['patch_id'], '123')
        self.assertEqual(payload['message_id'], 'test-message-id')
    
    @patch('src.functions.fetch_patches.index.patchwork_api.fetch_patches')
    def test_handler_no_results(self, mock_fetch):
        """Test handling when no patches are returned"""
        # Mock empty API response
        mock_fetch.return_value = {
            'results': [],
            'count': 0
        }
        
        # Run the Lambda handler
        event = {'page': 1, 'per_page': 10}
        context = MagicMock()
        
        response = handler(event, context)
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        
        # Parse the response body
        body = json.loads(response['body'])
        self.assertEqual(body['count'], 0)
    
    @patch('src.functions.fetch_patches.index.patchwork_api.fetch_patches')
    def test_handler_api_error(self, mock_fetch):
        """Test handling API errors gracefully"""
        # Mock API error
        mock_fetch.side_effect = Exception("API Error")
        
        # Run the Lambda handler
        event = {'page': 1, 'per_page': 10}
        context = MagicMock()
        
        response = handler(event, context)
        
        # Verify error response
        self.assertEqual(response['statusCode'], 500)
        
        # Check error message
        body = json.loads(response['body'])
        self.assertIn('Error', body['message'])

if __name__ == '__main__':
    unittest.main()