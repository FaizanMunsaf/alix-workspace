import { useState, type FormEvent } from "react";
import { askQuestion, type QAResponse } from "../../api/qa";
import type { DocumentMessage } from "../../api/history";

type Props = {
  documentId: string | null;
  messages: DocumentMessage[];
  onAsked: () => Promise<void>;
};

export function AskPanel({ documentId, messages, onAsked }: Props) {
  const [query, setQuery] = useState("");
  const [qa, setQa] = useState<QAResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);

  async function handleAsk(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setAsking(true);
    setError(null);
    try {
      setQa(await askQuestion(query.trim(), documentId ?? undefined));
      setQuery("");
      await onAsked();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question failed.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="assistant-body">
      <form onSubmit={handleAsk} className="ask-form">
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={
            documentId ? "Ask about this contract…" : "Ask across ingested contracts…"
          }
          rows={4}
        />
        <button type="submit" disabled={asking}>
          {asking ? "Searching…" : "Search"}
        </button>
      </form>
      {error && <p className="error-text">{error}</p>}
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
          {qa.sources.map((source, index) => (
            <p key={index} className="qa-source">
              {source.metadata.clause_category ?? "clause"}: {source.content}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
