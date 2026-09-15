import { useCallback, useEffect, useRef, useState } from "react";
import { AssistantPanel } from "../components/assistant/AssistantPanel";
import { DocumentSidebar } from "../components/documents/DocumentSidebar";
import {
  ContractEditor,
  type ContractEditorHandle,
  type EditorSelection,
} from "../components/editor/ContractEditor";
import {
  exportDocument,
  getDocument,
  listDocuments,
  saveDocumentContent,
  uploadDocument,
  type DocumentDetail,
  type DocumentListItem,
} from "../api/documents";
import { applyEdit, type EditPatch } from "../api/edits";

export function WorkspacePage() {
  const editorRef = useRef<ContractEditorHandle>(null);
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [selected, setSelected] = useState<DocumentDetail | null>(null);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [selection, setSelection] = useState<EditorSelection | null>(null);
  const [contentNonce, setContentNonce] = useState(0);
  const [applyingId, setApplyingId] = useState<string | null>(null);

  const refreshList = useCallback(async () => {
    try {
      setDocuments(await listDocuments());
      setListError(null);
    } catch (err) {
      setListError(err instanceof Error ? err.message : "Could not load documents.");
    } finally {
      setListLoading(false);
    }
  }, []);

  const openDocument = useCallback(async (documentId: string) => {
    const detail = await getDocument(documentId);
    setSelected(detail);
    setDirty(false);
    setSelection(null);
    setContentNonce((value) => value + 1);
    return detail;
  }, []);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  const processing = selected?.versions.at(-1)?.processing_status ?? selected?.status ?? null;
  const isProcessing = processing === "pending" || processing === "processing";

  useEffect(() => {
    if (!selected || !isProcessing) return;
    const timer = window.setInterval(() => {
      void openDocument(selected.document_id).then(() => void refreshList());
    }, 2000);
    return () => window.clearInterval(timer);
  }, [selected, isProcessing, openDocument, refreshList]);

  async function handleUpload(file: File) {
    setActionError(null);
    try {
      const uploaded = await uploadDocument(file);
      await refreshList();
      await openDocument(uploaded.document_id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Upload failed.");
    }
  }

  async function handleSave() {
    if (!selected) return;
    const html = editorRef.current?.getHTML();
    if (!html) return;
    setBusy("Saving…");
    setActionError(null);
    try {
      const saved = await saveDocumentContent(
        selected.document_id,
        html,
        selected.active_version_id ?? undefined,
      );
      setSelected(saved);
      setDirty(false);
      await refreshList();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleExport() {
    if (!selected) return;
    setBusy("Exporting…");
    setActionError(null);
    try {
      await exportDocument(selected.document_id, selected.title);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleAcceptEdit(patch: EditPatch) {
    if (!selected) throw new Error("Open a document first.");
    setApplyingId(patch.id);
    setActionError(null);
    try {
      const html = editorRef.current?.getHTML() || selected.html || "";
      const result = await applyEdit(selected.document_id, {
        before: patch.before,
        after: patch.after,
        html,
        version_id: selected.active_version_id,
      });
      setSelected({ ...selected, html: result.html });
      setContentNonce((value) => value + 1);
      setDirty(false);
      await refreshList();
    } finally {
      setApplyingId(null);
    }
  }

  const canEdit = Boolean(selected) && !isProcessing && processing !== "failed";

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Alix</h1>
          <p className="header-sub">
            {selected ? selected.title : "Contract workspace"}
            {dirty ? " · unsaved" : ""}
          </p>
        </div>
        <div className="header-actions">
          <button type="button" disabled={!canEdit || Boolean(busy)} onClick={() => void handleSave()}>
            {busy === "Saving…" ? "Saving…" : "Save"}
          </button>
          <button type="button" disabled={!canEdit || Boolean(busy)} onClick={() => void handleExport()}>
            {busy === "Exporting…" ? "Exporting…" : "Export .docx"}
          </button>
        </div>
      </header>
      {actionError && <div className="banner-error">{actionError}</div>}
      <main className="workspace">
        <DocumentSidebar
          documents={documents}
          selectedId={selected?.document_id ?? null}
          loading={listLoading}
          error={listError}
          onSelect={(documentId) => {
            setActionError(null);
            void openDocument(documentId).catch((err) => {
              setActionError(err instanceof Error ? err.message : "Could not open document.");
            });
          }}
          onUpload={handleUpload}
        />
        <section className="canvas">
          <ContractEditor
            ref={editorRef}
            documentId={selected?.document_id ?? null}
            html={selected?.html ?? ""}
            processingStatus={processing}
            contentNonce={contentNonce}
            editable={canEdit}
            onDirty={() => setDirty(true)}
            onSelectionChange={setSelection}
          />
        </section>
        <AssistantPanel
          documentId={selected?.document_id ?? null}
          versions={selected?.versions ?? []}
          selection={selection}
          getHtml={() => editorRef.current?.getHTML() || selected?.html || ""}
          applyingId={applyingId}
          onAcceptEdit={handleAcceptEdit}
        />
      </main>
    </div>
  );
}
