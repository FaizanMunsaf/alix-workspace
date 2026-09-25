import { useEffect, useState, type FormEvent } from "react";
import type { DocumentChange } from "../../api/history";
import {
  proposeEdits,
  type EditPatch,
  type EditScope,
  type ProposeEditResponse,
} from "../../api/edits";
import type { EditorSelection } from "../editor/ContractEditor";

const QUICK_ACTIONS = [
  "Rewrite this more clearly",
  "Shorten this without changing its meaning",
  "Make this clause mutual",
  "Simplify this wording without changing its meaning",
];

type Props = {
  documentId: string | null;
  selection: EditorSelection | null;
  getHtml: () => string;
  applyingId: string | null;
  pending: DocumentChange[];
  onAccept: (patch: EditPatch) => Promise<void>;
  onReject: (patchId: string) => Promise<void>;
  onProposed: () => Promise<void>;
};

function patchesFromPending(documentId: string, pending: DocumentChange[]): ProposeEditResponse {
  return {
    document_id: documentId,
    scope: "selection",
    instruction: pending[0]?.instruction ?? "",
    plan: [],
    patches: pending.map((change) => ({
      id: change.id,
      target: change.target,
      before: change.before,
      after: change.after,
      rationale: change.rationale ?? "",
      status: "pending",
    })),
  };
}

export function EditPanel({
  documentId,
  selection,
  getHtml,
  applyingId,
  pending,
  onAccept,
  onReject,
  onProposed,
}: Props) {
  const [scope, setScope] = useState<EditScope>("selection");
  const [instruction, setInstruction] = useState("");
  const [proposal, setProposal] = useState<ProposeEditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [proposing, setProposing] = useState(false);

  const pendingSnapshot = JSON.stringify(
    pending.map((change) => ({
      id: change.id,
      instruction: change.instruction,
      target: change.target,
      before: change.before,
      after: change.after,
      rationale: change.rationale,
    })),
  );

  useEffect(() => {
    if (!documentId) {
      setProposal(null);
      return;
    }
    const items = JSON.parse(pendingSnapshot) as DocumentChange[];
    setProposal((current) => {
      const pendingIds = items.map((item) => item.id).join(",");
      const currentIds = current?.patches.map((patch) => patch.id).join(",") ?? "";
      if (current && pendingIds && pendingIds === currentIds) {
        return current;
      }
      return items.length ? patchesFromPending(documentId, items) : null;
    });
  }, [documentId, pendingSnapshot]);

  async function runPropose(prompt: string) {
    if (!documentId || !prompt.trim()) return;
    setProposing(true);
    setError(null);
    try {
      const result = await proposeEdits(documentId, {
        instruction: prompt.trim(),
        selection_text: scope === "selection" ? selection?.text ?? null : null,
        html: getHtml(),
        scope,
      });
      setProposal(result);
      await onProposed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not propose an edit.");
    } finally {
      setProposing(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    await runPropose(instruction);
  }

  async function rejectPatch(patchId: string) {
    setError(null);
    try {
      await onReject(patchId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reject the edit.");
    }
  }

  async function acceptPatch(patch: EditPatch) {
    setError(null);
    try {
      await onAccept(patch);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not apply the edit.");
    }
  }

  const selectedPreview = selection?.text.trim() ?? "";

  return (
    <div className="assistant-body">
      <div className="scope-toggle">
        <button
          type="button"
          className={scope === "selection" ? "active" : ""}
          onClick={() => setScope("selection")}
        >
          Selection
        </button>
        <button
          type="button"
          className={scope === "document" ? "active" : ""}
          onClick={() => setScope("document")}
        >
          Whole document
        </button>
      </div>

      {scope === "selection" ? (
        <p className="hint">
          {selectedPreview
            ? `Selected: ${selectedPreview.slice(0, 160)}${selectedPreview.length > 160 ? "…" : ""}`
            : "Select a clause in the contract, then choose an action."}
        </p>
      ) : (
        <p className="hint">
          Broad instructions use the full indexed contract when it fits, otherwise the
          top matching clauses. Excerpts are uniquified so apply hits the right place.
        </p>
      )}

      <div className="quick-actions">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action}
            type="button"
            disabled={!documentId || proposing}
            onClick={() => {
              setInstruction(action);
              void runPropose(action);
            }}
          >
            {action}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="ask-form">
        <textarea
          value={instruction}
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="e.g. Reduce the liability cap to 12 months of fees"
          rows={3}
        />
        <button type="submit" disabled={!documentId || proposing}>
          {proposing ? "Proposing…" : "Propose edit"}
        </button>
      </form>
      {error && <p className="error-text">{error}</p>}

      {proposal && (
        <div className="qa-result">
          {proposal.plan.length > 0 && (
            <p className="hint">Plan: {proposal.plan.join(" · ")}</p>
          )}
          {proposal.patches.length === 0 && (
            <p className="hint">No patches were proposed.</p>
          )}
          {proposal.patches.map((patch) => (
            <article key={patch.id} className="patch-card">
              <p className="patch-target">{patch.target}</p>
              {patch.rationale && <p className="hint">{patch.rationale}</p>}
              <p className="diff-deleted">{patch.before}</p>
              <p className="diff-added">{patch.after}</p>
              <div className="patch-actions">
                <button
                  type="button"
                  disabled={Boolean(applyingId)}
                  onClick={() => void acceptPatch(patch)}
                >
                  {applyingId === patch.id ? "Applying…" : "Accept"}
                </button>
                <button
                  type="button"
                  disabled={Boolean(applyingId)}
                  onClick={() => void rejectPatch(patch.id)}
                >
                  Reject
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
