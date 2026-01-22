'use client';

import { useEffect, useMemo, useState } from 'react';

import type { ActiveCourse } from '../../lib/course';
import type { EscalationEvent, EscalationRow, EscalationStatus } from '../../lib/instructors';
import {
  listEscalationEvents,
  listEscalations,
  logEscalationReplyInitiated,
  markEscalationViewed,
  updateEscalation,
} from '../../lib/instructors';

type Props = {
  activeCourse: ActiveCourse;
  onCountsChange?: (delta?: { new?: number; unresolved?: number }) => void;
};

const STATUS_LABELS: Record<EscalationStatus, string> = {
  new: 'New',
  in_process: 'In process',
  contacted: 'Contacted',
  resolved: 'Resolved',
};

function truncate(text: string, max = 80) {
  const trimmed = text.trim().replace(/\s+/g, ' ');
  if (trimmed.length <= max) return trimmed;
  return `${trimmed.slice(0, Math.max(0, max - 1)).trimEnd()}…`;
}

function parseIso(value?: string | null): Date | null {
  if (!value) return null;
  const ms = Date.parse(value);
  if (!Number.isFinite(ms)) return null;
  return new Date(ms);
}

function hoursExcludingWeekends(start: Date, end: Date): number {
  if (end <= start) return 0;
  let cursor = new Date(start.getTime());
  let hours = 0;

  while (cursor < end) {
    const day = cursor.getDay(); // 0=Sun, 6=Sat
    const next = new Date(cursor.getTime());
    next.setHours(24, 0, 0, 0);
    const segmentEnd = next < end ? next : end;

    if (day !== 0 && day !== 6) {
      hours += (segmentEnd.getTime() - cursor.getTime()) / (1000 * 60 * 60);
    }
    cursor = segmentEnd;
  }

  return hours;
}

function ageLabel(submittedAt?: string | null) {
  const submitted = parseIso(submittedAt);
  if (!submitted) return '—';
  const now = new Date();
  const hours = hoursExcludingWeekends(submitted, now);
  if (hours < 1) return 'Just now';
  if (hours < 24) return `${Math.round(hours)}h`;
  return `${Math.round(hours / 24)}d`;
}

function overdue(submittedAt?: string | null) {
  const submitted = parseIso(submittedAt);
  if (!submitted) return false;
  return hoursExcludingWeekends(submitted, new Date()) >= 48;
}

function mailtoLink(payload: {
  to: string;
  subject: string;
  body: string;
}) {
  const params = new URLSearchParams();
  params.set('subject', payload.subject);
  params.set('body', payload.body);
  return `mailto:${encodeURIComponent(payload.to)}?${params.toString()}`;
}

export default function EscalationsInbox({ activeCourse, onCountsChange }: Props) {
  const [rows, setRows] = useState<EscalationRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | EscalationStatus>('all');
  const [showOverdueOnly, setShowOverdueOnly] = useState(false);
  const [pageSize, setPageSize] = useState(10);
  const [page, setPage] = useState(1);

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [eventsById, setEventsById] = useState<Record<string, EscalationEvent[]>>({});
  const [savingId, setSavingId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listEscalations(activeCourse.id);
      const ordered = data.map((row, idx) => ({ ...row, __order: idx }));
      setRows(ordered);
      onCountsChange?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load escalations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setRows([]);
    setExpandedId(null);
    setEventsById({});
    setPage(1);
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCourse.id]);

  const normalizedQuery = query.trim().toLowerCase();

  const filtered = useMemo(() => {
    const base = rows.filter((row) => {
      const status = (row.status || 'new') as EscalationStatus;
      if (statusFilter !== 'all' && status !== statusFilter) return false;
      if (showOverdueOnly && !overdue(row.submitted_at)) return false;

      if (!normalizedQuery) return true;
      const haystack = [
        row.student_name || '',
        row.student_email || '',
        row.question || '',
        row.notes || '',
        row.status || '',
        row.escalation_reason || '',
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalizedQuery);
    });

    base.sort((a, b) => {
      const aOrder = (a as any).__order ?? 0;
      const bOrder = (b as any).__order ?? 0;
      if (aOrder !== bOrder) return aOrder - bOrder;
      const aTs = Date.parse(a.submitted_at || '') || 0;
      const bTs = Date.parse(b.submitted_at || '') || 0;
      return bTs - aTs;
    });

    return base;
  }, [normalizedQuery, rows, showOverdueOnly, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const clampedPage = Math.min(page, totalPages);
  const paged = filtered.slice((clampedPage - 1) * pageSize, clampedPage * pageSize);

  useEffect(() => {
    if (page !== clampedPage) setPage(clampedPage);
  }, [clampedPage, page]);

  const openRow = async (row: EscalationRow) => {
    if (!row.id) return;
    const nextId = row.id;
    const willOpen = expandedId !== nextId;
    const wasNew = !row.last_viewed_at;
    setExpandedId(willOpen ? nextId : null);
    if (!willOpen) return;

    try {
      const updated = await markEscalationViewed(activeCourse.id, nextId);
      setRows((current) => current.map((r) => (r.id === nextId ? { ...r, ...updated } : r)));
      if (wasNew && updated.last_viewed_at) {
        onCountsChange?.({ new: -1 });
      } else {
        onCountsChange?.();
      }
    } catch {
      // ignore view marking failures
    }

    try {
      const events = await listEscalationEvents(activeCourse.id, nextId);
      setEventsById((current) => ({ ...current, [nextId]: events }));
    } catch {
      // ignore event loading failures
    }
  };

  const applyUpdate = async (id: string, patch: { status?: EscalationStatus; notes?: string }) => {
    setSavingId(id);
    setError(null);
    const before = rows.find((r) => r.id === id);
    const wasNew = !before?.last_viewed_at;
    try {
      const updated = await updateEscalation(activeCourse.id, id, patch);
      setRows((current) => current.map((row) => (row.id === id ? { ...row, ...updated } : row)));
      const nowNew = !updated.last_viewed_at;
      const deltaNew = (nowNew ? 1 : 0) - (wasNew ? 1 : 0);
      if (deltaNew !== 0) {
        onCountsChange?.({ new: deltaNew });
      } else {
        onCountsChange?.();
      }
      const events = await listEscalationEvents(activeCourse.id, id);
      setEventsById((current) => ({ ...current, [id]: events }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update escalation');
    } finally {
      setSavingId(null);
    }
  };

  const buildReply = (row: EscalationRow) => {
    const studentName = row.student_name || 'there';
    const question = row.question || '';
    const subject = `LENA follow-up: ${activeCourse.name} - ${truncate(question, 60)}`;
    const body = [
      `Hello, ${studentName},`,
      ``,
      `You recently escalated a question in LENA. I just wanted to take the time to respond and address your question.`,
      ``,
      `Your question:`,
      `> ${question}`,
      ``,
      `—`,
      ``,
    ].join('\n');
    const to = row.student_email || '';
    return { to, subject, body };
  };

  return (
    <section className="lena-card lena-card-padding flex w-full flex-1 flex-col gap-4">
      <header className="lena-section-header">
        <div className="flex flex-col gap-1">
          <h1 className="lena-title">Escalations</h1>
          <p className="lena-subtitle">Follow up on questions students asked to route to an instructor.</p>
        </div>
        <button type="button" onClick={load} disabled={loading} className="lena-button-primary">
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </header>

      <div className="grid gap-3 lg:grid-cols-12">
        <div className="lg:col-span-6">
          <label className="text-xs font-semibold text-slate-600" htmlFor="escalation-search">
            Search
          </label>
          <input
            id="escalation-search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            className="lena-input mt-1"
            placeholder="Search student, email, or question…"
          />
        </div>

        <div className="lg:col-span-3">
          <label className="text-xs font-semibold text-slate-600" htmlFor="escalation-status">
            Status
          </label>
          <select
            id="escalation-status"
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value as 'all' | EscalationStatus);
              setPage(1);
            }}
            className="lena-input mt-1"
          >
            <option value="all">All</option>
            <option value="new">New</option>
            <option value="in_process">In process</option>
            <option value="contacted">Contacted</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        <div className="lg:col-span-3">
          <label className="text-xs font-semibold text-slate-600" htmlFor="escalation-page-size">
            Per page
          </label>
          <select
            id="escalation-page-size"
            value={pageSize}
            onChange={(event) => {
              setPageSize(Number(event.target.value));
              setPage(1);
            }}
            className="lena-input mt-1"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      <label className="flex items-center gap-2 text-xs text-slate-600">
        <input
          type="checkbox"
          checked={showOverdueOnly}
          onChange={(event) => {
            setShowOverdueOnly(event.target.checked);
            setPage(1);
          }}
        />
        Show overdue only (48 business hours)
      </label>

      {error && <div className="lena-alert-error">{error}</div>}

      {paged.length === 0 && !loading && (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
          No escalations match your filters.
        </div>
      )}

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <ul className="divide-y divide-slate-100">
          {paged.map((row) => {
            const status = (row.status || 'new') as EscalationStatus;
            const isNew = !row.last_viewed_at;
            const isOverdue = overdue(row.submitted_at);
            const preview = truncate(row.question || '', 80);
            const confidencePct =
              typeof row.confidence === 'number' ? `${Math.round(row.confidence * 100)}%` : null;
            const isExpanded = expandedId === row.id;

            return (
              <li
                key={row.id}
                className={`transition-all ${
                  isExpanded
                    ? 'bg-slate-50 shadow-sm'
                    : isNew
                      ? 'bg-amber-50/80'
                      : 'bg-white'
                } hover:bg-slate-100/70 hover:shadow-sm`}
              >
                <div
                  className={`px-4 py-3 transition-all duration-200 ${
                    isExpanded ? 'border-l-4 border-l-lena-primary/60 bg-slate-50' : ''
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <button
                      type="button"
                      className="group min-w-0 flex-1 text-left"
                      onClick={() => void openRow(row)}
                      aria-expanded={expandedId === row.id}
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-slate-900">{row.student_name || 'Student'}</span>
                        {row.student_email && <span className="text-xs text-slate-500">{row.student_email}</span>}
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                          {STATUS_LABELS[status]}
                        </span>
                        {isNew && (
                          <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white animate-pulse">
                            New
                          </span>
                        )}
                        {isOverdue && (
                          <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">
                            Overdue
                          </span>
                        )}
                        {confidencePct && (
                          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">
                            Confidence {confidencePct}
                          </span>
                        )}
                        {row.escalation_reason && (
                          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">
                            {row.escalation_reason === 'low_confidence' ? 'Low confidence' : row.escalation_reason}
                          </span>
                        )}
                      </div>
                      <p className="mt-2 text-sm text-slate-700">{preview || '—'}</p>
                    </button>

                    <div className="flex shrink-0 flex-col items-end gap-2">
                      <div className="text-xs text-slate-500">
                        {row.submitted_at ? new Date(row.submitted_at).toLocaleString() : '—'} · {ageLabel(row.submitted_at)}
                      </div>
                      <a
                        href={row.student_email ? mailtoLink(buildReply(row)) : undefined}
                        onClick={(event) => {
                          if (!row.student_email) {
                            event.preventDefault();
                            return;
                          }
                          void logEscalationReplyInitiated(activeCourse.id, row.id).catch(() => undefined);
                        }}
                        className={`lena-button-primary px-3 py-1 text-xs ${
                          !row.student_email ? 'pointer-events-none opacity-50' : ''
                        }`}
                      >
                        Reply
                      </a>
                    </div>
                  </div>
                </div>

                <div
                  className={`overflow-hidden border-t border-slate-100 transition-[max-height,opacity,padding,background-color] duration-300 ease-out ${
                    isExpanded ? 'max-h-[1600px] bg-slate-50 px-4 py-4 opacity-100' : 'max-h-0 bg-white px-4 py-0 opacity-0'
                  }`}
                >
                  {isExpanded && (
                    <div className="space-y-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="text-sm font-semibold text-slate-800">Escalation details</h3>
                          <p className="text-xs text-slate-500">Question, notes, status, and activity</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setExpandedId(null)}
                          className="lena-button-secondary px-3 py-1 text-xs"
                        >
                          Collapse
                        </button>
                      </div>

                      <div className="grid gap-4 lg:grid-cols-12">
                        <div className="lg:col-span-8 space-y-4">
                          <div>
                            <h3 className="text-sm font-semibold text-slate-800">Question</h3>
                            <p className="mt-2 whitespace-pre-line rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800">
                              {row.question || '—'}
                            </p>
                          </div>

                          <div>
                            <h3 className="text-sm font-semibold text-slate-800">Notes</h3>
                            <textarea
                              value={row.notes || ''}
                              onChange={(event) => {
                                const next = event.target.value;
                                setRows((current) =>
                                  current.map((r) => (r.id === row.id ? { ...r, notes: next } : r)),
                                );
                              }}
                              className="lena-input mt-2 min-h-[96px]"
                              placeholder="Add notes about follow-up…"
                            />
                            <div className="mt-2 flex flex-wrap gap-2">
                              <button
                                type="button"
                                onClick={() => void applyUpdate(row.id, { notes: row.notes || '' })}
                                disabled={savingId === row.id}
                                className="lena-button-primary px-4 py-2 text-sm"
                              >
                                {savingId === row.id ? 'Saving…' : 'Save note'}
                              </button>
                              <button
                                type="button"
                                onClick={() => void applyUpdate(row.id, { status: 'contacted' })}
                                disabled={savingId === row.id}
                                className="lena-button-secondary px-4 py-2 text-sm"
                              >
                                Mark contacted
                              </button>
                              <button
                                type="button"
                                onClick={() => void applyUpdate(row.id, { status: 'resolved' })}
                                disabled={savingId === row.id}
                                className="lena-button-secondary px-4 py-2 text-sm"
                              >
                                Mark resolved
                              </button>
                            </div>
                          </div>
                        </div>

                        <div className="lg:col-span-4">
                          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                            <h3 className="text-sm font-semibold text-slate-800">Details</h3>
                            <dl className="mt-3 space-y-2 text-sm text-slate-700">
                              <div className="flex items-start justify-between gap-3">
                                <dt className="text-xs font-semibold text-slate-500">Course</dt>
                                <dd className="text-right">{activeCourse.name}</dd>
                              </div>
                              <div className="flex items-start justify-between gap-3">
                                <dt className="text-xs font-semibold text-slate-500">Status</dt>
                                <dd>
                                  <select
                                    value={status}
                                    onChange={(event) =>
                                      void applyUpdate(row.id, { status: event.target.value as EscalationStatus })
                                    }
                                    className="lena-input py-1 text-sm"
                                    disabled={savingId === row.id}
                                  >
                                    <option value="new">New</option>
                                    <option value="in_process">In process</option>
                                    <option value="contacted">Contacted</option>
                                    <option value="resolved">Resolved</option>
                                  </select>
                                </dd>
                              </div>
                              <div className="flex items-start justify-between gap-3">
                                <dt className="text-xs font-semibold text-slate-500">Actions</dt>
                                <dd>
                                  <div className="flex flex-wrap items-center gap-2 pt-1">
                                    <button
                                      type="button"
                                      onClick={() => void applyUpdate(row.id, { status: 'in_process' })}
                                      disabled={savingId === row.id}
                                      className="lena-button-secondary px-3 py-1 text-xs"
                                    >
                                      Mark in process
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => void applyUpdate(row.id, { status: 'new' })}
                                      disabled={savingId === row.id}
                                      className="lena-button-secondary px-3 py-1 text-xs"
                                      title="Demo/testing: mark as new to exercise the badge"
                                    >
                                      Mark new
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => void applyUpdate(row.id, { status: 'contacted' })}
                                      disabled={savingId === row.id}
                                      className="lena-button-secondary px-3 py-1 text-xs"
                                    >
                                      Mark contacted
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => void applyUpdate(row.id, { status: 'resolved' })}
                                      disabled={savingId === row.id}
                                      className="lena-button-secondary px-3 py-1 text-xs"
                                    >
                                      Mark resolved
                                    </button>
                                  </div>
                                </dd>
                              </div>
                              <div className="flex items-start justify-between gap-3">
                                <dt className="text-xs font-semibold text-slate-500">Submitted</dt>
                                <dd className="text-right">
                                  {row.submitted_at ? new Date(row.submitted_at).toLocaleString() : '—'}
                                </dd>
                              </div>
                              <div className="flex items-start justify-between gap-3">
                                <dt className="text-xs font-semibold text-slate-500">Age</dt>
                                <dd className="text-right">{ageLabel(row.submitted_at)}</dd>
                              </div>
                              <div className="flex items-start justify-between gap-3">
                                <dt className="text-xs font-semibold text-slate-500">Contacted</dt>
                                <dd className="text-right">
                                  {row.contacted_at ? new Date(row.contacted_at).toLocaleString() : '—'}
                                </dd>
                              </div>
                              <div className="flex items-start justify-between gap-3">
                                <dt className="text-xs font-semibold text-slate-500">Resolved</dt>
                                <dd className="text-right">
                                  {row.resolved_at ? new Date(row.resolved_at).toLocaleString() : '—'}
                                </dd>
                              </div>
                            </dl>

                            <div className="mt-4">
                              <h3 className="text-sm font-semibold text-slate-800">Activity</h3>
                              <div className="mt-2 space-y-2 text-xs text-slate-600">
                                {(eventsById[row.id] || []).length === 0 ? (
                                  <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3">
                                    No activity yet.
                                  </div>
                                ) : (
                                  <ul className="space-y-2">
                                    {(eventsById[row.id] || []).slice(0, 8).map((event) => (
                                      <li key={event.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2">
                                        <div className="flex items-center justify-between gap-3">
                                          <span className="font-semibold text-slate-700">{event.type.replace(/_/g, ' ')}</span>
                                          <span className="text-slate-500">{new Date(event.at).toLocaleString()}</span>
                                        </div>
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
        <span>
          Showing {(clampedPage - 1) * pageSize + 1}-{Math.min(clampedPage * pageSize, filtered.length)} of{' '}
          {filtered.length}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={clampedPage <= 1}
            className="lena-button-secondary px-3 py-1 text-xs"
          >
            Prev
          </button>
          <span className="text-xs text-slate-500">
            Page {clampedPage} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={clampedPage >= totalPages}
            className="lena-button-secondary px-3 py-1 text-xs"
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
