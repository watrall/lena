// EscalationsTable.tsx – tabular view of escalation requests and delivery status.
interface EscalationRow {
  question: string;
  student: string;
  submitted_at: string;
  delivered: boolean;
}

interface EscalationsTableProps {
  rows: EscalationRow[];
}

export default function EscalationsTable({ rows }: EscalationsTableProps) {
  if (rows.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
        No escalations yet. Once a student requests follow-up, the request will pop up here.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 shadow-sm">
      <table className="w-full text-left text-sm text-slate-700">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 font-semibold">Question</th>
            <th className="px-4 py-3 font-semibold">Student</th>
            <th className="px-4 py-3 font-semibold">Submitted</th>
            <th className="px-4 py-3 font-semibold">Delivered</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={`${row.question}-${index}`}
              className={`border-t border-slate-100 ${index % 2 === 0 ? 'bg-white' : 'bg-slate-50/60'}`}
            >
              <td className="px-4 py-3 text-slate-800">{row.question}</td>
              <td className="px-4 py-3">{row.student}</td>
              <td className="px-4 py-3 text-slate-500">
                {new Date(row.submitted_at).toLocaleDateString()}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
                    row.delivered
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {row.delivered ? 'Delivered' : 'Pending'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
