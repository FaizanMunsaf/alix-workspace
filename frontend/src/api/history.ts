import { request } from "./client";
import type { DocumentDetail, DocumentVersion } from "./documents";

export type ChangeDecision = "pending" | "accepted" | "rejected";

export type DocumentChange = {
  id: string;
  document_id: string;
  version_id: string | null;
  result_version_id: string | null;
  actor: "user" | "ai" | string;
  instruction: string | null;
  target: string;
  before: string;
  after: string;
  rationale: string | null;
  decision: ChangeDecision;
  created_at: string;
  decided_at: string | null;
};

export type DocumentMessage = {
  id: string;
  document_id: string;
  role: "user" | "assistant" | string;
  content: string;
  created_at: string;
};

export type ApplyChangeResponse = {
  document_id: string;
  html: string;
  before: string;
  after: string;
  active_version_id: string | null;
  versions: DocumentVersion[];
};

export function listChanges(documentId: string) {
  return request<DocumentChange[]>(`/documents/${documentId}/changes`);
}

export function listMessages(documentId: string) {
  return request<DocumentMessage[]>(`/documents/${documentId}/messages`);
}

export function rejectChange(documentId: string, changeId: string) {
  return request<DocumentChange>(`/documents/${documentId}/changes/${changeId}/reject`, {
    method: "POST",
  });
}

export function acceptChange(documentId: string, changeId: string, html?: string | null) {
  return request<ApplyChangeResponse>(
    `/documents/${documentId}/changes/${changeId}/accept`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ html: html ?? null }),
    },
  );
}

export function restoreVersion(documentId: string, versionId: string) {
  return request<DocumentDetail>(`/documents/${documentId}/restore`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ version_id: versionId }),
  });
}
