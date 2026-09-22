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
import {
  acceptChange,
  listChanges,
  listMessages,
  rejectChange,
  restoreVersion,
  type DocumentChange,
  type DocumentMessage,
} from "../api/history";
import { type EditPatch } from "../api/edits";

export function WorkspacePage() {
  const editorRef = useRef<ContractEditorHandle>(null);
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [selected, setSelected] = useState<DocumentDetail | null>(null);
  const [changes, setChanges] = useState<DocumentChange[]>([]);
  const [messages, setMessages] = useState<DocumentMessage[]>([]);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [selection, setSelection] = useState<EditorSelection | null>(null);
  const [contentNonce, setContentNonce] = useState(0);
  const [applyingId, setApplyingId] = useState<string | null>(null);
  const [restoringId, setRestoringId] = useState<string | null>(null);

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

  const refreshHistory = useCallback(async (documentId: string) => {
    const [nextChanges, nextMessages] = await Promise.all([
      listChanges(documentId),
      listMessages(documentId),
    ]);
    setChanges(nextChanges);
    setMessages(nextMessages);
  }, []);

  const openDocument = useCallback(
    async (documentId: string) => {
      const detail = await getDocument(documentId);
      setSelected(detail);
      setChanges([]);
      setMessages([]);
      setDirty(false);
      setSelection(null);
      setContentNonce((value) => value + 1);
      await refreshHistory(documentId).catch(() => {
        setChanges([]);
        setMessages([]);
      });
      return detail;
    },
    [refreshHistory],
  );

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
      await refreshHistory(saved.document_id);
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
      const result = await acceptChange(selected.document_id, patch.id, html);
      setSelected({
        ...selected,
        html: result.html,
        active_version_id: result.active_version_id,
        versions: result.versions.length ? result.versions : selected.versions,
      });
      setContentNonce((value) => value + 1);
      setDirty(false);
      await refreshList();
      await refreshHistory(selected.document_id);
    } finally {
      setApplyingId(null);
    }
  }

  async function handleRejectEdit(patchId: string) {
    if (!selected) throw new Error("Open a document first.");
    await rejectChange(selected.document_id, patchId);
    await refreshHistory(selected.document_id);
  }

  async function handleRestore(versionId: string) {
    if (!selected) return;
    setRestoringId(versionId);
    setActionError(null);
    try {
      const saved = await restoreVersion(selected.document_id, versionId);
      setSelected(saved);
      setContentNonce((value) => value + 1);
      setDirty(false);
      await refreshList();
      await refreshHistory(saved.document_id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Restore failed.");
    } finally {
      setRestoringId(null);
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
            {selected?.versions.length
              ? ` · v${selected.versions.at(-1)?.version_number ?? 1}`
              : ""}
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
          changes={changes}
          messages={messages}
          selection={selection}
          getHtml={() => editorRef.current?.getHTML() || selected?.html || ""}
          applyingId={applyingId}
          restoringId={restoringId}
          onAcceptEdit={handleAcceptEdit}
          onRejectEdit={handleRejectEdit}
          onRestore={handleRestore}
          onHistoryRefresh={async () => {
            if (selected) await refreshHistory(selected.document_id);
          }}
          onJumpToSource={(text) => editorRef.current?.jumpToText(text) ?? false}
        />
      </main>
    </div>
  );
}
