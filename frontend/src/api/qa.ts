import { request } from "./client";

export type QAResponse = {
  query: string;
  answer: string;
  sources: Array<{
    content: string;
    metadata: {
      document_id?: string;
      version_id?: string;
      ast_node_id?: string;
      clause_category?: string;
      distance?: number;
      label?: string;
    };
  }>;
};

export function askQuestion(
  query: string,
  documentId?: string,
  selection?: string | null,
) {
  return request<QAResponse>("/qa/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      document_id: documentId ?? null,
      selection: selection?.trim() ? selection.trim() : null,
      top_k: 12,
    }),
  });
}
