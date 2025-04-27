/**
 * Represents a patch from the Patchwork API
 */
export interface Patch {
  id: string;
  name: string;
  submitter: string;
  submittedAt: string;
  status: PatchStatus;
  url: string;
  messageId: string;
  summary?: string;
  series?: string;
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
  RFC = 'RFC'
}

/**
 * Represents a discussion related to a patch
 */
export interface Discussion {
  id: string;
  patchId: string;
  author: string;
  timestamp: string;
  messageId: string;
  inReplyTo?: string;
  content: string;
  summary?: string;
}