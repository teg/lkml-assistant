"""
Repository for accessing Discussion data in DynamoDB
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from boto3.dynamodb.conditions import Key, Attr

from src.utils import dynamodb
from src.models.database import DiscussionDbRecord

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get table name from environment or use default
DISCUSSIONS_TABLE = os.environ.get('DISCUSSIONS_TABLE_NAME', 'LkmlAssistant-Discussions')

def get_discussion_by_id(discussion_id: str, timestamp: Optional[str] = None) -> DiscussionDbRecord:
    """
    Get a discussion by its ID
    """
    try:
        key = {'id': discussion_id}
        if timestamp:
            key['timestamp'] = timestamp
            
        result = dynamodb.get_item(DISCUSSIONS_TABLE, key)
        return result
    except dynamodb.ItemNotFoundError:
        logger.warning(f"Discussion not found with ID: {discussion_id}")
        raise
    except Exception as e:
        logger.error(f"Error getting discussion {discussion_id}: {str(e)}")
        raise

def save_discussion(discussion: DiscussionDbRecord) -> DiscussionDbRecord:
    """
    Save a discussion to DynamoDB (create or update)
    """
    try:
        dynamodb.put_item(DISCUSSIONS_TABLE, discussion)
        return discussion
    except Exception as e:
        logger.error(f"Error saving discussion {discussion.get('id')}: {str(e)}")
        raise

def update_discussion_summary(discussion_id: str, timestamp: str, summary: str) -> Dict[str, Any]:
    """
    Update the summary for a discussion
    """
    try:
        result = dynamodb.update_item(
            DISCUSSIONS_TABLE,
            {'id': discussion_id, 'timestamp': timestamp},
            update_expression="SET summary = :summary",
            expression_attribute_values={
                ':summary': summary
            }
        )
        return result
    except Exception as e:
        logger.error(f"Error updating summary for discussion {discussion_id}: {str(e)}")
        raise

def update_discussion_sentiment(discussion_id: str, timestamp: str, sentiment: str) -> Dict[str, Any]:
    """
    Update the sentiment for a discussion
    """
    try:
        result = dynamodb.update_item(
            DISCUSSIONS_TABLE,
            {'id': discussion_id, 'timestamp': timestamp},
            update_expression="SET sentiment = :sentiment",
            expression_attribute_values={
                ':sentiment': sentiment
            }
        )
        return result
    except Exception as e:
        logger.error(f"Error updating sentiment for discussion {discussion_id}: {str(e)}")
        raise

def get_discussions_by_patch(patch_id: str, limit: int = 50, last_evaluated_key: Optional[Dict[str, Any]] = None) -> Tuple[List[DiscussionDbRecord], Optional[Dict[str, Any]]]:
    """
    Get discussions by patch ID using the PatchIndex GSI
    """
    try:
        key_condition = Key('gsi1pk').eq(f"PATCH#{patch_id}")
        
        params = {
            'table_name': DISCUSSIONS_TABLE,
            'index_name': 'PatchIndex',
            'key_condition_expression': key_condition,
            'scan_index_forward': True,  # Sort by timestamp (oldest first)
            'limit': limit
        }
        
        if last_evaluated_key:
            params['exclusive_start_key'] = last_evaluated_key
            
        response = dynamodb.query_items(**params)
        
        return response.get('Items', []), response.get('LastEvaluatedKey')
    except Exception as e:
        logger.error(f"Error querying discussions by patch {patch_id}: {str(e)}")
        raise

def get_discussions_by_thread(thread_id: str, limit: int = 50, last_evaluated_key: Optional[Dict[str, Any]] = None) -> Tuple[List[DiscussionDbRecord], Optional[Dict[str, Any]]]:
    """
    Get discussions by thread ID using the ThreadIndex GSI
    """
    try:
        key_condition = Key('gsi2pk').eq(f"THREAD#{thread_id}")
        
        params = {
            'table_name': DISCUSSIONS_TABLE,
            'index_name': 'ThreadIndex',
            'key_condition_expression': key_condition,
            'scan_index_forward': True,  # Sort by timestamp (oldest first)
            'limit': limit
        }
        
        if last_evaluated_key:
            params['exclusive_start_key'] = last_evaluated_key
            
        response = dynamodb.query_items(**params)
        
        return response.get('Items', []), response.get('LastEvaluatedKey')
    except Exception as e:
        logger.error(f"Error querying discussions by thread {thread_id}: {str(e)}")
        raise

def get_discussions_by_author(author_email: str, limit: int = 50, last_evaluated_key: Optional[Dict[str, Any]] = None) -> Tuple[List[DiscussionDbRecord], Optional[Dict[str, Any]]]:
    """
    Get discussions by author email using the AuthorIndex GSI
    """
    try:
        key_condition = Key('gsi3pk').eq(f"AUTHOR#{author_email}")
        
        params = {
            'table_name': DISCUSSIONS_TABLE,
            'index_name': 'AuthorIndex',
            'key_condition_expression': key_condition,
            'scan_index_forward': False,  # Sort by timestamp (newest first)
            'limit': limit
        }
        
        if last_evaluated_key:
            params['exclusive_start_key'] = last_evaluated_key
            
        response = dynamodb.query_items(**params)
        
        return response.get('Items', []), response.get('LastEvaluatedKey')
    except Exception as e:
        logger.error(f"Error querying discussions by author {author_email}: {str(e)}")
        raise

def delete_discussion(discussion_id: str, timestamp: str) -> Dict[str, Any]:
    """
    Delete a discussion by its ID and timestamp
    """
    try:
        result = dynamodb.delete_item(DISCUSSIONS_TABLE, {'id': discussion_id, 'timestamp': timestamp})
        return result
    except Exception as e:
        logger.error(f"Error deleting discussion {discussion_id}: {str(e)}")
        raise

def count_discussions_by_patch(patch_id: str) -> int:
    """
    Count the number of discussions for a patch
    """
    try:
        key_condition = Key('gsi1pk').eq(f"PATCH#{patch_id}")
        
        params = {
            'table_name': DISCUSSIONS_TABLE,
            'index_name': 'PatchIndex',
            'key_condition_expression': key_condition,
            'select': 'COUNT'
        }
            
        response = dynamodb.query_items(**params)
        
        return response.get('Count', 0)
    except Exception as e:
        logger.error(f"Error counting discussions for patch {patch_id}: {str(e)}")
        raise

def get_latest_discussions(limit: int = 20, last_evaluated_key: Optional[Dict[str, Any]] = None) -> Tuple[List[DiscussionDbRecord], Optional[Dict[str, Any]]]:
    """
    Get latest discussions across all patches
    Note: This is less efficient as it requires a scan operation
    """
    try:
        response = dynamodb.dynamodb.Table(DISCUSSIONS_TABLE).scan(
            Limit=limit,
            ExclusiveStartKey=last_evaluated_key if last_evaluated_key else None
        )
        
        # Sort manually by timestamp (newest first)
        items = sorted(
            response.get('Items', []),
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        return items, response.get('LastEvaluatedKey')
    except Exception as e:
        logger.error(f"Error getting latest discussions: {str(e)}")
        raise

def batch_get_discussions(discussion_ids: List[Tuple[str, str]]) -> List[DiscussionDbRecord]:
    """
    Batch get multiple discussions by their IDs and timestamps
    """
    if not discussion_ids:
        return []
        
    try:
        # Split into batches of 100 (DynamoDB batch limit)
        batch_size = 100
        all_discussions = []
        
        for i in range(0, len(discussion_ids), batch_size):
            batch = discussion_ids[i:i + batch_size]
            keys = [{'id': did, 'timestamp': ts} for did, ts in batch]
            
            request_items = {
                DISCUSSIONS_TABLE: {
                    'Keys': keys,
                    'ConsistentRead': False
                }
            }
            
            response = dynamodb.batch_get_items(request_items)
            all_discussions.extend(response.get('Responses', {}).get(DISCUSSIONS_TABLE, []))
        
        return all_discussions
    except Exception as e:
        logger.error(f"Error batch getting discussions: {str(e)}")
        raise