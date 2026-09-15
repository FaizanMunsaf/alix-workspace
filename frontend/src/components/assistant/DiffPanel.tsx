import { useState, type FormEvent } from "react";
import { diffVersions, type DiffResponse } from "../../api/diff";
import type { DocumentVersion } from "../../api/documents";

type Props = {
  versions: DocumentVersion[];
};

export function DiffPanel({ versions }: Props) {
  const [fromId, setFromId] = useState("");
  const [toId, setToId] = useState("");
  const [diff, setDiff] = useState<DiffResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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
          Diff compares two stored versions of this document. Saving edits updates
          the current version; a second version appears when one is ingested later.
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
    </div>
  );
}
