import { Citation } from '../../lib/api';

type Props = {
    citations: Citation[];
};

export const CitationList = ({ citations }: Props) => {
    return (
        <ul className="mt-2 space-y-2 rounded-2xl border border-slate-200 bg-white p-3">
            {citations.map((citation, index) => (
                <li key={`${citation.source_path}-${index}`} className="text-xs text-slate-600">
                    <span className="font-semibold text-slate-700">{citation.title}</span>
                    {citation.section && (
                        <span className="ml-1 text-slate-500">· {citation.section}</span>
                    )}
                    <div className="text-slate-400">{citation.source_path}</div>
                </li>
            ))}
        </ul>
    );
};
