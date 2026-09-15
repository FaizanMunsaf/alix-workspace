import { request } from "./client";

export type EditScope = "selection" | "document";

export type EditPatch = {
  id: string;
  target: string;
  before: string;
  after: string;
  rationale: string;
  status: "pending";
};

export type ProposeEditResponse = {
  document_id: string;
  scope: EditScope;
  instruction: string;
  plan: string[];
  patches: EditPatch[];
};

export type ApplyEditResponse = {
  document_id: string;
  html: string;
  before: string;
  after: string;
};

export function proposeEdits(
  documentId: string,
  body: {
    instruction: string;
    selection_text?: string | null;
    html?: string | null;
    scope: EditScope;
  },
) {
  return request<ProposeEditResponse>(`/documents/${documentId}/edits/propose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function applyEdit(
  documentId: string,
  body: { before: string; after: string; html?: string | null; version_id?: string | null },
) {
  return request<ApplyEditResponse>(`/documents/${documentId}/edits/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
