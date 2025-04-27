import json
import os
import boto3
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
patches_table = dynamodb.Table(os.environ.get('PATCHES_TABLE_NAME'))

# Patchwork API endpoint
PATCHWORK_API_URL = 'https://patchwork.kernel.org/api/1.1/projects/rust-for-linux/patches/'

def create_patch_record(patch_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Patchwork API data into our database schema
    """
    now = datetime.utcnow().isoformat()
    patch_id = str(patch_data['id'])
    
    # Extract submitter info
    submitter = patch_data.get('submitter', {})
    submitter_id = str(submitter.get('id', '0'))
    submitter_name = submitter.get('name', 'Unknown')
    submitter_email = submitter.get('email', '')
    
    # Extract series info if available
    series_data = patch_data.get('series', [])
    series_id = None
    series_name = None
    series_version = None
    
    if series_data and len(series_data) > 0:
        first_series = series_data[0]
        series_id = str(first_series.get('id'))
        series_name = first_series.get('name')
        series_version = first_series.get('version')
    
    # Create DynamoDB item
    patch_item = {
        # Primary key
        'id': patch_id,
        
        # Metadata fields
        'name': patch_data.get('name', ''),
        'submitterId': submitter_id,
        'submitterName': submitter_name,
        'submitterEmail': submitter_email,
        'submittedAt': patch_data.get('date', now),
        'lastUpdatedAt': now,
        'status': 'NEW',  # Default status
        
        # URL references
        'url': patch_data.get('url', ''),
        'webUrl': patch_data.get('web_url', ''),
        'mboxUrl': patch_data.get('mbox', ''),
        
        # Email threading
        'messageId': patch_data.get('msgid', ''),
        
        # Content
        'commitRef': patch_data.get('commit_ref'),
        'pullUrl': patch_data.get('pull_url'),
        'hash': patch_data.get('hash', ''),
        'content': patch_data.get('content', ''),
        
        # Tracking
        'discussionCount': 0,
        
        # GSI fields - for querying by submitter
        'gsi1pk': f"SUBMITTER#{submitter_id}",
        'gsi1sk': f"DATE#{patch_data.get('date', now)}",
        
        # GSI fields - for querying by status
        'gsi3pk': 'STATUS#NEW',
        'gsi3sk': f"DATE#{patch_data.get('date', now)}"
    }
    
    # Add series fields if available
    if series_id:
        patch_item['seriesId'] = series_id
        patch_item['seriesName'] = series_name
        patch_item['seriesVersion'] = series_version
        patch_item['gsi2pk'] = f"SERIES#{series_id}"
        patch_item['gsi2sk'] = f"DATE#{patch_data.get('date', now)}"
    
    return patch_item

def get_patches(page: int = 1, per_page: int = 20) -> List[Dict[str, Any]]:
    """
    Get patches from Patchwork API with pagination
    """
    response = requests.get(
        PATCHWORK_API_URL, 
        params={
            'page': page, 
            'per_page': per_page,
            'order': '-date'  # Get newest patches first
        }
    )
    response.raise_for_status()
    
    # Extract results from API response
    data = response.json()
    return data.get('results', [])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to fetch patches from Patchwork API and store in DynamoDB
    """
    try:
        print(f"Starting fetch patches lambda at {datetime.utcnow().isoformat()}")
        
        # Get configuration from event or use defaults
        page = event.get('page', 1)
        per_page = event.get('per_page', 20)
        
        # Get patches from Patchwork
        patches = get_patches(page, per_page)
        print(f"Retrieved {len(patches)} patches from Patchwork API")
        
        # Process and store patches
        for patch in patches:
            patch_item = create_patch_record(patch)
            
            # Store in DynamoDB
            patches_table.put_item(Item=patch_item)
        
        # Check if we need to process more pages
        if len(patches) == per_page and event.get('process_all_pages', False):
            # Schedule another invocation for the next page
            # This would typically be done with Step Functions or EventBridge
            print(f"Scheduling processing for page {page + 1}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {len(patches)} patches',
                'count': len(patches),
                'page': page
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error fetching patches: {str(e)}'
            })
        }