import type { DocumentChange, DocumentMessage } from "../../api/history";
import type { DocumentVersion } from "../../api/documents";

type Props = {
  documentId: string | null;
  versions: DocumentVersion[];
  changes: DocumentChange[];
  messages: DocumentMessage[];
  restoringId: string | null;
  onRestore: (versionId: string) => Promise<void>;
};

function formatWhen(value: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function HistoryPanel({
  documentId,
  versions,
  changes,
  messages,
  restoringId,
  onRestore,
}: Props) {
  if (!documentId) {
    return (
      <div className="assistant-body">
        <p className="hint">Open a contract to see checkpoints, redlines, and conversation history.</p>
      </div>
    );
  }

  const latestId = versions.at(-1)?.id;

  return (
    <div className="assistant-body">
      <p className="hint">
        Saves and accepted AI edits create a new version. Restore copies an older
        checkpoint forward; it does not delete history.
      </p>

      <h3 className="history-heading">Versions</h3>
      {versions.length === 0 && <p className="hint">No versions yet.</p>}
      {versions.map((version) => (
        <article key={version.id} className="history-item">
          <p className="patch-target">
            Version {version.version_number}
            {version.id === latestId ? " · current" : ""}
          </p>
          <p className="history-meta">{formatWhen(version.created_at)}</p>
          {version.id !== latestId && (
            <div className="patch-actions">
              <button
                type="button"
                disabled={Boolean(restoringId)}
                onClick={() => void onRestore(version.id)}
              >
                {restoringId === version.id ? "Restoring…" : "Restore"}
              </button>
            </div>
          )}
        </article>
      ))}

      <h3 className="history-heading">Changes</h3>
      {changes.length === 0 && <p className="hint">No redlines or saves recorded yet.</p>}
      {changes.map((change) => (
        <article key={change.id} className="history-item">
          <p className="patch-target">
            {change.actor === "ai" ? "AI" : "User"} · {change.target} · {change.decision}
          </p>
          {change.instruction && <p className="hint">{change.instruction}</p>}
          <p className="history-meta">
            {formatWhen(change.created_at)}
            {change.decided_at ? ` · decided ${formatWhen(change.decided_at)}` : ""}
          </p>
          {change.before && <p className="diff-deleted">{change.before}</p>}
          {change.after && <p className="diff-added">{change.after}</p>}
        </article>
      ))}

      <h3 className="history-heading">Conversation</h3>
      {messages.length === 0 && <p className="hint">No questions on this document yet.</p>}
      {messages.map((message) => (
        <article key={message.id} className="history-item">
          <p className="patch-target">{message.role === "user" ? "You" : "Assistant"}</p>
          <p className="qa-answer">{message.content}</p>
          <p className="history-meta">{formatWhen(message.created_at)}</p>
        </article>
      ))}
    </div>
  );
}
