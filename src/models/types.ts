/**
 * Represents a patch in our system (transformed from Patchwork API)
 */
export interface Patch {
  // Primary key for DynamoDB
  id: string;
  
  // Metadata fields
  name: string;
  submitter: {
    id: string;
    name: string;
    email: string;
  };
  submittedAt: string;
  lastUpdatedAt: string;
  status: PatchStatus;
  
  // URL references
  url: string;
  webUrl: string;
  mboxUrl: string;
  
  // Email threading
  messageId: string;
  
  // Content
  commitRef?: string;
  pullUrl?: string;
  hash?: string;
  content: string;
  
  // Analysis
  summary?: string;
  tags?: string[];
  reviewScore?: number;
  
  // Series information
  series?: {
    id: string;
    name: string;
    version: number;
    position?: number;
  };
  
  // Tracking
  discussionCount: number;
  lastDiscussionAt?: string;
}

/**
 * Possible statuses for a patch
 */
export enum PatchStatus {
  NEW = 'NEW',
  UNDER_REVIEW = 'UNDER_REVIEW',
  ACCEPTED = 'ACCEPTED',
  REJECTED = 'REJECTED',
  SUPERSEDED = 'SUPERSEDED',
  RFC = 'RFC',
  CHANGES_REQUESTED = 'CHANGES_REQUESTED',
  AWAITING_UPSTREAM = 'AWAITING_UPSTREAM'
}

/**
 * Represents a discussion related to a patch
 */
export interface Discussion {
  // Primary key for DynamoDB
  id: string;
  
  // Sort key for DynamoDB
  timestamp: string;
  
  // Patch relationship
  patchId: string;
  
  // Metadata
  author: {
    name: string;
    email: string;
  };
  
  // Email threading
  messageId: string;
  inReplyTo?: string;
  threadId: string;
  
  // Content
  subject: string;
  content: string;
  
  // Analysis
  sentiment?: 'positive' | 'negative' | 'neutral';
  summary?: string;
  isReview: boolean;
  reviewScore?: number;
  reviewType?: 'acked-by' | 'reviewed-by' | 'tested-by' | 'comment';
  
  // References
  codeReferences?: {
    file: string;
    line: number;
    content: string;
  }[];
}

/**
 * Represents a tag applied to patches
 */
export interface Tag {
  id: string;
  name: string;
  color: string;
  description?: string;
}

/**
 * Represents a person (maintainer, contributor)
 */
export interface Person {
  id: string;
  name: string;
  email: string;
  role?: 'maintainer' | 'contributor' | 'reviewer';
  activity?: {
    patchCount: number;
    commentCount: number;
    lastActive: string;
  };
}