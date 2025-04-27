# Data Models

This document details the data models used in the LKML Assistant application.

## Domain Models

### Patch

Represents a patch submitted to the Linux kernel mailing list:

```typescript
interface Patch {
  id: string;              // Unique identifier (from Patchwork)
  submitterId: string;     // ID of the person who submitted the patch
  submitterName: string;   // Name of the submitter
  submitterEmail: string;  // Email of the submitter
  subject: string;         // Patch subject/title
  date: string;            // Submission date (ISO format)
  messageId: string;       // Email Message-ID
  url: string;             // URL to the patch on Patchwork
  state: PatchState;       // Current state of the patch
  project: string;         // Project (e.g., "Rust for Linux")
  series: {                // Series information
    id: string;            // Series ID
    name: string;          // Series name
    version: number;       // Version of the series
    partIndex: number;     // Position of patch in series
    totalParts: number;    // Total patches in series
  } | null;
  tags: string[];          // Associated tags
  coverLetter: string | null; // ID of the cover letter if part of a series
  content: string;         // The actual patch content
  isRustRelated: boolean;  // Indicates if the patch is Rust-related
  lastUpdated: string;     // When the record was last updated
}

enum PatchState {
  NEW = "new",
  UNDER_REVIEW = "under-review",
  ACCEPTED = "accepted",
  REJECTED = "rejected",
  RFC = "rfc",
  NOT_APPLICABLE = "not-applicable",
  SUPERSEDED = "superseded",
  AWAITING_UPSTREAM = "awaiting-upstream",
  DEFERRED = "deferred"
}
```

### Discussion

Represents a discussion thread related to a patch:

```typescript
interface Discussion {
  id: string;                // Unique identifier (messageId)
  patchId: string;           // ID of the related patch
  parentId: string | null;   // ID of the parent message in thread
  authorName: string;        // Name of the author
  authorEmail: string;       // Email of the author
  subject: string;           // Subject/title of the message
  date: string;              // Date the message was sent (ISO format)
  messageId: string;         // Email Message-ID
  inReplyTo: string | null;  // Message-ID this is a reply to
  content: string;           // Message content
  references: string[];      // Message-IDs referenced by this message
  isRustReviewer: boolean;   // If author is a Rust subsystem reviewer
  tags: DiscussionTag[];     // Tags/classifications of the message
  lastUpdated: string;       // When the record was last updated
}

enum DiscussionTag {
  QUESTION = "question",
  ISSUE = "issue",
  APPROVAL = "approval",
  SUGGESTION = "suggestion",
  ADDRESSED = "addressed",
  ACKNOWLEDGEMENT = "acknowledgement",
  TECHNICAL_DISCUSSION = "technical-discussion"
}
```

### Series

Represents a series of related patches:

```typescript
interface Series {
  id: string;              // Unique identifier
  name: string;            // Series name
  submitterId: string;     // ID of the person who submitted the series
  submitterName: string;   // Name of the submitter
  date: string;            // Submission date (ISO format)
  version: number;         // Series version
  coverLetterMessageId: string | null; // Message-ID of cover letter
  coverLetterContent: string | null;   // Content of cover letter
  patchCount: number;      // Total number of patches in series
  patches: string[];       // Array of patch IDs in this series
  isComplete: boolean;     // Whether all patches are present
  lastUpdated: string;     // When the record was last updated
}
```

### Person

Represents individuals involved in the kernel development:

```typescript
interface Person {
  id: string;              // Unique identifier
  name: string;            // Full name
  email: string;           // Email address
  isRustReviewer: boolean; // Whether they're a Rust subsystem reviewer
  activity: {              // Activity statistics
    patchesSubmitted: number;
    reviews: number;
    commentsTotal: number;
  };
  lastUpdated: string;     // When the record was last updated
}
```

## Database Models

### DynamoDB Table Design

The application uses DynamoDB with a Single-Table Design pattern:

#### Patches Table

| Attribute | Type | Description |
|-----------|------|-------------|
| PK | String | Primary Key - "PATCH#<id>" |
| SK | String | Sort Key - "#METADATA" |
| id | String | Patch ID |
| submitterId | String | Submitter ID |
| submitterName | String | Submitter name |
| submitterEmail | String | Submitter email |
| subject | String | Patch subject |
| date | String | Submission date |
| messageId | String | Email Message-ID |
| url | String | URL to patch |
| state | String | Current state |
| project | String | Project name |
| series | Map | Series information |
| tags | List | Associated tags |
| coverLetter | String | Cover letter ID |
| content | String | Patch content |
| isRustRelated | Boolean | If Rust-related |
| lastUpdated | String | Last update timestamp |
| GSI1PK | String | "DATE" (for date-based queries) |
| GSI1SK | String | Date in ISO format |
| GSI2PK | String | "SERIES#<seriesId>" (for series queries) |
| GSI2SK | String | "PATCH#<partIndex>" |
| GSI3PK | String | "MESSAGE#<messageId>" (for message-ID lookup) |
| GSI3SK | String | "#METADATA" |

#### Discussions Table

| Attribute | Type | Description |
|-----------|------|-------------|
| PK | String | Primary Key - "PATCH#<patchId>" |
| SK | String | Sort Key - "DISCUSSION#<id>" |
| id | String | Discussion ID |
| patchId | String | Related patch ID |
| parentId | String | Parent message ID |
| authorName | String | Author name |
| authorEmail | String | Author email |
| subject | String | Message subject |
| date | String | Message date |
| messageId | String | Email Message-ID |
| inReplyTo | String | In-reply-to field |
| content | String | Message content |
| references | List | Referenced message IDs |
| isRustReviewer | Boolean | If from Rust reviewer |
| tags | List | Message tags |
| lastUpdated | String | Last update timestamp |
| GSI1PK | String | "DATE" (for date-based queries) |
| GSI1SK | String | Date in ISO format |
| GSI2PK | String | "AUTHOR#<authorEmail>" (for author queries) |
| GSI2SK | String | "DISCUSSION#<id>" |
| GSI3PK | String | "MESSAGE#<messageId>" (for message-ID lookup) |
| GSI3SK | String | "#METADATA" |

## API Response Models

### Patchwork API Response

```typescript
interface PatchworkResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PatchworkPatch[];
}

interface PatchworkPatch {
  id: number;
  url: string;
  web_url: string;
  project: {
    id: number;
    name: string;
    linkname: string;
  };
  state: string;
  date: string;
  name: string;
  submitter: {
    id: number;
    url: string;
    name: string;
    email: string;
  };
  mbox: string;
  series: {
    id: number;
    name: string;
    version: number;
  }[];
  delegate: {
    id: number;
    username: string;
    email: string;
  } | null;
  archived: boolean;
  msgid: string;
  list_archive_url: string;
  // Additional fields...
}
```

### Lore.kernel.org Response

```typescript
interface LoreResponse {
  messages: LoreMessage[];
  threadRootId: string;
}

interface LoreMessage {
  id: string;
  from: string;
  date: string;
  subject: string;
  messageId: string;
  inReplyTo: string | null;
  references: string[];
  body: string;
  // Additional fields...
}
```

## Data Transformations

The application transforms between API responses and domain models:

1. **API Response → Domain Model**: 
   - External API data is mapped to internal domain models
   - Additional fields are calculated or inferred

2. **Domain Model → Database Model**:
   - Domain models are transformed to fit DynamoDB's data structure
   - Keys and indexes are generated appropriately

3. **Database Model → Domain Model**:
   - Database records are transformed back to domain models
   - Relationship data might be assembled from multiple records

## Data Access Patterns

The data models are optimized for these access patterns:

1. Get a patch by ID
2. Get all discussions for a patch
3. Get patches by submission date (newest first)
4. Get all patches in a series
5. Search for patches with specific tags
6. Get discussions by author
7. Get a patch or discussion by message ID
8. Get all patches by a specific submitter