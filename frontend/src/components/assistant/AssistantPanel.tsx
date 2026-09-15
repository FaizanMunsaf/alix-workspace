import { useState } from "react";
import type { DocumentVersion } from "../../api/documents";
import type { EditPatch } from "../../api/edits";
import type { EditorSelection } from "../editor/ContractEditor";
import { AskPanel } from "./AskPanel";
import { DiffPanel } from "./DiffPanel";
import { EditPanel } from "./EditPanel";

type Tab = "edit" | "ask" | "diff";

type Props = {
  documentId: string | null;
  versions: DocumentVersion[];
  selection: EditorSelection | null;
  getHtml: () => string;
  applyingId: string | null;
  onAcceptEdit: (patch: EditPatch) => Promise<void>;
};

export function AssistantPanel({
  documentId,
  versions,
  selection,
  getHtml,
  applyingId,
  onAcceptEdit,
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
          onAccept={onAcceptEdit}
        />
      )}
      {tab === "ask" && <AskPanel documentId={documentId} />}
      {tab === "diff" && <DiffPanel versions={versions} />}
    </aside>
  );
}
