import { request } from "./client";
import type { EditPatch } from "./edits";

export type SourceLayer = "playbook" | "public_ref";

export type KnowledgeSource = {
  id: string;
  title: string;
  source_layer: SourceLayer;
  description: string | null;
  chunk_count: number;
  created_at: string;
};

export type GroundedCitation = {
  layer: "contract" | "playbook" | "public_ref";
  label: string;
  title: string | null;
  content: string;
};

export type GroundedReviewResponse = {
  document_id: string;
  instruction: string;
  plan: string[];
  deviations: string[];
  patches: EditPatch[];
  citations: GroundedCitation[];
};

export function listKnowledgeSources() {
  return request<KnowledgeSource[]>("/knowledge/");
}

export function seedKnowledge(force = false) {
  return request<{ seeded: boolean; sources: number; chunks?: number; message: string }>(
    `/knowledge/seed?force=${force ? "true" : "false"}`,
    { method: "POST" },
  );
}

export function groundedReview(
  documentId: string,
  body: {
    html?: string | null;
    instruction?: string | null;
    include_public?: boolean;
  } = {},
) {
  return request<GroundedReviewResponse>(`/documents/${documentId}/grounded/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      html: body.html ?? null,
      instruction: body.instruction ?? null,
      include_public: body.include_public ?? true,
    }),
  });
}
