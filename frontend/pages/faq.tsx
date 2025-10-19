import { useEffect, useMemo, useState } from 'react';

import type { FAQEntry } from '../lib/api';
import { fetchFaq } from '../lib/api';

function matches(entry: FAQEntry, term: string) {
  const haystack = `${entry.question} ${entry.answer}`.toLowerCase();
  return haystack.includes(term.toLowerCase());
}

export default function FAQPage() {
  const [faq, setFaq] = useState<FAQEntry[]>([]);
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFaq()
      .then(setFaq)
      .catch((err) => setError(err instanceof Error ? err.message : 'Unable to load FAQ'));
  }, []);

  const filtered = useMemo(() => {
    if (!search) return faq;
    return faq.filter((entry) => matches(entry, search));
  }, [faq, search]);

  return (
    <div className="chat-card">
      <div className="chat-header">
        <div>
          <h1>Frequently Asked Questions</h1>
          <p className="bubble-meta">
            Curated answers promoted from learner feedback during the pilot.
          </p>
        </div>
      </div>

      <div className="composer">
        <input
          placeholder="Search the FAQ..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </div>

      <div className="chat-history">
        {filtered.length === 0 && (
          <div className="empty-state">No FAQ entries yet. Ask questions to build the list.</div>
        )}
        {filtered.map((entry, index) => (
          <div key={`${entry.question}-${index}`} className="bubble assistant">
            <strong>{entry.question}</strong>
            <span>{entry.answer}</span>
            <div className="bubble-meta">
              {entry.source_path && <span>Source: {entry.source_path} · </span>}
              {entry.updated_at && <span>Updated {new Date(entry.updated_at).toLocaleDateString()}</span>}
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div className="bubble-meta" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}
