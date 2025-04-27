import json
import os
import boto3
import requests
from datetime import datetime

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
patches_table = dynamodb.Table(os.environ.get('PATCHES_TABLE_NAME'))

# Patchwork API endpoint
PATCHWORK_API_URL = 'https://patchwork.kernel.org/api/1.1/projects/rust-for-linux/patches/'

def handler(event, context):
    """
    Lambda function to fetch patches from Patchwork API and store in DynamoDB
    """
    try:
        # Get patches from Patchwork
        response = requests.get(PATCHWORK_API_URL, params={'page': 1, 'per_page': 20})
        response.raise_for_status()
        
        patches = response.json()
        
        # Process and store patches
        for patch in patches:
            patch_item = {
                'id': str(patch['id']),
                'name': patch['name'],
                'submitter': patch['submitter']['name'],
                'submittedAt': patch['date'],
                'status': 'NEW',  # Default status
                'url': patch['url'],
                'messageId': patch.get('msgid', ''),
                'summary': '',  # Will be populated later
                'lastUpdated': datetime.utcnow().isoformat()
            }
            
            # Store in DynamoDB
            patches_table.put_item(Item=patch_item)
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully processed {len(patches)} patches')
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error fetching patches: {str(e)}')
        }