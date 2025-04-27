"""
Utilities for publishing CloudWatch metrics
"""
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize CloudWatch client
cloudwatch = boto3.client('cloudwatch')

# Default namespace for all metrics
DEFAULT_NAMESPACE = 'LkmlAssistant'

def publish_metric(metric_name: str, value: float, unit: str = 'Count', 
                  namespace: str = DEFAULT_NAMESPACE, dimensions: Optional[List[Dict[str, str]]] = None) -> bool:
    """
    Publish a metric to CloudWatch
    """
    try:
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = dimensions
        
        response = cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[metric_data]
        )
        
        logger.debug(f"Published metric {metric_name}={value} {unit}")
        return True
    except Exception as e:
        logger.error(f"Error publishing metric {metric_name}: {str(e)}")
        return False

def record_lambda_invocation(function_name: str, success: bool = True, 
                            duration_ms: Optional[float] = None, 
                            record_count: Optional[int] = None) -> None:
    """
    Record Lambda invocation metrics
    """
    # Get the source if specified in environment
    source = os.environ.get('METRIC_SOURCE', 'unknown')
    
    # Common dimensions for all metrics
    dimensions = [
        {'Name': 'FunctionName', 'Value': function_name},
        {'Name': 'Source', 'Value': source}
    ]
    
    # Record invocation count
    publish_metric(
        'Invocations', 
        1, 
        'Count',
        dimensions=dimensions
    )
    
    # Record success/failure
    status = 'Success' if success else 'Failure'
    publish_metric(
        'InvocationStatus', 
        1, 
        'Count',
        dimensions=dimensions + [{'Name': 'Status', 'Value': status}]
    )
    
    # Record duration if provided
    if duration_ms is not None:
        publish_metric(
            'Duration', 
            duration_ms, 
            'Milliseconds',
            dimensions=dimensions
        )
    
    # Record processed item count if provided
    if record_count is not None:
        publish_metric(
            'RecordCount', 
            record_count, 
            'Count',
            dimensions=dimensions
        )

def record_api_call(api_name: str, endpoint: str, success: bool = True, 
                  latency_ms: Optional[float] = None,
                  status_code: Optional[int] = None) -> None:
    """
    Record API call metrics
    """
    # Common dimensions
    dimensions = [
        {'Name': 'API', 'Value': api_name},
        {'Name': 'Endpoint', 'Value': endpoint}
    ]
    
    # Record call count
    publish_metric(
        'ApiCalls', 
        1, 
        'Count',
        dimensions=dimensions
    )
    
    # Record success/failure
    status = 'Success' if success else 'Failure'
    publish_metric(
        'ApiCallStatus', 
        1, 
        'Count',
        dimensions=dimensions + [{'Name': 'Status', 'Value': status}]
    )
    
    # Record latency if provided
    if latency_ms is not None:
        publish_metric(
            'ApiLatency', 
            latency_ms, 
            'Milliseconds',
            dimensions=dimensions
        )
    
    # Record status code if provided
    if status_code is not None:
        publish_metric(
            'ApiStatusCode', 
            1, 
            'Count',
            dimensions=dimensions + [{'Name': 'StatusCode', 'Value': str(status_code)}]
        )