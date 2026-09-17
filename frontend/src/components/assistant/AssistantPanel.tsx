import { useState } from "react";
import type { DocumentChange, DocumentMessage } from "../../api/history";
import type { DocumentVersion } from "../../api/documents";
import type { EditPatch } from "../../api/edits";
import type { EditorSelection } from "../editor/ContractEditor";
import { AskPanel } from "./AskPanel";
import { DiffPanel } from "./DiffPanel";
import { EditPanel } from "./EditPanel";
import { HistoryPanel } from "./HistoryPanel";

type Tab = "edit" | "ask" | "diff" | "history";

type Props = {
  documentId: string | null;
  versions: DocumentVersion[];
  changes: DocumentChange[];
  messages: DocumentMessage[];
  selection: EditorSelection | null;
  getHtml: () => string;
  applyingId: string | null;
  restoringId: string | null;
  onAcceptEdit: (patch: EditPatch) => Promise<void>;
  onRejectEdit: (patchId: string) => Promise<void>;
  onRestore: (versionId: string) => Promise<void>;
  onHistoryRefresh: () => Promise<void>;
};

export function AssistantPanel({
  documentId,
  versions,
  changes,
  messages,
  selection,
  getHtml,
  applyingId,
  restoringId,
  onAcceptEdit,
  onRejectEdit,
  onRestore,
  onHistoryRefresh,
}: Props) {
  const [tab, setTab] = useState<Tab>("edit");

  return (
    <aside className="assistant">
      <div className="assistant-tabs">
        {(
          [
            ["edit", "Edit"],
            ["ask", "Ask"],
            ["diff", "Diff"],
            ["history", "History"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? "active" : ""}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>
      {tab === "edit" && (
        <EditPanel
          documentId={documentId}
          selection={selection}
          getHtml={getHtml}
          applyingId={applyingId}
          pending={changes.filter((change) => change.decision === "pending")}
          onAccept={onAcceptEdit}
          onReject={onRejectEdit}
          onProposed={onHistoryRefresh}
        />
      )}
      {tab === "ask" && (
        <AskPanel documentId={documentId} messages={messages} onAsked={onHistoryRefresh} />
      )}
      {tab === "diff" && (
        <DiffPanel
          documentId={documentId}
          versions={versions}
          restoringId={restoringId}
          onRestore={onRestore}
        />
      )}
      {tab === "history" && (
        <HistoryPanel
          documentId={documentId}
          versions={versions}
          changes={changes}
          messages={messages}
          restoringId={restoringId}
          onRestore={onRestore}
        />
      )}
    </aside>
  );
}
