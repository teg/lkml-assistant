"""
Special handler for test mode to mock Patchwork API responses
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def process_test_data(event: Dict[str, Any]):
    """
    When in test mode, use the provided test data instead of calling Patchwork API
    """
    logger.info("Running in test mode with mock data")
    
    # Extract test data from the event
    test_data = event.get("test_data", [])
    
    # Return the test data as the "API response"
    return {
        "results": test_data
    }