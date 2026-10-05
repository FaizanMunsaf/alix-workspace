import { useEffect, useState, type FormEvent } from "react";
import type { DocumentChange } from "../../api/history";
import type { EditPatch } from "../../api/edits";
import {
  groundedReview,
  listKnowledgeSources,
  type GroundedCitation,
  type GroundedReviewResponse,
  type KnowledgeSource,
} from "../../api/knowledge";

type Props = {
  documentId: string | null;
  getHtml: () => string;
  applyingId: string | null;
  pending: DocumentChange[];
  onAccept: (patch: EditPatch) => Promise<void>;
  onReject: (patchId: string) => Promise<void>;
  onProposed: () => Promise<void>;
  onJumpToSource: (text: string) => boolean;
};

const LAYER_LABEL: Record<GroundedCitation["layer"], string> = {
  contract: "Contract",
  playbook: "Playbook",
  public_ref: "Public",
};

export function GroundedPanel({
  documentId,
  getHtml,
  applyingId,
  pending,
  onAccept,
  onReject,
  onProposed,
  onJumpToSource,
}: Props) {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [instruction, setInstruction] = useState("");
  const [includePublic, setIncludePublic] = useState(true);
  const [review, setReview] = useState<GroundedReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingSources, setLoadingSources] = useState(false);
  const [reviewing, setReviewing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoadingSources(true);
    void listKnowledgeSources()
      .then((rows) => {
        if (!cancelled) setSources(rows);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load knowledge sources.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingSources(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleReview(event: FormEvent) {
    event.preventDefault();
    if (!documentId) return;
    setReviewing(true);
    setError(null);
    try {
      const result = await groundedReview(documentId, {
        html: getHtml(),
        instruction: instruction.trim() || null,
        include_public: includePublic,
      });
      setReview(result);
      await onProposed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Grounded review failed.");
    } finally {
      setReviewing(false);
    }
  }

  const patches: EditPatch[] =
    review?.patches?.length
      ? review.patches
      : pending.map((change) => ({
          id: change.id,
          target: change.target,
          before: change.before,
          after: change.after,
          rationale: change.rationale ?? "",
          status: "pending" as const,
        }));

  return (
    <div className="assistant-body">
      <p className="hint">
        Review the active contract against private playbooks and optional public legal refs.
        Sources stay labeled by layer; only contract text can be redlined.
      </p>

      <div className="qa-result">
        <p className="patch-target">Knowledge layers</p>
        {loadingSources && <p className="hint">Loading sources…</p>}
        {!loadingSources && sources.length === 0 && (
          <p className="hint">No knowledge sources yet.</p>
        )}
        {sources.map((source) => (
          <article key={source.id} className="history-item">
            <p className="qa-source-label">
              {source.source_layer === "playbook" ? "Playbook" : "Public"} · {source.title}
            </p>
            <p className="hint">
              {source.description ?? "—"} ({source.chunk_count} chunks)
            </p>
          </article>
        ))}
      </div>

      <form onSubmit={handleReview} className="ask-form">
        <textarea
          value={instruction}
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="Optional instruction (default: align liability & confidentiality with playbooks)"
          rows={3}
          disabled={!documentId || reviewing}
        />
        <label className="hint">
          <input
            type="checkbox"
            checked={includePublic}
            onChange={(event) => setIncludePublic(event.target.checked)}
          />{" "}
          Include public legal references
        </label>
        <button type="submit" disabled={!documentId || reviewing}>
          {reviewing ? "Reviewing…" : "Review against playbooks"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {review && (
        <div className="qa-result">
          {review.deviations.length > 0 && (
            <>
              <p className="patch-target">Deviations</p>
              <ul className="hint">
                {review.deviations.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </>
          )}
          {review.plan.length > 0 && (
            <>
              <p className="patch-target">Plan</p>
              <ul className="hint">
                {review.plan.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {patches.length > 0 && (
        <div className="qa-result">
          <p className="patch-target">Proposed redlines</p>
          {patches.map((patch) => (
            <article key={patch.id} className="history-item">
              <p className="patch-target">{patch.target}</p>
              <p className="diff-deleted">{patch.before}</p>
              <p className="diff-added">{patch.after}</p>
              {patch.rationale && <p className="hint">{patch.rationale}</p>}
              <div className="ask-form" style={{ flexDirection: "row" }}>
                <button
                  type="button"
                  disabled={applyingId === patch.id}
                  onClick={() => void onAccept(patch)}
                >
                  {applyingId === patch.id ? "Applying…" : "Accept"}
                </button>
                <button type="button" onClick={() => void onReject(patch.id)}>
                  Reject
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {review && review.citations.length > 0 && (
        <div className="qa-result">
          <p className="patch-target">Citations by layer</p>
          {review.citations.map((citation, index) => (
            <button
              key={`${citation.label}-${index}`}
              type="button"
              className="qa-source qa-source-button"
              onClick={() => {
                if (citation.layer === "contract") onJumpToSource(citation.content);
              }}
              title={
                citation.layer === "contract"
                  ? "Jump to contract passage"
                  : `${LAYER_LABEL[citation.layer]} reference`
              }
            >
              <span className="qa-source-label">
                {LAYER_LABEL[citation.layer]} · {citation.label}
                {citation.title ? ` · ${citation.title}` : ""}
              </span>
              <span className="qa-source-body">{citation.content}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
