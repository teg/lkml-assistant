"""
DynamoDB utility functions for data access
"""

import os
import json
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get region and endpoint configuration
region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
dynamodb_endpoint = os.environ.get("DYNAMODB_ENDPOINT")

# Initialize DynamoDB resource with appropriate configuration
if dynamodb_endpoint:
    # For local development or testing with DynamoDB Local
    logger.info(f"Using DynamoDB local endpoint: {dynamodb_endpoint}")
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=dynamodb_endpoint,
        region_name=region,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test")
    )
else:
    # For production use in AWS
    logger.info(f"Using DynamoDB in region: {region}")
    dynamodb = boto3.resource("dynamodb", region_name=region)

# Initialize table references
patches_table = dynamodb.Table(
    os.environ.get("PATCHES_TABLE_NAME", "LkmlAssistant-Patches")
)
discussions_table = dynamodb.Table(
    os.environ.get("DISCUSSIONS_TABLE_NAME", "LkmlAssistant-Discussions")
)


class DatabaseError(Exception):
    """Base exception for database errors"""

    pass


class ItemNotFoundError(DatabaseError):
    """Exception raised when an item is not found"""

    pass


class QueryError(DatabaseError):
    """Exception raised when a query fails"""

    pass


def handle_db_error(func):
    """
    Decorator to handle common DynamoDB errors
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")

            logger.error(f"DynamoDB error: {error_code} - {error_message}")

            if error_code == "ResourceNotFoundException":
                raise ItemNotFoundError(f"Item not found: {error_message}")
            elif error_code == "ConditionalCheckFailedException":
                raise DatabaseError(f"Condition check failed: {error_message}")
            else:
                raise DatabaseError(f"Database error: {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise DatabaseError(f"Unexpected database error: {str(e)}")

    return wrapper


@handle_db_error

def get_item(table_name: str, key: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a single item from DynamoDB
    """
    table = dynamodb.Table(table_name)
    response = table.get_item(Key=key)

    item = response.get("Item")
    if not item:
        logger.info(f"Item not found with key: {key}")
        return None

    return item


@handle_db_error

def put_item(
    table_name: str, item: Dict[str, Any], condition_expression: Optional[str] = None
) -> Dict[str, Any]:
    """
    Put an item into DynamoDB with optional condition expression
    """
    table = dynamodb.Table(table_name)

    params = {"Item": item}
    if condition_expression:
        params["ConditionExpression"] = condition_expression

    response = table.put_item(**params)
    return response


@handle_db_error

def update_item(
    table_name: str,
    key: Dict[str, Any],
    update_expression: str,
    expression_attribute_values: Dict[str, Any],
    condition_expression: Optional[str] = None,
    expression_attribute_names: Optional[Dict[str, str]] = None,
    return_values: str = "UPDATED_NEW",
) -> Dict[str, Any]:
    """
    Update an item in DynamoDB
    """
    table = dynamodb.Table(table_name)

    params = {
        "Key": key,
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
        "ReturnValues": return_values,
    }

    if condition_expression:
        params["ConditionExpression"] = condition_expression

    if expression_attribute_names:
        params["ExpressionAttributeNames"] = expression_attribute_names

    response = table.update_item(**params)
    return response


@handle_db_error

def delete_item(
    table_name: str, key: Dict[str, Any], condition_expression: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete an item from DynamoDB
    """
    table = dynamodb.Table(table_name)

    params = {"Key": key}
    if condition_expression:
        params["ConditionExpression"] = condition_expression

    response = table.delete_item(**params)
    return response


@handle_db_error

def query_items(
    table_name: str,
    key_condition_expression: Key,
    filter_expression: Optional[Union[Attr, Dict[str, Any]]] = None,
    index_name: Optional[str] = None,
    limit: Optional[int] = None,
    scan_index_forward: bool = True,
    exclusive_start_key: Optional[Dict[str, Any]] = None,
    projection_expression: Optional[str] = None,
    expression_attribute_names: Optional[Dict[str, str]] = None,
    expression_attribute_values: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Query items from DynamoDB
    """
    table = dynamodb.Table(table_name)

    params = {
        "KeyConditionExpression": key_condition_expression,
        "ScanIndexForward": scan_index_forward,
    }

    if index_name:
        params["IndexName"] = index_name

    if filter_expression:
        params["FilterExpression"] = filter_expression

    if limit is not None:
        params["Limit"] = limit

    if exclusive_start_key:
        params["ExclusiveStartKey"] = exclusive_start_key

    if projection_expression:
        params["ProjectionExpression"] = projection_expression

    if expression_attribute_names:
        params["ExpressionAttributeNames"] = expression_attribute_names

    if expression_attribute_values:
        params["ExpressionAttributeValues"] = expression_attribute_values

    response = table.query(**params)
    return response


@handle_db_error

def batch_get_items(request_items: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Batch get items from multiple tables
    """
    response = dynamodb.batch_get_item(RequestItems=request_items)
    return response


@handle_db_error

def batch_write_items(request_items: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Batch write items to multiple tables
    """
    response = dynamodb.batch_write_item(RequestItems=request_items)
    return response


@handle_db_error

def transaction_write_items(transaction_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Write items in a transaction
    """
    # Create DynamoDB client which supports transact_write_items
    if dynamodb_endpoint:
        dynamodb_client = boto3.client(
            "dynamodb",
            endpoint_url=dynamodb_endpoint,
            region_name=region,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test")
        )
    else:
        dynamodb_client = boto3.client("dynamodb", region_name=region)

    response = dynamodb_client.transact_write_items(TransactItems=transaction_items)
    return response


@handle_db_error

def transaction_get_items(transaction_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get items in a transaction
    """
    # Create DynamoDB client which supports transact_get_items
    if dynamodb_endpoint:
        dynamodb_client = boto3.client(
            "dynamodb",
            endpoint_url=dynamodb_endpoint,
            region_name=region,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test")
        )
    else:
        dynamodb_client = boto3.client("dynamodb", region_name=region)

    response = dynamodb_client.transact_get_items(TransactItems=transaction_items)
    return response
