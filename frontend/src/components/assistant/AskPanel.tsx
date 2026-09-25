import { useState, type FormEvent } from "react";
import { askQuestion, type QAResponse } from "../../api/qa";
import type { DocumentMessage } from "../../api/history";
import type { DocumentVersion } from "../../api/documents";
import type { EditorSelection } from "../editor/ContractEditor";

type OutlineItem = {
  label: string;
  jumpText: string;
};

type AstNodeLike = {
  node_type?: string;
  title?: string | null;
  content?: string | null;
  children?: AstNodeLike[];
};

type Props = {
  documentId: string | null;
  selection: EditorSelection | null;
  versions: DocumentVersion[];
  messages: DocumentMessage[];
  onAsked: () => Promise<void>;
  onJumpToSource: (text: string) => boolean;
};

export function AskPanel({
  documentId,
  selection,
  versions,
  messages,
  onAsked,
  onJumpToSource,
}: Props) {
  const [query, setQuery] = useState("");
  const [qa, setQa] = useState<QAResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const [jumpHint, setJumpHint] = useState<string | null>(null);

  const selectedText = selection?.text.trim() ?? "";
  const outline = outlineFromVersion(versions.at(-1) ?? null);

  async function handleAsk(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setAsking(true);
    setError(null);
    setJumpHint(null);
    try {
      setQa(
        await askQuestion(
          query.trim(),
          documentId ?? undefined,
          selectedText || null,
        ),
      );
      setQuery("");
      await onAsked();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question failed.");
    } finally {
      setAsking(false);
    }
  }

  function handleJump(content: string) {
    const ok = onJumpToSource(content);
    setJumpHint(ok ? "Located in the document." : "Could not find that passage in the editor.");
  }

  return (
    <div className="assistant-body">
      <form onSubmit={handleAsk} className="ask-form">
        {selectedText ? (
          <p className="qa-selection-hint">
            Using selection ({selectedText.length} chars). Clear the highlight to ask about the
            whole contract.
          </p>
        ) : (
          <p className="hint">
            Tip: highlight a clause first to ground the answer on that passage.
          </p>
        )}
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={
            documentId
              ? selectedText
                ? "Ask about the selected passage…"
                : "Ask about this contract… e.g. Where is termination?"
              : "Ask across ingested contracts…"
          }
          rows={4}
        />
        <button type="submit" disabled={asking}>
          {asking ? "Searching…" : "Ask"}
        </button>
      </form>
      {error && <p className="error-text">{error}</p>}
      {jumpHint && <p className="hint">{jumpHint}</p>}
      {outline.length > 0 && (
        <div className="qa-result">
          <p className="patch-target">Outline</p>
          {outline.map((item, index) => (
            <button
              key={`${item.label}-${index}`}
              type="button"
              className="qa-source qa-source-button"
              onClick={() => handleJump(item.jumpText)}
              title="Jump to this heading"
            >
              <span className="qa-source-label">{item.label}</span>
            </button>
          ))}
        </div>
      )}
      {messages.length > 0 ? (
        <div className="qa-result">
          {messages.map((message) => (
            <article key={message.id} className="history-item">
              <p className="patch-target">{message.role === "user" ? "You" : "Assistant"}</p>
              <p className="qa-answer">{message.content}</p>
            </article>
          ))}
        </div>
      ) : (
        qa && <p className="qa-answer">{qa.answer}</p>
      )}
      {qa && qa.sources.length > 0 && (
        <div className="qa-result">
          <p className="patch-target">Sources</p>
          {qa.sources.map((source, index) => (
            <button
              key={index}
              type="button"
              className="qa-source qa-source-button"
              onClick={() => handleJump(source.content)}
              title="Jump to this passage in the editor"
            >
              <span className="qa-source-label">
                {source.metadata.label ?? `Source ${index + 1}`}
                {source.metadata.clause_category
                  ? ` · ${source.metadata.clause_category}`
                  : ""}
              </span>
              <span className="qa-source-body">{source.content}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function outlineFromVersion(version: DocumentVersion | null): OutlineItem[] {
  const nodes = version?.ast_json?.nodes;
  if (!Array.isArray(nodes)) return [];
  const items: OutlineItem[] = [];
  walkOutline(nodes as AstNodeLike[], items);
  return items.slice(0, 40);
}

function walkOutline(nodes: AstNodeLike[], items: OutlineItem[]) {
  for (const node of nodes) {
    const type = node.node_type ?? "";
    const title = (node.title || "").trim();
    const content = (node.content || "").trim();
    if (
      (type === "heading" ||
        type === "section" ||
        type === "clause" ||
        type === "sub_clause") &&
      (title || content)
    ) {
      const label = title || content.slice(0, 80);
      items.push({
        label: title ? label : content.slice(0, 80),
        jumpText: title ? `${title} ${content}`.trim() : content,
      });
    }
    if (node.children?.length) walkOutline(node.children, items);
  }
}
