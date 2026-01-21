'use client';

import { useEffect, useMemo, useState } from 'react';

import type { CourseSummary, ExportComponent, ExportFormat, ExportRangeKind } from '../../lib/api';
import { exportData, getCourses } from '../../lib/api';
import type { ActiveCourse } from '../../lib/course';

type CourseMode = 'current' | 'choose' | 'all';

type Props = {
  open: boolean;
  activeCourse: ActiveCourse | null;
  onClose: () => void;
};

const INSIGHTS_COMPONENTS: Array<{ id: ExportComponent; label: string }> = [
  { id: 'insights_totals', label: 'Insights: totals' },
  { id: 'insights_top_questions', label: 'Insights: top questions' },
  { id: 'insights_daily_volume', label: 'Insights: daily volume' },
  { id: 'insights_confidence_trend', label: 'Insights: confidence trend' },
  { id: 'insights_pain_points', label: 'Insights: pain points' },
  { id: 'insights_escalations', label: 'Insights: escalations table' },
];

const RAW_COMPONENTS: Array<{ id: ExportComponent; label: string }> = [
  { id: 'raw_interactions', label: 'Raw: interactions log' },
  { id: 'raw_answers', label: 'Raw: answers log' },
  { id: 'raw_review_queue', label: 'Raw: review queue' },
  { id: 'raw_faq', label: 'Raw: FAQ entries' },
  { id: 'raw_escalations', label: 'Raw: escalations (PII optional)' },
];

function defaultTimezone(): string | undefined {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return undefined;
  }
}

export default function ExportDataModal({ open, activeCourse, onClose }: Props) {
  const [courseMode, setCourseMode] = useState<CourseMode>('current');
  const [courseList, setCourseList] = useState<CourseSummary[]>([]);
  const [courseListError, setCourseListError] = useState<string | null>(null);
  const [chosenCourseId, setChosenCourseId] = useState<string>('');

  const [format, setFormat] = useState<ExportFormat>('json');
  const [range, setRange] = useState<ExportRangeKind>('30d');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  const [components, setComponents] = useState<Set<ExportComponent>>(
    () => new Set<ExportComponent>(['insights_totals']),
  );

  const [includePii, setIncludePii] = useState(false);
  const [includePiiConfirm, setIncludePiiConfirm] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setError(null);
    setCourseListError(null);
    setChosenCourseId(activeCourse?.id || '');

    // Fetch course list for "choose course" dropdown.
    getCourses()
      .then((data) => setCourseList(data))
      .catch((err) => setCourseListError(err instanceof Error ? err.message : 'Unable to load courses'));
  }, [activeCourse?.id, open]);

  const hasActiveCourse = Boolean(activeCourse?.id);
  const canUseCurrentCourse = hasActiveCourse;

  const effectiveCourseId = useMemo(() => {
    if (courseMode === 'all') return 'all';
    if (courseMode === 'choose') return chosenCourseId;
    return activeCourse?.id || '';
  }, [activeCourse?.id, chosenCourseId, courseMode]);

  const componentList = useMemo(() => Array.from(components), [components]);

  const requiresPiiConfirmation = includePii;
  const piiConfirmed = !requiresPiiConfirmation || includePiiConfirm.trim() === 'INCLUDE';

  const hasComponents = componentList.length > 0;
  const requiresDates = range === 'custom';
  const customDatesOk =
    !requiresDates || (startDate.trim().length === 10 && endDate.trim().length === 10);

  const formReady = effectiveCourseId && hasComponents && customDatesOk && piiConfirmed && !submitting;

  const toggleComponent = (id: ExportComponent) => {
    setComponents((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    setComponents(new Set<ExportComponent>([...INSIGHTS_COMPONENTS, ...RAW_COMPONENTS].map((c) => c.id)));
  };

  const clearAll = () => setComponents(new Set());

  const handleDownload = async () => {
    if (!formReady) return;
    setSubmitting(true);
    setError(null);

    try {
      const tz = defaultTimezone();
      const { blob, filename } = await exportData({
        courseId: effectiveCourseId,
        components: componentList,
        format,
        range,
        startDate: requiresDates ? startDate : undefined,
        endDate: requiresDates ? endDate : undefined,
        tz,
        includePii,
        includePiiConfirm: includePii ? includePiiConfirm.trim() : undefined,
      });

      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/60 px-4 py-8">
      <div role="dialog" aria-modal="true" className="relative w-full max-w-2xl rounded-3xl bg-white p-8 shadow-xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
          aria-label="Close export modal"
          disabled={submitting}
        >
          ✕
        </button>

        <div className="mb-6 flex flex-col gap-2">
          <h2 className="text-xl font-semibold text-slate-900">Export data</h2>
          <p className="text-sm text-slate-600">
            Download course data for analysis elsewhere. Exports use your local timezone for date filters.
          </p>
        </div>

        {error && (
          <div className="mb-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">
            {error}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-800">Course</h3>
              <div className="mt-2 space-y-2 text-sm text-slate-700">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="course-mode"
                    value="current"
                    checked={courseMode === 'current'}
                    onChange={() => setCourseMode('current')}
                    disabled={!canUseCurrentCourse || submitting}
                  />
                  Current course {activeCourse ? `(${activeCourse.name})` : ''}
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="course-mode"
                    value="choose"
                    checked={courseMode === 'choose'}
                    onChange={() => setCourseMode('choose')}
                    disabled={submitting}
                  />
                  Choose course…
                </label>
                {courseMode === 'choose' && (
                  <div className="pl-6">
                    <select
                      value={chosenCourseId}
                      onChange={(event) => setChosenCourseId(event.target.value)}
                      disabled={submitting}
                      className="lena-input"
                    >
                      <option value="" disabled>
                        Select a course
                      </option>
                      {courseList.map((course) => (
                        <option key={course.id} value={course.id}>
                          {course.code ? `${course.code} · ${course.name}` : course.name}
                        </option>
                      ))}
                    </select>
                    {courseListError && <p className="mt-2 text-xs text-rose-700">{courseListError}</p>}
                  </div>
                )}
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="course-mode"
                    value="all"
                    checked={courseMode === 'all'}
                    onChange={() => setCourseMode('all')}
                    disabled={submitting}
                  />
                  All courses (creates a zip split by course)
                </label>
                {!canUseCurrentCourse && courseMode === 'current' && (
                  <p className="pl-6 text-xs text-slate-500">Pick a course first to use “Current course”.</p>
                )}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-slate-800">Format</h3>
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setFormat('json')}
                  disabled={submitting}
                  className={`lena-tab ${format === 'json' ? 'lena-tab-active' : 'lena-tab-inactive'}`}
                >
                  JSON
                </button>
                <button
                  type="button"
                  onClick={() => setFormat('csv')}
                  disabled={submitting}
                  className={`lena-tab ${format === 'csv' ? 'lena-tab-active' : 'lena-tab-inactive'}`}
                >
                  CSV
                </button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-slate-800">Date range</h3>
              <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                <button
                  type="button"
                  onClick={() => setRange('7d')}
                  disabled={submitting}
                  className={`rounded-2xl border px-3 py-2 text-left transition ${
                    range === '7d' ? 'border-lena-primary bg-lena-primary text-white' : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  Last 7 days
                </button>
                <button
                  type="button"
                  onClick={() => setRange('30d')}
                  disabled={submitting}
                  className={`rounded-2xl border px-3 py-2 text-left transition ${
                    range === '30d' ? 'border-lena-primary bg-lena-primary text-white' : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  Last 30 days
                </button>
                <button
                  type="button"
                  onClick={() => setRange('all')}
                  disabled={submitting}
                  className={`rounded-2xl border px-3 py-2 text-left transition ${
                    range === 'all' ? 'border-lena-primary bg-lena-primary text-white' : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  All time
                </button>
                <button
                  type="button"
                  onClick={() => setRange('custom')}
                  disabled={submitting}
                  className={`rounded-2xl border px-3 py-2 text-left transition ${
                    range === 'custom' ? 'border-lena-primary bg-lena-primary text-white' : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  Custom…
                </button>
              </div>
              {range === 'custom' && (
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600" htmlFor="export-start">
                      Start (YYYY-MM-DD)
                    </label>
                    <input
                      id="export-start"
                      type="date"
                      value={startDate}
                      onChange={(event) => setStartDate(event.target.value)}
                      disabled={submitting}
                      className="lena-input mt-1"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600" htmlFor="export-end">
                      End (YYYY-MM-DD)
                    </label>
                    <input
                      id="export-end"
                      type="date"
                      value={endDate}
                      onChange={(event) => setEndDate(event.target.value)}
                      disabled={submitting}
                      className="lena-input mt-1"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-800">Components</h3>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={selectAll}
                    disabled={submitting}
                    className="lena-button-ghost px-3 py-1"
                  >
                    Select all
                  </button>
                  <button
                    type="button"
                    onClick={clearAll}
                    disabled={submitting}
                    className="lena-button-ghost px-3 py-1"
                  >
                    Clear
                  </button>
                </div>
              </div>

              <div className="mt-3 space-y-3">
                <div>
                  <p className="text-xs font-semibold text-slate-500">Insights</p>
                  <div className="mt-2 space-y-2 text-sm text-slate-700">
                    {INSIGHTS_COMPONENTS.map((item) => (
                      <label key={item.id} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={components.has(item.id)}
                          onChange={() => toggleComponent(item.id)}
                          disabled={submitting}
                        />
                        {item.label}
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-xs font-semibold text-slate-500">Raw logs</p>
                  <div className="mt-2 space-y-2 text-sm text-slate-700">
                    {RAW_COMPONENTS.map((item) => (
                      <label key={item.id} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={components.has(item.id)}
                          onChange={() => toggleComponent(item.id)}
                          disabled={submitting}
                        />
                        {item.label}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {!hasComponents && (
                <p className="mt-3 text-xs text-rose-700">Select at least one component.</p>
              )}
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <label className="flex items-start gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={includePii}
                  onChange={(event) => setIncludePii(event.target.checked)}
                  disabled={submitting}
                  className="mt-1"
                />
                <span>
                  Include student PII (name/email) where available. Off by default.
                  <span className="block text-xs text-slate-500">
                    Requires typing INCLUDE to confirm.
                  </span>
                </span>
              </label>
              {includePii && (
                <div className="mt-3">
                  <label htmlFor="pii-confirm" className="block text-xs font-semibold text-slate-600">
                    Confirm
                  </label>
                  <input
                    id="pii-confirm"
                    type="text"
                    value={includePiiConfirm}
                    onChange={(event) => setIncludePiiConfirm(event.target.value)}
                    disabled={submitting}
                    placeholder="Type INCLUDE"
                    className="lena-input mt-1"
                  />
                  {!piiConfirmed && (
                    <p className="mt-2 text-xs text-rose-700">Type INCLUDE to enable PII export.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="mt-7 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="lena-button-secondary px-4 py-2 text-sm"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDownload}
            disabled={!formReady}
            className="lena-button-primary px-5 py-2 text-sm"
          >
            {submitting ? 'Preparing…' : 'Download export'}
          </button>
        </div>
      </div>
    </div>
  );
}
