import { useState, type FormEvent } from "react";
import { diffVersions, type DiffResponse } from "../../api/diff";
import type { DocumentVersion } from "../../api/documents";

type Props = {
  documentId: string | null;
  versions: DocumentVersion[];
  restoringId: string | null;
  onRestore: (versionId: string) => Promise<void>;
};

export function DiffPanel({ documentId, versions, restoringId, onRestore }: Props) {
  const [fromId, setFromId] = useState("");
  const [toId, setToId] = useState("");
  const [diff, setDiff] = useState<DiffResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const latestId = versions.at(-1)?.id;

  async function handleDiff(event: FormEvent) {
    event.preventDefault();
    if (!fromId || !toId) return;
    setError(null);
    try {
      setDiff(await diffVersions(fromId, toId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Diff failed.");
    }
  }

  return (
    <div className="assistant-body">
      {versions.length < 2 ? (
        <p className="hint">
          Diff compares two stored versions. Save or accept an AI edit to create a
          checkpoint, then compare them here.
        </p>
      ) : (
        <form onSubmit={handleDiff} className="ask-form">
          <label>
            From
            <select value={fromId} onChange={(event) => setFromId(event.target.value)}>
              <option value="">Select version</option>
              {versions.map((version) => (
                <option key={version.id} value={version.id}>
                  v{version.version_number}
                </option>
              ))}
            </select>
          </label>
          <label>
            To
            <select value={toId} onChange={(event) => setToId(event.target.value)}>
              <option value="">Select version</option>
              {versions.map((version) => (
                <option key={version.id} value={version.id}>
                  v{version.version_number}
                </option>
              ))}
            </select>
          </label>
          <button type="submit">Compare</button>
        </form>
      )}
      {error && <p className="error-text">{error}</p>}
      {diff && (
        <div className="qa-result">
          <p className="hint">
            {diff.summary.added ?? 0} added, {diff.summary.deleted ?? 0} deleted,{" "}
            {diff.summary.modified ?? 0} modified
          </p>
          {[...diff.added, ...diff.deleted, ...diff.modified].map((change) => (
            <p key={`${change.status}-${change.path}`} className={`diff-${change.status}`}>
              {change.status} · {change.path}
              {change.title ? ` · ${change.title}` : ""}
            </p>
          ))}
        </div>
      )}
      {documentId && versions.length > 1 && (
        <div className="qa-result">
          <p className="hint">Restore copies an older version forward as a new checkpoint.</p>
          {versions
            .filter((version) => version.id !== latestId)
            .map((version) => (
              <div key={version.id} className="patch-actions">
                <button
                  type="button"
                  disabled={Boolean(restoringId)}
                  onClick={() => void onRestore(version.id)}
                >
                  {restoringId === version.id
                    ? "Restoring…"
                    : `Restore v${version.version_number}`}
                </button>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
