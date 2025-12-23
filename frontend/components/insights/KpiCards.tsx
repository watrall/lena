import type { ReactNode } from 'react';

interface KpiMetric {
  id: string;
  label: string;
  value: ReactNode;
  description?: string;
}

interface KpiCardsProps {
  metrics: KpiMetric[];
  onRefresh?: () => void;
  refreshing?: boolean;
}

export default function KpiCards({ metrics, onRefresh, refreshing }: KpiCardsProps) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-900">Course Pulse</h2>
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600 transition enabled:hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        )}
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <article
            key={metric.id}
            className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-5 text-sm text-slate-700 shadow-sm"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">
              {metric.label}
            </p>
            <div className="mt-3 text-2xl font-semibold text-slate-900">{metric.value}</div>
            {metric.description && <p className="mt-2 text-xs text-slate-500">{metric.description}</p>}
          </article>
        ))}
      </div>
    </div>
  );
}
