"""
Utilities for interacting with the Patchwork API
"""

import time
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Callable, Union
from requests.exceptions import RequestException
from src.utils.api import retry_with_backoff

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Patchwork API URL
PATCHWORK_API_URL = (
    "https://patchwork.kernel.org/api/1.1/projects/rust-for-linux/patches/"
)


class PatchworkAPIError(Exception):
    """Exception raised for Patchwork API errors"""

    pass


@retry_with_backoff(max_retries=5, initial_backoff=2.0)
def fetch_patches(
    page: int = 1, per_page: int = 20, order: str = "-date"
) -> Dict[str, Any]:
    """
    Fetch patches from the Patchwork API with retries
    """
    url = PATCHWORK_API_URL
    params = {"page": page, "per_page": per_page, "order": order}

    logger.info(
        f"Fetching patches from Patchwork API: page={page}, per_page={per_page}"
    )

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])
        count = data.get("count", 0)

        logger.info(
            f"Successfully fetched {len(results)} patches from Patchwork API (total: {count})"
        )

        return data
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from Patchwork API: {str(e)}")
        if e.response.status_code == 429:
            # Rate limit hit, retry after a longer delay
            logger.warning("Rate limit hit, waiting for 60 seconds before retry")
            time.sleep(60)
        raise PatchworkAPIError(f"HTTP error: {str(e)}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to Patchwork API: {str(e)}")
        raise PatchworkAPIError(f"Connection error: {str(e)}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to Patchwork API: {str(e)}")
        raise PatchworkAPIError(f"Timeout error: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from Patchwork API: {str(e)}")
        raise PatchworkAPIError(f"Request error: {str(e)}")
    except ValueError as e:
        logger.error(f"Error parsing JSON from Patchwork API: {str(e)}")
        raise PatchworkAPIError(f"JSON parse error: {str(e)}")


def fetch_all_patches(
    max_pages: int = 5, per_page: int = 50, order: str = "-date"
) -> List[Dict[str, Any]]:
    """
    Fetch all patches across multiple pages
    """
    all_patches = []
    current_page = 1
    more_pages = True

    while more_pages and current_page <= max_pages:
        try:
            data = fetch_patches(page=current_page, per_page=per_page, order=order)

            # Get results
            results = data.get("results", [])
            all_patches.extend(results)

            # Check if there are more pages
            more_pages = data.get("next") is not None

            # Increment page counter
            current_page += 1

            # Small delay to avoid overwhelming the API
            time.sleep(1)
        except PatchworkAPIError as e:
            logger.error(f"Error fetching page {current_page}: {str(e)}")
            if current_page > 1:
                # We've already got some data, so just return what we have
                logger.warning(f"Returning {len(all_patches)} patches retrieved so far")
                break
            else:
                # We've got no data at all, so re-raise the exception
                raise

    return all_patches


def fetch_patch_by_id(patch_id: Union[str, int]) -> Dict[str, Any]:
    """
    Fetch a specific patch by ID
    """
    url = f"{PATCHWORK_API_URL}{patch_id}/"

    try:

        @retry_with_backoff(max_retries=3, initial_backoff=1.0)
        def _fetch():
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()

        return _fetch()
    except Exception as e:
        logger.error(f"Error fetching patch {patch_id}: {str(e)}")
        raise PatchworkAPIError(f"Error fetching patch {patch_id}: {str(e)}")


def search_patches(query: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Search for patches matching a query
    """
    url = PATCHWORK_API_URL
    params = {"q": query, "page": page, "per_page": per_page}

    try:

        @retry_with_backoff(max_retries=3, initial_backoff=1.0)
        def _search():
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()

        return _search()
    except Exception as e:
        logger.error(f"Error searching patches with query '{query}': {str(e)}")
        raise PatchworkAPIError(f"Error searching patches: {str(e)}")
