import { useState, type FormEvent } from "react";
import { askQuestion, type QAResponse } from "../../api/qa";

type Props = {
  documentId: string | null;
};

export function AskPanel({ documentId }: Props) {
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
      {qa && (
        <div className="qa-result">
          <p className="qa-answer">{qa.answer}</p>
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
