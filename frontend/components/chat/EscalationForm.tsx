import { useState } from 'react';

type Props = {
    messageId: string;
    onSubmit: (messageId: string, name: string, email: string) => void;
    onCancel: () => void;
    isSubmitting: boolean;
    error: string | null;
};

export const EscalationForm = ({ messageId, onSubmit, onCancel, isSubmitting, error }: Props) => {
    const [studentName, setStudentName] = useState('');
    const [studentEmail, setStudentEmail] = useState('');
    const [localError, setLocalError] = useState<string | null>(null);

    const handleSubmit = () => {
        const trimmedName = studentName.trim();
        const trimmedEmail = studentEmail.trim();

        if (!trimmedName || !trimmedEmail) {
            setLocalError('Add your name and email so the instructor can reply.');
            return;
        }

        const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail);
        if (!emailValid) {
            setLocalError('That email looks off. Give it another look.');
            return;
        }

        setLocalError(null);
        onSubmit(messageId, trimmedName, trimmedEmail);
    };

    const consentId = `escalation-consent-${messageId}`;
    const errorId = `escalation-error-${messageId}`;
    const showEscalationError = Boolean(error || localError);
    const displayError = error || localError;

    return (
        <div className="space-y-3" role="form" aria-labelledby={consentId}>
            <p className="font-semibold text-indigo-800">
                Want an instructor to follow up? Drop your info and we&apos;ll pass it along.
            </p>
            <div className="grid gap-3 md:grid-cols-2">
                <label className="flex flex-col gap-1 text-left">
                    <span className="text-[11px] uppercase tracking-wide text-indigo-500">
                        Name
                    </span>
                    <input
                        type="text"
                        value={studentName}
                        onChange={(event) => setStudentName(event.target.value)}
                        className="rounded-lg border border-indigo-200 px-3 py-2 text-sm text-slate-800 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        placeholder="Jordan Smith"
                        aria-describedby={`${consentId}${showEscalationError ? ` ${errorId}` : ''}`}
                        aria-invalid={showEscalationError && !studentName.trim()}
                    />
                </label>
                <label className="flex flex-col gap-1 text-left">
                    <span className="text-[11px] uppercase tracking-wide text-indigo-500">
                        Email
                    </span>
                    <input
                        type="email"
                        value={studentEmail}
                        onChange={(event) => setStudentEmail(event.target.value)}
                        className="rounded-lg border border-indigo-200 px-3 py-2 text-sm text-slate-800 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        placeholder="you@example.edu"
                        aria-describedby={`${consentId}${showEscalationError ? ` ${errorId}` : ''}`}
                        aria-invalid={showEscalationError && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(studentEmail)}
                        onKeyDown={(event) => {
                            if (event.key === 'Enter' && !event.shiftKey) {
                                event.preventDefault();
                                handleSubmit();
                            }
                        }}
                    />
                </label>
            </div>
            <p id={consentId} className="text-[11px] text-indigo-500">
                Your name and email will be shared with your instructor to follow up on this question.
            </p>
            {showEscalationError && (
                <div
                    id={errorId}
                    role="alert"
                    className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-[11px] text-rose-700"
                >
                    {displayError}
                </div>
            )}
            <div className="flex flex-wrap items-center gap-3">
                <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                    className="rounded-full bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition enabled:hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-indigo-300"
                    aria-label="Submit escalation request"
                >
                    {isSubmitting ? 'Sending…' : 'Send to instructor'}
                </button>
                <button
                    type="button"
                    onClick={onCancel}
                    className="text-xs font-semibold text-indigo-500 underline-offset-2 hover:underline"
                    aria-label="Close escalation form"
                >
                    Back
                </button>
            </div>
        </div>
    );
};
