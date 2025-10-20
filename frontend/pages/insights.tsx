// insights.tsx – dashboards the course by blending KPIs, charts, and pain points.
'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

import type { NextPage } from 'next';

import KpiCards from '../components/insights/KpiCards';
import ConfidenceChart from '../components/insights/ConfidenceChart';
import DailyVolumeChart from '../components/insights/DailyVolumeChart';
import EscalationsTable from '../components/insights/EscalationsTable';
import PainPointsList from '../components/insights/PainPointsList';
import TopQuestions from '../components/insights/TopQuestions';
import type { InsightsSummary } from '../lib/api';
import { fetchInsights } from '../lib/api';
import type { ActiveCourse } from '../lib/course';

type InsightsPageProps = {
  activeCourse: ActiveCourse | null;
};

const InsightsPage: NextPage<InsightsPageProps> = ({ activeCourse }) => {
  const [insights, setInsights] = useState<InsightsSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadInsights = useCallback(
    async (courseId: string) => {
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
    },
    [],
  );

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
      {
        id: 'total-questions',
        label: 'Total Questions',
        value: insights.totals.questions.toLocaleString(),
      },
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

  const topQuestionLabels = useMemo(
    () => (insights ? insights.top_questions.map((item) => item.label) : []),
    [insights],
  );

  const topQuestionCounts = useMemo(
    () => (insights ? insights.top_questions.map((item) => item.count) : []),
    [insights],
  );

  const dailyVolumeLabels = useMemo(
    () => (insights ? insights.daily_volume.map((item) => item.date) : []),
    [insights],
  );
  const dailyVolumeValues = useMemo(
    () => (insights ? insights.daily_volume.map((item) => item.count) : []),
    [insights],
  );

  const confidenceLabels = useMemo(
    () => (insights ? insights.confidence_trend.map((item) => item.date) : []),
    [insights],
  );
  const confidenceValues = useMemo(
    () => (insights ? insights.confidence_trend.map((item) => item.confidence) : []),
    [insights],
  );

  const handleRefresh = () => {
    if (!activeCourse) return;
    loadInsights(activeCourse.id);
  };

  const courseLocked = !activeCourse;

  return (
    <section className="flex w-full flex-1 flex-col gap-6 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100 md:p-8">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-semibold text-slate-900 md:text-2xl">Course Insights</h1>
          <p className="text-sm text-slate-600">
            Spot engagement trends and escalation patterns for{' '}
            {activeCourse ? (
              <span className="font-semibold text-slate-800">{activeCourse.name}</span>
            ) : (
              'your course'
            )}
            .
          </p>
        </div>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={courseLocked || loading}
          className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition enabled:hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? 'Refreshing…' : 'Refresh data'}
        </button>
      </header>

      {courseLocked && (
        <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
          Choose a course to load its insights dashboard. We keep each class separated so instructors
          can act quickly on what matters.
        </div>
      )}

      {!courseLocked && error && (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700">
          {error}
        </div>
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
                  No question clusters yet. Encourage students to reach out so we can surface themes.
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
                  No activity plotted yet. Once questions start flowing, volume trends will show here.
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
                  Confidence data will appear after a few days of usage.
                </div>
              )}
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-800">Escalations</h2>
              <p className="mt-1 text-xs text-slate-500">
                Track which questions turned into instructor follow-up.
              </p>
              <div className="mt-4">
                <EscalationsTable rows={insights?.escalations ?? []} />
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-800">Emerging Pain Points</h2>
            <p className="mt-1 text-xs text-slate-500">
              Week-over-week change in student confusion by topic.
            </p>
            <div className="mt-4">
              <PainPointsList items={insights?.pain_points ?? []} />
            </div>
          </div>

          {insights && (
            <footer className="text-xs text-slate-400">
              Last refreshed {new Date(insights.last_updated).toLocaleString()}
            </footer>
          )}
        </>
      )}
    </section>
  );
};

export default InsightsPage;
