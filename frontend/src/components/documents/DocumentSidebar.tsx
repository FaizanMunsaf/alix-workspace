import { useState } from "react";
import type { DocumentListItem } from "../../api/documents";

type Props = {
  documents: DocumentListItem[];
  selectedId: string | null;
  loading: boolean;
  error: string | null;
  onSelect: (documentId: string) => void;
  onUpload: (file: File) => Promise<void>;
};

export function DocumentSidebar({
  documents,
  selectedId,
  loading,
  error,
  onSelect,
  onUpload,
}: Props) {
  const [uploading, setUploading] = useState(false);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    try {
      await onUpload(file);
    } finally {
      setUploading(false);
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <h2>Documents</h2>
        <label className="upload-button">
          {uploading ? "Uploading…" : "Upload .docx"}
          <input
            type="file"
            accept=".docx"
            hidden
            disabled={uploading}
            onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              void handleFile(file);
            }}
          />
        </label>
        <p className="hint">Stored contracts stay here. Open one to keep editing.</p>
        {error && <p className="error-text">{error}</p>}
      </div>
      <ul className="document-list">
        {loading && documents.length === 0 && <li className="muted">Loading…</li>}
        {!loading && documents.length === 0 && (
          <li className="muted">No documents yet.</li>
        )}
        {documents.map((doc) => (
          <li key={doc.document_id}>
            <button
              type="button"
              className={doc.document_id === selectedId ? "active" : ""}
              onClick={() => onSelect(doc.document_id)}
            >
              <span className="doc-title">{doc.title}</span>
              <span className={`status status-${doc.processing_status}`}>
                {doc.processing_status}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
