import { API_BASE, request } from "./client";

export type ProcessingStatus = "pending" | "processing" | "completed" | "failed" | string;

export type DocumentListItem = {
  document_id: string;
  version_id: string | null;
  title: string;
  status: string;
  processing_status: ProcessingStatus;
  version_number: number;
  created_at: string;
};

export type DocumentVersion = {
  id: string;
  document_id: string;
  version_number: number;
  raw_text: string | null;
  file_path: string | null;
  processing_status: ProcessingStatus;
  ast_json: { nodes?: unknown[]; html?: string } | null;
  html: string | null;
  created_at: string;
};

export type DocumentDetail = {
  document_id: string;
  title: string;
  status: string;
  document_type: string;
  html: string | null;
  active_version_id: string | null;
  versions: DocumentVersion[];
};

export type UploadResponse = {
  document_id: string;
  version_id: string;
  title: string;
  status: string;
  processing_status: ProcessingStatus;
  message: string;
  filename: string;
};

export function listDocuments() {
  return request<DocumentListItem[]>("/documents/");
}

export function getDocument(documentId: string) {
  return request<DocumentDetail>(`/documents/${documentId}`);
}

export function uploadDocument(file: File, title?: string) {
  const body = new FormData();
  body.append("file", file);
  if (title) body.append("title", title);
  return request<UploadResponse>("/documents/upload", { method: "POST", body });
}

export function saveDocumentContent(documentId: string, html: string, versionId?: string) {
  return request<DocumentDetail>(`/documents/${documentId}/content`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ html, version_id: versionId ?? null }),
  });
}

export async function exportDocument(documentId: string, filename: string) {
  const response = await fetch(`${API_BASE}/documents/${documentId}/export`);
  if (!response.ok) {
    throw new Error("Export failed.");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.endsWith(".docx") ? filename : `${filename}.docx`;
  link.click();
  URL.revokeObjectURL(url);
}
