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
    };
  }>;
};

export function askQuestion(query: string, documentId?: string) {
  return request<QAResponse>("/qa/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, document_id: documentId ?? null, top_k: 5 }),
  });
}
