# 1. Adopt Single-Table Design for DynamoDB

Date: 2023-04-27

## Status

Accepted

## Context

The LKML Assistant application needs to store and query several related data entities:
- Linux kernel mailing list discussions
- Patches and patch series
- Metadata about maintainers and subsystems
- User preferences and interaction history

We need to decide on a database design approach that will:
1. Provide consistent, predictable performance at scale
2. Support various access patterns (by discussion ID, by patch ID, by date range, etc.)
3. Be cost-effective as the dataset grows
4. Allow for efficient relationships between entities without complex joins
5. Fit well with our serverless architecture

DynamoDB has been selected as our primary datastore due to its seamless integration with AWS Lambda, scalability, and managed nature. However, DynamoDB has specific design considerations that differ from traditional relational databases.

## Decision

We will adopt a single-table design pattern for our DynamoDB implementation where all entity types will be stored in a single table with careful design of partition and sort keys.

Key aspects of this design:
1. Partition Key: We will use a composite key that includes entity type as a prefix (e.g., "DISCUSSION#12345", "PATCH#67890")
2. Sort Key: Will be designed to enable efficient querying for our primary access patterns
3. GSIs (Global Secondary Indexes): We will create 2-3 well-designed GSIs to support secondary access patterns
4. Entity relationships: Will be modeled using carefully designed key structures rather than joins

The single table will use this general schema pattern:
- PK: Entity identifier (e.g., "DISCUSSION#12345", "PATCH#67890")
- SK: Sort key designed for primary access patterns (e.g., "METADATA", "CREATED#2023-04-27", etc.)
- GSI1PK/GSI1SK: For querying by date ranges, status, or other secondary patterns
- GSI2PK/GSI2SK: For relationship queries (e.g., finding all patches in a discussion)
- Type: Entity type attribute for easier client-side filtering
- Entity-specific attributes as needed

## Consequences

### Positive
1. Simplified operations with only one table to manage and monitor
2. Reduced costs compared to multiple tables, particularly for provisioned capacity
3. Ability to fetch related items in a single query using key conditions
4. Flexible schema that can evolve with the application's needs
5. Efficient transaction support across entity types
6. Optimized for the most frequent access patterns identified in requirements

### Negative
1. More complex initial design process requiring careful planning of keys and indexes
2. Less intuitive data modeling compared to traditional relational approaches
3. Risk of hot partitions if key design is suboptimal
4. More complex queries for uncommon access patterns
5. Learning curve for developers more familiar with relational data modeling

### Mitigations
1. We will create comprehensive documentation of the data model and access patterns
2. Implement repository pattern to abstract DynamoDB complexity from application code
3. Create helper utilities for common query patterns
4. Establish load testing early to validate partition design
5. Implement monitoring for hot partitions and other DynamoDB performance metrics