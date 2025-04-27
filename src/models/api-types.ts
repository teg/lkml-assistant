/**
 * Types representing the Patchwork API responses
 * Based on https://patchwork.kernel.org/api/1.1/
 */

export interface PatchworkPerson {
  id: number;
  url: string;
  name: string;
  email: string;
}

export interface PatchworkProject {
  id: number;
  url: string;
  name: string;
  link_name: string;
  list_id: string;
  list_email: string;
  web_url: string;
  scm_url: string;
  webscm_url: string;
}

export interface PatchworkSeries {
  id: number;
  url: string;
  name: string;
  date: string;
  version: number;
  mbox: string;
}

export interface PatchworkPatch {
  id: number;
  url: string;
  web_url: string;
  msgid: string;
  date: string;
  name: string;
  commit_ref: string | null;
  pull_url: string | null;
  state: string;
  archived: boolean;
  hash: string;
  submitter: PatchworkPerson;
  delegate: PatchworkPerson | null;
  mbox: string;
  series: PatchworkSeries[];
  content: string;
  headers: Record<string, string>;
  project: PatchworkProject;
}

export interface PatchworkListResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}