import { useMemo, useState } from "react";
import type { DocumentChange, DocumentMessage } from "../../api/history";
import type { DocumentVersion } from "../../api/documents";
import type { EditPatch } from "../../api/edits";

type AuditFilter = "all" | "pending" | "ai" | "user" | "versions" | "chat";

type Props = {
  documentId: string | null;
  versions: DocumentVersion[];
  changes: DocumentChange[];
  messages: DocumentMessage[];
  applyingId: string | null;
  restoringId: string | null;
  onRestore: (versionId: string) => Promise<void>;
  onAccept: (patch: EditPatch) => Promise<void>;
  onReject: (patchId: string) => Promise<void>;
  onJumpToSource: (text: string) => boolean;
};

function formatWhen(value: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function toPatch(change: DocumentChange): EditPatch {
  return {
    id: change.id,
    target: change.target,
    before: change.before,
    after: change.after,
    rationale: change.rationale || "",
    status: "pending",
  };
}

function versionLabel(
  versions: DocumentVersion[],
  versionId: string | null,
): string | null {
  if (!versionId) return null;
  const match = versions.find((version) => version.id === versionId);
  return match ? `v${match.version_number}` : null;
}

export function HistoryPanel({
  documentId,
  versions,
  changes,
  messages,
  applyingId,
  restoringId,
  onRestore,
  onAccept,
  onReject,
  onJumpToSource,
}: Props) {
  const [filter, setFilter] = useState<AuditFilter>("all");
  const [jumpHint, setJumpHint] = useState<string | null>(null);

  const latestId = versions.at(-1)?.id;
  const pending = useMemo(
    () => changes.filter((change) => change.decision === "pending"),
    [changes],
  );
  const decided = useMemo(
    () => changes.filter((change) => change.decision !== "pending"),
    [changes],
  );
  const aiCount = changes.filter((change) => change.actor === "ai").length;
  const userCount = changes.filter((change) => change.actor === "user").length;
  const acceptedCount = changes.filter((change) => change.decision === "accepted").length;
  const rejectedCount = changes.filter((change) => change.decision === "rejected").length;

  const timeline = useMemo(() => {
    type Item =
      | { kind: "change"; at: string; change: DocumentChange }
      | { kind: "version"; at: string; version: DocumentVersion }
      | { kind: "message"; at: string; message: DocumentMessage };

    const items: Item[] = [
      ...changes.map((change) => ({
        kind: "change" as const,
        at: change.decided_at || change.created_at,
        change,
      })),
      ...versions.map((version) => ({
        kind: "version" as const,
        at: version.created_at,
        version,
      })),
      ...messages.map((message) => ({
        kind: "message" as const,
        at: message.created_at,
        message,
      })),
    ];
    return items.sort((a, b) => (a.at < b.at ? 1 : a.at > b.at ? -1 : 0));
  }, [changes, versions, messages]);

  if (!documentId) {
    return (
      <div className="assistant-body">
        <p className="hint">Open a contract to see checkpoints, redlines, and conversation history.</p>
      </div>
    );
  }

  function handleJump(text: string) {
    const ok = onJumpToSource(text);
    setJumpHint(ok ? "Located in the document." : "Could not find that passage in the editor.");
  }

  const showPending = filter === "all" || filter === "pending";
  const showVersions = filter === "all" || filter === "versions";
  const showDecided =
    filter === "all" || filter === "ai" || filter === "user";
  const showChat = filter === "all" || filter === "chat";
  const showTimeline = filter === "all";

  const filteredDecided = decided.filter((change) => {
    if (filter === "ai") return change.actor === "ai";
    if (filter === "user") return change.actor === "user";
    return true;
  });

  return (
    <div className="assistant-body">
      <div className="audit-summary">
        <span>{versions.length} versions</span>
        <span>{pending.length} pending</span>
        <span>{acceptedCount} accepted</span>
        <span>{rejectedCount} rejected</span>
        <span>{aiCount} AI / {userCount} user</span>
        <span>{messages.length} messages</span>
      </div>

      <div className="scope-toggle audit-filters">
        {(
          [
            ["all", "All"],
            ["pending", "Pending"],
            ["ai", "AI"],
            ["user", "User"],
            ["versions", "Versions"],
            ["chat", "Chat"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={filter === id ? "active" : ""}
            onClick={() => setFilter(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {jumpHint && <p className="hint">{jumpHint}</p>}

      {showPending && (
        <>
          <h3 className="history-heading">Pending redlines ({pending.length})</h3>
          {pending.length === 0 && <p className="hint">No pending AI proposals.</p>}
          {pending.map((change) => (
            <article key={change.id} className="history-item patch-card">
              <p className="patch-target">AI · {change.target} · pending</p>
              {change.instruction && <p className="hint">{change.instruction}</p>}
              <p className="history-meta">
                {formatWhen(change.created_at)}
                {versionLabel(versions, change.version_id)
                  ? ` · from ${versionLabel(versions, change.version_id)}`
                  : ""}
              </p>
              {change.before && <p className="diff-deleted">{change.before}</p>}
              {change.after && <p className="diff-added">{change.after}</p>}
              <div className="patch-actions">
                <button
                  type="button"
                  disabled={applyingId === change.id}
                  onClick={() => void onAccept(toPatch(change))}
                >
                  {applyingId === change.id ? "Applying…" : "Accept"}
                </button>
                <button
                  type="button"
                  disabled={Boolean(applyingId)}
                  onClick={() => void onReject(change.id)}
                >
                  Reject
                </button>
                {change.before && (
                  <button type="button" onClick={() => handleJump(change.before)}>
                    Jump
                  </button>
                )}
              </div>
            </article>
          ))}
        </>
      )}

      {showVersions && (
        <>
          <h3 className="history-heading">Versions</h3>
          {versions.length === 0 && <p className="hint">No versions yet.</p>}
          {[...versions].reverse().map((version) => (
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
        </>
      )}

      {showDecided && (
        <>
          <h3 className="history-heading">
            {filter === "ai"
              ? "AI changes"
              : filter === "user"
                ? "User changes"
                : "Decided changes"}
          </h3>
          {filteredDecided.length === 0 && (
            <p className="hint">No matching decided changes yet.</p>
          )}
          {filteredDecided.map((change) => (
            <article key={change.id} className="history-item">
              <p className="patch-target">
                {change.actor === "ai" ? "AI" : "User"} · {change.target} · {change.decision}
              </p>
              {change.instruction && <p className="hint">{change.instruction}</p>}
              <p className="history-meta">
                {formatWhen(change.created_at)}
                {change.decided_at ? ` · decided ${formatWhen(change.decided_at)}` : ""}
                {versionLabel(versions, change.version_id)
                  ? ` · from ${versionLabel(versions, change.version_id)}`
                  : ""}
                {versionLabel(versions, change.result_version_id)
                  ? ` → ${versionLabel(versions, change.result_version_id)}`
                  : ""}
              </p>
              {change.before && <p className="diff-deleted">{change.before}</p>}
              {change.after && <p className="diff-added">{change.after}</p>}
              {(change.before || change.after) && (
                <div className="patch-actions">
                  <button
                    type="button"
                    onClick={() => handleJump(change.before || change.after)}
                  >
                    Jump
                  </button>
                </div>
              )}
            </article>
          ))}
        </>
      )}

      {showChat && (
        <>
          <h3 className="history-heading">Conversation</h3>
          {messages.length === 0 && <p className="hint">No questions on this document yet.</p>}
          {messages.map((message) => (
            <article key={message.id} className="history-item">
              <p className="patch-target">
                {message.role === "user" ? "You" : "Assistant"}
              </p>
              <p className="qa-answer">{message.content}</p>
              <p className="history-meta">{formatWhen(message.created_at)}</p>
            </article>
          ))}
        </>
      )}

      {showTimeline && timeline.length > 0 && (
        <>
          <h3 className="history-heading">Audit timeline</h3>
          {timeline.slice(0, 40).map((item, index) => {
            if (item.kind === "version") {
              return (
                <article key={`v-${item.version.id}-${index}`} className="history-item timeline-item">
                  <p className="patch-target">
                    Checkpoint · v{item.version.version_number}
                    {item.version.id === latestId ? " · current" : ""}
                  </p>
                  <p className="history-meta">{formatWhen(item.at)}</p>
                </article>
              );
            }
            if (item.kind === "message") {
              return (
                <article key={`m-${item.message.id}-${index}`} className="history-item timeline-item">
                  <p className="patch-target">
                    Chat · {item.message.role === "user" ? "You" : "Assistant"}
                  </p>
                  <p className="qa-answer">{item.message.content.slice(0, 160)}</p>
                  <p className="history-meta">{formatWhen(item.at)}</p>
                </article>
              );
            }
            return (
              <article key={`c-${item.change.id}-${index}`} className="history-item timeline-item">
                <p className="patch-target">
                  {item.change.actor === "ai" ? "AI" : "User"} · {item.change.target} ·{" "}
                  {item.change.decision}
                </p>
                <p className="history-meta">{formatWhen(item.at)}</p>
              </article>
            );
          })}
        </>
      )}
    </div>
  );
}
