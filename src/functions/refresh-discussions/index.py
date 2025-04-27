"""
Lambda function to refresh discussions for recent patches
"""
import json
import os
import boto3
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add project root to Python path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.repositories import patch_repository, discussion_repository

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Lambda client for invoking other functions
lambda_client = boto3.client('lambda')

# Name of the fetch discussions Lambda function
FETCH_DISCUSSIONS_LAMBDA = os.environ.get('FETCH_DISCUSSIONS_LAMBDA', 'LkmlAssistant-FetchDiscussions')

def get_recent_patches(days_to_look_back: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get patches from the last N days
    """
    # Calculate cutoff date
    cutoff_date = (datetime.utcnow() - timedelta(days=days_to_look_back)).isoformat()
    
    try:
        # Use a combination of statuses to get relevant patches
        statuses = ['NEW', 'UNDER_REVIEW', 'ACCEPTED']
        all_patches = []
        
        for status in statuses:
            patches, _ = patch_repository.get_patches_by_status(status, limit=limit)
            
            # Filter by date
            recent_patches = [
                p for p in patches 
                if p.get('submittedAt', '9999-01-01') >= cutoff_date
            ]
            
            all_patches.extend(recent_patches)
            
            # If we've reached our limit, stop
            if len(all_patches) >= limit:
                break
        
        # Sort by submittedAt descending and limit
        all_patches.sort(key=lambda p: p.get('submittedAt', ''), reverse=True)
        return all_patches[:limit]
    
    except Exception as e:
        logger.error(f"Error getting recent patches: {str(e)}")
        return []

def refresh_discussions_for_patch(patch_id: str, message_id: str) -> bool:
    """
    Trigger the fetch-discussions Lambda for a patch
    """
    if not message_id:
        logger.warning(f"No message ID for patch {patch_id}, skipping discussion refresh")
        return False
    
    try:
        payload = {
            'patch_id': patch_id,
            'message_id': message_id,
            'source': 'refresh-discussions'
        }
        
        # Invoke the fetch-discussions Lambda asynchronously
        response = lambda_client.invoke(
            FunctionName=FETCH_DISCUSSIONS_LAMBDA,
            InvocationType='Event',  # Asynchronous
            Payload=json.dumps(payload)
        )
        
        status_code = response.get('StatusCode')
        if status_code == 202:  # 202 Accepted
            logger.info(f"Successfully triggered discussion refresh for patch {patch_id}")
            return True
        else:
            logger.warning(f"Unexpected status code {status_code} when triggering discussion refresh for patch {patch_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error triggering discussion refresh for patch {patch_id}: {str(e)}")
        return False

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to refresh discussions for recent patches
    """
    try:
        logger.info(f"Starting refresh discussions lambda at {datetime.utcnow().isoformat()}")
        
        # Get configuration from event or use defaults
        days_to_look_back = event.get('days_to_look_back', 30)
        limit = event.get('limit', 100)
        source = event.get('source', 'manual')
        
        # Get recent patches
        patches = get_recent_patches(days_to_look_back, limit)
        logger.info(f"Found {len(patches)} recent patches to refresh discussions for")
        
        # Track success/failure
        success_count = 0
        failure_count = 0
        
        # Process each patch
        for patch in patches:
            patch_id = patch.get('id')
            message_id = patch.get('messageId')
            
            if not message_id:
                logger.warning(f"Patch {patch_id} has no message ID, skipping")
                failure_count += 1
                continue
            
            # Trigger discussion refresh
            success = refresh_discussions_for_patch(patch_id, message_id)
            if success:
                success_count += 1
            else:
                failure_count += 1
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Refresh discussions triggered for {success_count} patches, {failure_count} failures',
                'source': source,
                'success_count': success_count,
                'failure_count': failure_count,
                'total_patches': len(patches)
            })
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error refreshing discussions: {str(e)}'
            })
        }