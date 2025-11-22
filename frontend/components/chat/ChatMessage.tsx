import { CitationList } from './CitationList';
import { EscalationForm } from './EscalationForm';
import { ChatMessage as ChatMessageType } from './types';

type Props = {
    message: ChatMessageType;
    onToggleCitations: (id: string) => void;
    onFeedback: (id: string, choice: 'helpful' | 'not_helpful') => void;
    onEscalationRequest: (id: string) => void;
    onCancelEscalation: (id: string) => void;
    onSubmitEscalation: (id: string, name: string, email: string) => void;
    escalationOpenId: string | null;
    escalationSubmitting: boolean;
    escalationError: string | null;
    feedbackPendingIds: Set<string>;
};

export const ChatMessage = ({
    message,
    onToggleCitations,
    onFeedback,
    onEscalationRequest,
    onCancelEscalation,
    onSubmitEscalation,
    escalationOpenId,
    escalationSubmitting,
    escalationError,
    feedbackPendingIds,
}: Props) => {
    const formatTime = (value: Date) =>
        value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (message.role === 'user') {
        return (
            <div className="flex justify-end">
                <div className="max-w-[75%] rounded-2xl bg-slate-900 px-4 py-3 text-sm text-white shadow">
                    <p className="whitespace-pre-line">{message.content}</p>
                    <span className="mt-2 block text-xs text-slate-200/80">
                        You · {formatTime(message.createdAt)}
                    </span>
                </div>
            </div>
        );
    }

    const { response, showCitations, feedback, escalationStatus } = message;
    const citations = response.citations;
    const consentId = `escalation-consent-${message.id}`;

    return (
        <div className="flex justify-start">
            <div className="max-w-[75%] rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 shadow">
                <p className="whitespace-pre-line">{message.content}</p>
                <span className="mt-2 block text-xs text-slate-500">
                    LENA · {formatTime(message.createdAt)}
                </span>

                {citations.length > 0 && (
                    <div className="mt-3">
                        <button
                            type="button"
                            onClick={() => onToggleCitations(message.id)}
                            className="text-xs font-semibold text-slate-700 underline-offset-2 hover:underline"
                        >
                            {showCitations ? 'Hide citations' : 'Show citations'}
                        </button>
                        {showCitations && <CitationList citations={citations} />}
                    </div>
                )}

                <div className="mt-3 flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-500">Did this help?</span>
                    {feedback ? (
                        <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${feedback === 'helpful'
                                    ? 'bg-emerald-500 text-white'
                                    : 'bg-amber-500 text-white'
                                }`}
                        >
                            {feedback === 'helpful' ? 'Thanks for letting us know!' : 'Noted for review.'}
                        </span>
                    ) : (
                        <>
                            <button
                                type="button"
                                disabled={feedbackPendingIds.has(message.id)}
                                onClick={() => onFeedback(message.id, 'helpful')}
                                className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 transition hover:bg-slate-200"
                            >
                                Helpful
                            </button>
                            <button
                                type="button"
                                disabled={feedbackPendingIds.has(message.id)}
                                onClick={() => onFeedback(message.id, 'not_helpful')}
                                className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 transition hover:bg-slate-200"
                            >
                                Needs work
                            </button>
                        </>
                    )}
                </div>

                {response.escalation_suggested && escalationStatus !== 'submitted' && (
                    <div className="mt-4 rounded-2xl border border-indigo-200 bg-indigo-50 p-4 text-xs text-indigo-700">
                        {escalationOpenId === message.id ? (
                            <EscalationForm
                                messageId={message.id}
                                onSubmit={onSubmitEscalation}
                                onCancel={() => onCancelEscalation(message.id)}
                                isSubmitting={escalationSubmitting}
                                error={escalationError}
                            />
                        ) : escalationStatus === 'opted_out' ? (
                            <span className="text-indigo-500">No follow-up requested.</span>
                        ) : (
                            <div className="flex flex-wrap items-center gap-3">
                                <span className="font-semibold text-indigo-800">
                                    Need an instructor to take a look?
                                </span>
                                <button
                                    type="button"
                                    onClick={() => onEscalationRequest(message.id)}
                                    className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-indigo-600 shadow-sm transition hover:bg-indigo-100"
                                    aria-label="Open escalation form"
                                    aria-expanded={escalationOpenId === message.id}
                                    aria-controls={consentId}
                                >
                                    Yes, let&apos;s do it
                                </button>
                                <button
                                    type="button"
                                    onClick={() => onCancelEscalation(message.id)}
                                    className="text-xs font-semibold text-indigo-500 underline-offset-2 hover:underline"
                                >
                                    No thanks
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {escalationStatus === 'submitted' && (
                    <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-[11px] font-semibold text-emerald-700">
                        Instructor follow-up requested. Keep an eye on your inbox.
                    </div>
                )}
            </div>
        </div>
    );
};
