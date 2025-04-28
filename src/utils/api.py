"""
Utility functions for API interactions
"""

import time
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Callable
from requests.exceptions import RequestException

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    backoff_multiplier: float = 2.0,
    errors_to_retry: List[Exception] = None,
) -> Callable:
    """
    Decorator to retry a function with exponential backoff
    """
    if errors_to_retry is None:
        errors_to_retry = [RequestException]

    def wrapper(*args, **kwargs):
        retries = 0
        backoff = initial_backoff

        while True:
            try:
                return func(*args, **kwargs)
            except tuple(errors_to_retry) as e:
                retries += 1
                if retries > max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded: {str(e)}")
                    raise

                wait_time = backoff * (2 ** (retries - 1))
                logger.warning(
                    f"Retry {retries}/{max_retries} after error: {str(e)}. Waiting {wait_time:.2f}s"
                )
                time.sleep(wait_time)

    return wrapper


@retry_with_backoff

def fetch_api_data(url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Fetch data from an API with retry logic
    """
    logger.info(f"Fetching data from {url}")
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def paginate_api_results(
    url: str,
    params: Dict[str, Any] = None,
    results_key: str = "results",
    next_key: str = "next",
    page_key: str = "page",
    per_page_key: str = "per_page",
    max_pages: int = 5,
) -> List[Dict[str, Any]]:
    """
    Paginate through API results
    """
    if params is None:
        params = {}

    all_results = []
    current_page = 1

    while current_page <= max_pages:
        # Update pagination parameters
        params[page_key] = current_page

        # Fetch current page
        page_data = fetch_api_data(url, params)

        # Extract results
        results = page_data.get(results_key, [])
        all_results.extend(results)

        # Check if there are more pages
        if not page_data.get(next_key):
            break

        current_page += 1

    return all_results
