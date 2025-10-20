// insights.tsx – lightweight stub that will evolve into the course insights dashboard.
import { useEffect, useState } from 'react';

import type { InsightsSummary } from '../lib/api';
import { fetchInsights } from '../lib/api';
import type { ActiveCourse } from '../lib/course';

type InsightsPageProps = {
  activeCourse: ActiveCourse | null;
};

export default function InsightsPage({ activeCourse }: InsightsPageProps) {
  const [insights, setInsights] = useState<InsightsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeCourse) {
      setInsights(null);
      setError(null);
      return;
    }

    fetchInsights(activeCourse.id)
      .then(setInsights)
      .catch((err) => setError(err instanceof Error ? err.message : 'Unable to load insights'));
  }, [activeCourse]);

  return (
    <div className="chat-card">
      <div className="chat-header">
        <div>
          <h1>Pilot Insights</h1>
          <p className="bubble-meta">
            Monitor engagement, confidence, and feedback trends to decide when to escalate policy updates.
          </p>
        </div>
      </div>

      {insights ? (
        <div className="insights-grid">
          <div className="insight-tile">
            <h2>{insights.total_questions}</h2>
            <span>Total questions asked</span>
          </div>
          <div className="insight-tile">
            <h2>{Math.round(insights.average_confidence * 100)}%</h2>
            <span>Average confidence</span>
          </div>
          <div className="insight-tile">
            <h2>{Math.round(insights.helpful_rate * 100)}%</h2>
            <span>Helpful feedback rate</span>
          </div>
          {typeof insights.total_feedback === 'number' && (
            <div className="insight-tile">
              <h2>{insights.total_feedback}</h2>
              <span>Total feedback signals</span>
            </div>
          )}
          <div className="bubble-meta">
            Last updated {new Date(insights.last_updated).toLocaleString()}
          </div>
        </div>
      ) : (
        <div className="empty-state">Loading insights…</div>
      )}

      {error && (
        <div className="bubble-meta" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}
