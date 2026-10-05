import { useState } from "react";
import type { DocumentChange, DocumentMessage } from "../../api/history";
import type { DocumentVersion } from "../../api/documents";
import type { EditPatch } from "../../api/edits";
import type { EditorSelection } from "../editor/ContractEditor";
import { AskPanel } from "./AskPanel";
import { DiffPanel } from "./DiffPanel";
import { EditPanel } from "./EditPanel";
import { GroundedPanel } from "./GroundedPanel";
import { HistoryPanel } from "./HistoryPanel";

type Tab = "edit" | "ask" | "grounded" | "diff" | "history";

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
  onJumpToSource: (text: string) => boolean;
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
  onJumpToSource,
}: Props) {
  const [tab, setTab] = useState<Tab>("edit");
  const pending = changes.filter((change) => change.decision === "pending");

  return (
    <aside className="assistant">
      <div className="assistant-tabs">
        {(
          [
            ["edit", "Edit"],
            ["ask", "Ask"],
            ["grounded", "Grounded"],
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
          pending={pending}
          onAccept={onAcceptEdit}
          onReject={onRejectEdit}
          onProposed={onHistoryRefresh}
        />
      )}
      {tab === "ask" && (
        <AskPanel
          documentId={documentId}
          selection={selection}
          versions={versions}
          messages={messages}
          onAsked={onHistoryRefresh}
          onJumpToSource={onJumpToSource}
        />
      )}
      {tab === "grounded" && (
        <GroundedPanel
          documentId={documentId}
          getHtml={getHtml}
          applyingId={applyingId}
          pending={pending}
          onAccept={onAcceptEdit}
          onReject={onRejectEdit}
          onProposed={onHistoryRefresh}
          onJumpToSource={onJumpToSource}
        />
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
          applyingId={applyingId}
          restoringId={restoringId}
          onRestore={onRestore}
          onAccept={onAcceptEdit}
          onReject={onRejectEdit}
          onJumpToSource={onJumpToSource}
        />
      )}
    </aside>
  );
}
