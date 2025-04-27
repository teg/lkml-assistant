"""
Lambda function to fetch discussions from lore.kernel.org
"""

import json
import os
import re
import boto3
import requests
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from email.parser import Parser
from email.policy import default
from bs4 import BeautifulSoup

# Add project root to Python path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.repositories import patch_repository, discussion_repository

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lore.kernel.org base URL - API endpoint doesn't exist, we need to scrape
LORE_BASE_URL = "https://lore.kernel.org/rust-for-linux/"


def extract_message_id(text: str) -> Optional[str]:
    """
    Extract message ID from email headers or content
    """
    pattern = r"<([^<>@\s]+@[^<>@\s]+)>"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def parse_email_content(raw_content: str) -> Dict[str, Any]:
    """
    Parse raw email content using email.parser
    """
    parser = Parser(policy=default)
    email_message = parser.parsestr(raw_content)

    # Extract headers
    headers = {}
    for key in email_message.keys():
        headers[key.lower()] = email_message[key]

    # Get content
    content = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                content = part.get_payload(decode=True).decode(
                    "utf-8", errors="replace"
                )
                break
    else:
        content = email_message.get_payload(decode=True).decode(
            "utf-8", errors="replace"
        )

    # Extract message IDs
    message_id = extract_message_id(headers.get("message-id", ""))
    in_reply_to = extract_message_id(headers.get("in-reply-to", ""))
    references = headers.get("references", "")

    # Get subject and clean it up
    subject = headers.get("subject", "").replace("Re: ", "").strip()

    # Get from and parse into name and email
    from_header = headers.get("from", "")
    author_name = from_header
    author_email = ""

    # Try to extract email address
    email_match = re.search(r"<([^<>]+)>", from_header)
    if email_match:
        author_email = email_match.group(1)
        name_part = from_header.split("<")[0].strip()
        if name_part:
            author_name = name_part

    return {
        "headers": headers,
        "content": content,
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "references": references,
        "subject": subject,
        "author_name": author_name,
        "author_email": author_email,
    }


def fetch_email_by_message_id(message_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch an email from lore.kernel.org by message ID
    """
    # Lore.kernel.org allows fetching emails by message-id by adding '/raw' to the URL
    url = f"{LORE_BASE_URL}/{message_id}/raw"

    try:
        response = requests.get(url)
        response.raise_for_status()

        # Parse the raw email content
        return parse_email_content(response.text)
    except Exception as e:
        logger.error(f"Error fetching email {message_id}: {str(e)}")
        return None


def fetch_thread_for_patch(patch_id: str, message_id: str) -> List[Dict[str, Any]]:
    """
    Fetch the thread for a given patch by its message ID
    """
    # For lore.kernel.org, we need to fetch the thread page and extract links
    thread_url = f"{LORE_BASE_URL}/{message_id}/"

    try:
        response = requests.get(thread_url)
        response.raise_for_status()

        # Parse HTML to extract all message links
        soup = BeautifulSoup(response.text, "html.parser")
        message_links = []

        # Find links to messages in the thread
        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Look for message IDs in links
            if re.match(
                r"^/rust-for-linux/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/$",
                href,
            ):
                message_id = href.split("/")[2]
                message_links.append(message_id)

        # Fetch each message's content
        messages = []
        for msg_id in message_links:
            email_data = fetch_email_by_message_id(msg_id)
            if email_data:
                messages.append(email_data)

        return messages
    except Exception as e:
        logger.error(
            f"Error fetching thread for patch {patch_id} ({message_id}): {str(e)}"
        )
        return []


def create_discussion_record(
    email_data: Dict[str, Any], patch_id: str
) -> Dict[str, Any]:
    """
    Create a discussion record from email data
    """
    now = datetime.utcnow().isoformat()
    message_id = email_data.get("message_id", "")
    thread_id = email_data.get("in_reply_to", message_id)

    # Use the message ID as the discussion ID for uniqueness
    discussion_id = message_id.replace("@", "-at-").replace(".", "-dot-")

    # Create DynamoDB item
    discussion_item = {
        # Primary key
        "id": discussion_id,
        # Sort key
        "timestamp": email_data.get("headers", {}).get("date", now),
        # Patch relationship
        "patchId": patch_id,
        # Metadata
        "authorName": email_data.get("author_name", "Unknown"),
        "authorEmail": email_data.get("author_email", ""),
        # Email threading
        "messageId": message_id,
        "inReplyTo": email_data.get("in_reply_to"),
        "threadId": thread_id,
        # Content
        "subject": email_data.get("subject", ""),
        "content": email_data.get("content", ""),
        # Analysis (defaults)
        "isReview": False,
        # GSI fields - for querying by patch
        "gsi1pk": f"PATCH#{patch_id}",
        "gsi1sk": f"DATE#{email_data.get('headers', {}).get('date', now)}",
        # GSI fields - for querying by thread
        "gsi2pk": f"THREAD#{thread_id}",
        "gsi2sk": f"DATE#{email_data.get('headers', {}).get('date', now)}",
        # GSI fields - for querying by author
        "gsi3pk": f"AUTHOR#{email_data.get('author_email', '')}",
        "gsi3sk": f"DATE#{email_data.get('headers', {}).get('date', now)}",
    }

    return discussion_item


def update_patch_discussion_count(patch_id: str, count: int) -> None:
    """
    Update the discussion count for a patch
    """
    try:
        patch_repository.update_discussion_count(patch_id, count)
    except Exception as e:
        logger.error(f"Error updating discussion count for patch {patch_id}: {str(e)}")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to fetch discussions for a patch
    """
    try:
        logger.info(
            f"Starting fetch discussions lambda at {datetime.utcnow().isoformat()}"
        )

        # Extract patch ID and message ID from the event
        patch_id = event.get("patch_id")
        message_id = event.get("message_id")

        if not patch_id or not message_id:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": "Missing required parameters: patch_id and message_id"}
                ),
            }

        # Fetch the thread for the patch
        messages = fetch_thread_for_patch(patch_id, message_id)
        logger.info(f"Retrieved {len(messages)} messages for patch {patch_id}")

        # Process and store discussions
        for email_data in messages:
            discussion_item = create_discussion_record(email_data, patch_id)

            # Store in DynamoDB using the repository
            discussion_repository.save_discussion(discussion_item)

        # Update the patch with the discussion count
        update_patch_discussion_count(patch_id, len(messages))

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Successfully processed {len(messages)} discussions for patch {patch_id}",
                    "count": len(messages),
                    "patch_id": patch_id,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")

        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error fetching discussions: {str(e)}"}),
        }
