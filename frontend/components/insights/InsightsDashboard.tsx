'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

import KpiCards from './KpiCards';
import ConfidenceChart from './ConfidenceChart';
import DailyVolumeChart from './DailyVolumeChart';
import EscalationsChart from './EscalationsChart';
import PainPointsList from './PainPointsList';
import TopQuestions from './TopQuestions';
import type { InsightsSummary } from '../../lib/api';
import { fetchInsights } from '../../lib/api';
import type { ActiveCourse } from '../../lib/course';

type Props = {
  activeCourse: ActiveCourse | null;
};

export default function InsightsDashboard({ activeCourse }: Props) {
  const [insights, setInsights] = useState<InsightsSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadInsights = useCallback(async (courseId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInsights(courseId);
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load insights');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!activeCourse) {
      setInsights(null);
      setError(null);
      setLoading(false);
      return;
    }
    loadInsights(activeCourse.id);
  }, [activeCourse, loadInsights]);

  const kpiMetrics = useMemo(() => {
    if (!insights) return [];
    return [
      { id: 'total-questions', label: 'Total Questions', value: insights.totals.questions.toLocaleString() },
      {
        id: 'helpful-rate',
        label: 'Helpful %',
        value: `${Math.round(insights.totals.helpful_rate * 100)}%`,
        description: 'Share of feedback marked helpful.',
      },
      {
        id: 'avg-confidence',
        label: 'Avg Confidence',
        value: `${Math.round(insights.totals.average_confidence * 100)}%`,
        description: 'Model self-rated accuracy last 7 days.',
      },
      {
        id: 'escalations',
        label: 'Escalations',
        value: insights.totals.escalations.toLocaleString(),
        description: 'Instructor follow-up requests this term.',
      },
    ];
  }, [insights]);

  const topQuestionLabels = useMemo(() => (insights ? insights.top_questions.map((item) => item.label) : []), [insights]);
  const topQuestionCounts = useMemo(() => (insights ? insights.top_questions.map((item) => item.count) : []), [insights]);

  const dailyVolumeLabels = useMemo(() => (insights ? insights.daily_volume.map((item) => item.date) : []), [insights]);
  const dailyVolumeValues = useMemo(() => (insights ? insights.daily_volume.map((item) => item.count) : []), [insights]);

  const confidenceLabels = useMemo(() => (insights ? insights.confidence_trend.map((item) => item.date) : []), [insights]);
  const confidenceValues = useMemo(() => (insights ? insights.confidence_trend.map((item) => item.confidence) : []), [insights]);

  const escalationDayBuckets = useMemo(() => {
    if (!insights) return { labels: [] as string[], values: [] as number[] };
    const counts: Record<string, number> = {};
    for (const entry of insights.escalations) {
      const day = (entry.submitted_at || '').slice(0, 10);
      if (!day) continue;
      counts[day] = (counts[day] || 0) + 1;
    }
    const labels = Object.keys(counts).sort();
    const values = labels.map((day) => counts[day]);
    return { labels, values };
  }, [insights]);

  const handleRefresh = () => {
    if (!activeCourse) return;
    loadInsights(activeCourse.id);
  };

  const courseLocked = !activeCourse;

  return (
    <section className="lena-card lena-card-padding flex w-full flex-1 flex-col gap-6">
      <header className="lena-section-header">
        <div className="flex flex-col gap-1">
          <h1 className="lena-title">Course Insights</h1>
          <p className="lena-subtitle">
            Spot engagement trends and escalation patterns for{' '}
            {activeCourse ? <span className="font-semibold text-slate-800">{activeCourse.name}</span> : 'your course'}.
          </p>
        </div>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={courseLocked || loading}
          className="lena-button-primary"
        >
          {loading ? 'Refreshing…' : 'Refresh data'}
        </button>
      </header>

      {courseLocked && (
        <div className="lena-callout">
          Choose a course to load its insights dashboard.
        </div>
      )}

      {!courseLocked && error && (
        <div className="lena-alert-error">{error}</div>
      )}

      {!courseLocked && !error && (
        <>
          <KpiCards metrics={kpiMetrics} onRefresh={handleRefresh} refreshing={loading} />

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-800">Top Questions</h2>
                <span className="text-xs text-slate-400">By volume</span>
              </div>
              {topQuestionLabels.length > 0 ? (
                <div className="mt-4">
                  <TopQuestions labels={topQuestionLabels} values={topQuestionCounts} />
                </div>
              ) : (
                <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
                  No top questions yet.
                </div>
              )}
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-800">Daily Volume</h2>
                <span className="text-xs text-slate-400">Last 30 days</span>
              </div>
              {dailyVolumeLabels.length > 0 ? (
                <div className="mt-4">
                  <DailyVolumeChart labels={dailyVolumeLabels} values={dailyVolumeValues} />
                </div>
              ) : (
                <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
                  No activity plotted yet.
                </div>
              )}
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-800">Confidence Over Time</h2>
                <span className="text-xs text-slate-400">Model self-report</span>
              </div>
              {confidenceLabels.length > 0 ? (
                <div className="mt-4">
                  <ConfidenceChart labels={confidenceLabels} values={confidenceValues} />
                </div>
              ) : (
                <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
                  Confidence data appears after the model answers a handful of questions.
                </div>
              )}
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-800">Escalations</h2>
              <p className="mt-1 text-xs text-slate-500">Escalations by day.</p>
              {escalationDayBuckets.labels.length > 0 ? (
                <div className="mt-4">
                  <EscalationsChart labels={escalationDayBuckets.labels} values={escalationDayBuckets.values} />
                </div>
              ) : (
                <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
                  No escalations yet.
                </div>
              )}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-800">Emerging Pain Points</h2>
            <p className="mt-1 text-xs text-slate-500">Week-over-week change in student confusion by topic.</p>
            <div className="mt-4">
              <PainPointsList items={insights?.pain_points ?? []} />
            </div>
          </div>

          {insights && <footer className="text-xs text-slate-400">Last refreshed {new Date(insights.last_updated).toLocaleString()}</footer>}
        </>
      )}
    </section>
  );
}
