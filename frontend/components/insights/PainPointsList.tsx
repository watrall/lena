interface PainPoint {
  label: string;
  change: number;
}

interface PainPointsListProps {
  items: PainPoint[];
}

function formatChange(value: number) {
  const sign = value > 0 ? '+' : '';
  return `${sign}${Math.round(value * 100)}%`;
}

export default function PainPointsList({ items }: PainPointsListProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
        No emerging pain points right now. Keep an eye here for spikes in student confusion.
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {items.map((item) => {
        const isUp = item.change > 0;
        return (
          <li
            key={item.label}
            className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm"
          >
            <span className="font-medium text-slate-800">{item.label}</span>
            <span
              className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
                isUp ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
              }`}
            >
              {formatChange(item.change)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
