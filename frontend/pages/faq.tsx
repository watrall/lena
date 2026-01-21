import { useEffect, useMemo, useState } from 'react';

import type { NextPage } from 'next';

import type { FAQEntry } from '../lib/api';
import { fetchFaq } from '../lib/api';
import type { ActiveCourse } from '../lib/course';

type FAQPageProps = {
  activeCourse: ActiveCourse | null;
};

function matches(entry: FAQEntry, term: string) {
  const needle = term.trim().toLowerCase();
  if (!needle) return true;
  const haystack = `${entry.question} ${entry.answer}`.toLowerCase();
  return haystack.includes(needle);
}

const FAQPage: NextPage<FAQPageProps> = ({ activeCourse }) => {
  const [entries, setEntries] = useState<FAQEntry[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeCourse) {
      setEntries([]);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchFaq(activeCourse.id)
      .then((data) => {
        if (!cancelled) {
          setEntries(data);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unable to load FAQ');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeCourse]);

  const filteredEntries = useMemo(
    () => entries.filter((entry) => matches(entry, search)),
    [entries, search],
  );

  const courseLocked = !activeCourse;
  const hasEntries = filteredEntries.length > 0;
  const hasSearchTerm = search.trim().length > 0;

  return (
    <section className="lena-card lena-card-padding flex w-full flex-1 flex-col">
      <header className="flex flex-col gap-2 border-b border-slate-100 pb-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="lena-title">Course FAQ</h1>
            <p className="lena-subtitle">
              Questions promoted from recent student activity. Tailored to{' '}
              {activeCourse ? (
                <span className="font-medium text-slate-800">{activeCourse.name}</span>
              ) : (
                'your selected course'
              )}
              .
            </p>
          </div>
          {loading && (
            <span className="rounded-full bg-lena-secondary px-4 py-2 text-xs font-semibold text-lena-primary">
              Loading…
            </span>
          )}
        </div>
      </header>

      <div className="mt-6 flex flex-col gap-6">
        <div className="relative">
          <label htmlFor="faq-search" className="sr-only">
            Search FAQ
          </label>
          <input
            id="faq-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={courseLocked ? 'Pick a course to enable search.' : 'Search questions or keywords'}
            disabled={courseLocked || loading}
            className="lena-input px-4 py-3"
          />
        </div>

        <div className="space-y-4">
          {courseLocked && (
            <div className="lena-callout rounded-2xl px-4 py-6">
              Choose a course to view curated FAQ content.
            </div>
          )}

          {!courseLocked && error && (
            <div className="lena-alert-error rounded-2xl px-4 py-3" role="alert">
              {error}
            </div>
          )}

          {!courseLocked && !error && !loading && !hasEntries && (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm leading-relaxed text-slate-600">
              {hasSearchTerm
                ? 'Nothing matches that search yet. Try a different keyword or ask the chatbot so we can learn.'
                : 'No FAQ entries yet. As the chat answers more questions, we’ll start capturing the best responses here.'}
            </div>
          )}

          {!courseLocked && !error && hasEntries && (
            <ul className="space-y-4">
              {filteredEntries.map((entry, index) => (
                <li
                  key={`${entry.question}-${index}`}
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4 text-sm text-slate-800 shadow-sm"
                >
                  <h2 className="text-sm font-semibold text-slate-900">{entry.question}</h2>
                  <p className="mt-2 whitespace-pre-line leading-relaxed text-slate-700">{entry.answer}</p>
                  <div className="mt-3 text-xs text-slate-500">
                    {entry.source_path && <span>Source: {entry.source_path}</span>}
                    {entry.updated_at && (
                      <span className="ml-2">
                        Updated{' '}
                        {new Date(entry.updated_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
};

export default FAQPage;
