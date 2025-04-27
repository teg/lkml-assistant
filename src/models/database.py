"""
Database models for DynamoDB
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PatchDbRecord:
    """Represents a patch record in DynamoDB"""

    pk: str  # Primary key - format: PATCH#{id}
    sk: str  # Sort key - format: #METADATA
    id: str  # Patch ID
    submitter_id: str  # Submitter ID
    submitter_name: str  # Submitter name
    submitter_email: str  # Submitter email
    subject: str  # Patch subject
    date: str  # Submission date (ISO format)
    message_id: str  # Email Message-ID
    url: str  # URL to patch
    state: str  # Current state
    project: str  # Project name
    series: Dict  # Series information
    tags: List[str]  # Associated tags
    cover_letter: Optional[str]  # Cover letter ID
    content: str  # Patch content
    is_rust_related: bool  # If Rust-related
    last_updated: str  # Last update timestamp
    gsi1pk: Optional[str] = None  # GSI1 partition key
    gsi1sk: Optional[str] = None  # GSI1 sort key
    gsi2pk: Optional[str] = None  # GSI2 partition key
    gsi2sk: Optional[str] = None  # GSI2 sort key
    gsi3pk: Optional[str] = None  # GSI3 partition key
    gsi3sk: Optional[str] = None  # GSI3 sort key


@dataclass
class DiscussionDbRecord:
    """Represents a discussion record in DynamoDB"""

    pk: str  # Primary key - format: PATCH#{patchId}
    sk: str  # Sort key - format: DISCUSSION#{id}
    id: str  # Discussion ID
    patch_id: str  # Related patch ID
    parent_id: Optional[str]  # Parent message ID
    author_name: str  # Author name
    author_email: str  # Author email
    subject: str  # Message subject
    date: str  # Message date (ISO format)
    message_id: str  # Email Message-ID
    in_reply_to: Optional[str]  # In-reply-to field
    content: str  # Message content
    references: List[str]  # Referenced message IDs
    is_rust_reviewer: bool  # If from Rust reviewer
    tags: List[str]  # Message tags
    last_updated: str  # Last update timestamp
    gsi1pk: Optional[str] = None  # GSI1 partition key
    gsi1sk: Optional[str] = None  # GSI1 sort key
    gsi2pk: Optional[str] = None  # GSI2 partition key
    gsi2sk: Optional[str] = None  # GSI2 sort key
    gsi3pk: Optional[str] = None  # GSI3 partition key
    gsi3sk: Optional[str] = None  # GSI3 sort key
