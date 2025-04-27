/**
 * Models representing the data as stored in DynamoDB
 */

import { PatchStatus } from './types';

/**
 * Represents a patch record in DynamoDB
 */
export interface PatchDbRecord {
  // Primary key
  id: string;
  
  // Metadata
  name: string;
  submitterId: string;
  submitterName: string;
  submitterEmail: string;
  submittedAt: string;
  lastUpdatedAt: string;
  status: PatchStatus;
  
  // URLs
  url: string;
  webUrl: string;
  mboxUrl: string;
  
  // Email threading
  messageId: string;
  
  // Content references
  commitRef?: string;
  pullUrl?: string;
  hash?: string;
  content: string;
  
  // Analysis
  summary?: string;
  tags?: string[];
  reviewScore?: number;
  
  // Series info
  seriesId?: string;
  seriesName?: string;
  seriesVersion?: number;
  seriesPosition?: number;
  
  // Tracking
  discussionCount: number;
  lastDiscussionAt?: string;
  
  // GSI fields
  gsi1pk?: string; // For querying by submitter - "SUBMITTER#<submitterId>"
  gsi1sk?: string; // Submitted date - "DATE#<ISO date>"
  
  gsi2pk?: string; // For querying by series - "SERIES#<seriesId>"
  gsi2sk?: string; // Series position or version - "POS#<position>" or "DATE#<ISO date>"
  
  gsi3pk?: string; // For querying by status - "STATUS#<status>"
  gsi3sk?: string; // Last updated date - "DATE#<ISO date>"
}

/**
 * Represents a discussion record in DynamoDB
 */
export interface DiscussionDbRecord {
  // Primary key
  id: string;
  
  // Sort key
  timestamp: string;
  
  // Patch relationship
  patchId: string;
  
  // Author info (denormalized)
  authorName: string;
  authorEmail: string;
  
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
  reviewType?: string;
  
  // Code references (if any)
  codeReferences?: string;
  
  // GSI fields
  gsi1pk?: string; // For querying by patch - "PATCH#<patchId>"
  gsi1sk?: string; // Timestamp - "DATE#<ISO date>"
  
  gsi2pk?: string; // For querying by thread - "THREAD#<threadId>"
  gsi2sk?: string; // Timestamp - "DATE#<ISO date>"
  
  gsi3pk?: string; // For querying by author - "AUTHOR#<authorEmail>"
  gsi3sk?: string; // Timestamp - "DATE#<ISO date>"
}

/**
 * Maps between API data and database records
 */
export class DatabaseMapper {
  /**
   * Creates a PatchDbRecord from an API Patch object
   */
  static createPatchRecord(patch: any): PatchDbRecord {
    const now = new Date().toISOString();
    
    return {
      id: patch.id.toString(),
      name: patch.name,
      submitterId: patch.submitter.id.toString(),
      submitterName: patch.submitter.name,
      submitterEmail: patch.submitter.email,
      submittedAt: patch.date,
      lastUpdatedAt: now,
      status: PatchStatus.NEW,
      url: patch.url,
      webUrl: patch.web_url,
      mboxUrl: patch.mbox,
      messageId: patch.msgid,
      commitRef: patch.commit_ref || undefined,
      pullUrl: patch.pull_url || undefined,
      hash: patch.hash,
      content: patch.content,
      discussionCount: 0,
      
      // GSI fields
      gsi1pk: `SUBMITTER#${patch.submitter.id}`,
      gsi1sk: `DATE#${patch.date}`,
      gsi3pk: `STATUS#${PatchStatus.NEW}`,
      gsi3sk: `DATE#${patch.date}`
    };
  }
  
  /**
   * Creates a DiscussionDbRecord from an API discussion object
   */
  static createDiscussionRecord(discussion: any, patchId: string): DiscussionDbRecord {
    const timestamp = new Date().toISOString();
    
    return {
      id: discussion.id,
      timestamp,
      patchId,
      authorName: discussion.author.name,
      authorEmail: discussion.author.email,
      messageId: discussion.message_id,
      inReplyTo: discussion.in_reply_to,
      threadId: discussion.thread_id || discussion.message_id,
      subject: discussion.subject,
      content: discussion.content,
      isReview: false,
      
      // GSI fields
      gsi1pk: `PATCH#${patchId}`,
      gsi1sk: `DATE#${timestamp}`,
      gsi2pk: `THREAD#${discussion.thread_id || discussion.message_id}`,
      gsi2sk: `DATE#${timestamp}`,
      gsi3pk: `AUTHOR#${discussion.author.email}`,
      gsi3sk: `DATE#${timestamp}`
    };
  }
}