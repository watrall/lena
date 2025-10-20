// index.tsx – main chat surface for course-scoped questions, citations, and escalation.
import { Fragment, useEffect, useMemo, useRef, useState } from 'react';

import type { NextPage } from 'next';

import type { AskResponse, Citation } from '../lib/api';
import { askQuestion, requestEscalation, submitFeedback } from '../lib/api';
import type { ActiveCourse } from '../lib/course';

type PageProps = {
  activeCourse: ActiveCourse | null;
};

type ChatMessage =
  | {
      id: string;
      role: 'user';
      content: string;
      createdAt: Date;
    }
  | {
      id: string;
      role: 'assistant';
      content: string;
      createdAt: Date;
      response: AskResponse;
      showCitations: boolean;
      feedback?: 'helpful' | 'not_helpful';
      escalationStatus?: 'suggested' | 'opted_out' | 'submitted';
      questionText: string;
    };

type ToastState =
  | {
      type: 'success' | 'error';
      message: string;
    }
  | null;

const ChatPage: NextPage<PageProps> = ({ activeCourse }) => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackPending, setFeedbackPending] = useState<string | null>(null);
  const [escalationOpenId, setEscalationOpenId] = useState<string | null>(null);
  const [escalationSubmitting, setEscalationSubmitting] = useState(false);
  const [studentName, setStudentName] = useState('');
  const [studentEmail, setStudentEmail] = useState('');
  const [toast, setToast] = useState<ToastState>(null);

  const transcriptEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    if (toast) {
      const timeout = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timeout);
    }
    return undefined;
  }, [toast]);

  useEffect(() => {
    if (!activeCourse) {
      setMessages([]);
      setInput('');
    }
  }, [activeCourse]);

  const lastAssistantMessage = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const candidate = messages[i];
      if (candidate.role === 'assistant') {
        return candidate;
      }
    }
    return undefined;
  }, [messages]);

  const formatTime = (value: Date) =>
    value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const handleSubmit = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    if (!activeCourse) {
      setToast({ type: 'error', message: 'Pick a course first so I know how to answer.' });
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
      createdAt: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await askQuestion({ question: trimmed, courseId: activeCourse.id });

      const assistantMessage: ChatMessage = {
        id: response.question_id,
        role: 'assistant',
        content: response.answer,
        createdAt: new Date(),
        response,
        showCitations: response.citations.length > 0,
        escalationStatus: response.escalation_suggested ? 'suggested' : undefined,
        questionText: trimmed,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong. Try again.';
      setError(message);
      setToast({ type: 'error', message });
      setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id));
      setInput(trimmed);
      inputRef.current?.focus();
    } finally {
      setLoading(false);
    }
  };

  const toggleCitations = (id: string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.role === 'assistant' && message.id === id
          ? { ...message, showCitations: !message.showCitations }
          : message,
      ),
    );
  };

  const handleFeedback = async (messageId: string, choice: 'helpful' | 'not_helpful') => {
    if (feedbackPending || !activeCourse) return;
    const target = messages.find(
      (message) => message.role === 'assistant' && message.id === messageId,
    );
    if (!target || target.role !== 'assistant') return;

    setFeedbackPending(messageId);
    setMessages((prev) =>
      prev.map((message) =>
        message.role === 'assistant' && message.id === messageId ? { ...message, feedback: choice } : message,
      ),
    );
    setError(null);

    try {
      await submitFeedback({
        question_id: messageId,
        helpful: choice === 'helpful',
        courseId: activeCourse.id,
      });
      setToast({ type: 'success', message: 'Thanks for the feedback.' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Could not send feedback.';
      setMessages((prev) =>
        prev.map((msg) =>
          msg.role === 'assistant' && msg.id === messageId ? { ...msg, feedback: undefined } : msg,
        ),
      );
      setToast({ type: 'error', message });
    } finally {
      setFeedbackPending(null);
    }
  };

  const handleEscalationRequest = (messageId: string) => {
    const target = messages.find(
      (message) => message.role === 'assistant' && message.id === messageId,
    );
    if (!target || target.role !== 'assistant') return;
    setEscalationOpenId(messageId);
    setStudentName('');
    setStudentEmail('');
  };

  const handleCancelEscalation = (messageId: string) => {
    setEscalationOpenId(null);
    setMessages((prev) =>
      prev.map((message) =>
        message.role === 'assistant' && message.id === messageId
          ? { ...message, escalationStatus: 'opted_out' }
          : message,
      ),
    );
  };

  const submitEscalation = async (messageId: string) => {
    if (!activeCourse) return;
    const target = messages.find(
      (message) => message.role === 'assistant' && message.id === messageId,
    );
    if (!target || target.role !== 'assistant') return;

    const trimmedName = studentName.trim();
    const trimmedEmail = studentEmail.trim();

    if (!trimmedName || !trimmedEmail) {
      setToast({ type: 'error', message: 'Add your name and email so the instructor can reply.' });
      return;
    }

    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail);
    if (!emailValid) {
      setToast({ type: 'error', message: 'That email looks off. Give it another look.' });
      return;
    }

    setEscalationSubmitting(true);
    setError(null);

    try {
      await requestEscalation({
        question_id: messageId,
        question: target.questionText,
        student_name: trimmedName,
        student_email: trimmedEmail,
        courseId: activeCourse.id,
      });

      setMessages((prev) =>
        prev.map((message) =>
          message.role === 'assistant' && message.id === messageId
            ? { ...message, escalationStatus: 'submitted' }
            : message,
        ),
      );
      setEscalationOpenId(null);
      setStudentName('');
      setStudentEmail('');
      setToast({ type: 'success', message: 'Thanks. We flagged this for your instructor.' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Could not reach the instructor queue.';
      setToast({ type: 'error', message });
    } finally {
      setEscalationSubmitting(false);
    }
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  const courseLocked = !activeCourse;
  const canSend = !courseLocked && input.trim().length > 0 && !loading;

  return (
    <Fragment>
      <section className="flex w-full flex-1 flex-col rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100 md:p-8">
        <header className="flex flex-col gap-2 border-b border-slate-100 pb-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold text-slate-900 md:text-2xl">Chat with LENA</h1>
              <p className="text-sm text-slate-600">
                Ask about policies, schedules, or coursework. You&apos;ll always see the sources.
              </p>
            </div>
            {lastAssistantMessage && lastAssistantMessage.role === 'assistant' && (
              <span className="rounded-full bg-slate-900/5 px-4 py-2 text-xs font-semibold text-slate-600">
                Confidence {Math.round(lastAssistantMessage.response.confidence * 100)}%
              </span>
            )}
          </div>
          {courseLocked && (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              Choose a course to unlock the chat. Use the button in the header to get started.
            </div>
          )}
        </header>

        <div className="mt-6 flex-1 overflow-y-auto">
          <div className="flex min-h-[320px] flex-col gap-4">
            {messages.length === 0 && (
              <div className="flex flex-1 items-center justify-center rounded-3xl border border-dashed border-slate-200 bg-slate-50 px-6 py-12 text-center text-sm text-slate-500">
                {courseLocked
                  ? 'Select your course to start a conversation.'
                  : 'Ask something like “When is the next assignment due?”'}
              </div>
            )}

            {messages.map((message) => {
              if (message.role === 'user') {
                return (
                  <div key={message.id} className="flex justify-end">
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
              const citations: Citation[] = response.citations;

              return (
                <div key={message.id} className="flex justify-start">
                  <div className="max-w-[75%] rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 shadow">
                    <p className="whitespace-pre-line">{message.content}</p>
                    <span className="mt-2 block text-xs text-slate-500">
                      LENA · {formatTime(message.createdAt)}
                    </span>

                    {citations.length > 0 && (
                      <div className="mt-3">
                        <button
                          type="button"
                          onClick={() => toggleCitations(message.id)}
                          className="text-xs font-semibold text-slate-700 underline-offset-2 hover:underline"
                        >
                          {showCitations ? 'Hide citations' : 'Show citations'}
                        </button>
                        {showCitations && (
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
                        )}
                      </div>
                    )}

                    <div className="mt-3 flex items-center gap-2">
                      <span className="text-xs font-medium text-slate-500">Did this help?</span>
                      <button
                        type="button"
                        disabled={feedbackPending === message.id}
                        onClick={() => handleFeedback(message.id, 'helpful')}
                        className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                          feedback === 'helpful'
                            ? 'bg-emerald-500 text-white'
                            : 'bg-white text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        Helpful
                      </button>
                      <button
                        type="button"
                        disabled={feedbackPending === message.id}
                        onClick={() => handleFeedback(message.id, 'not_helpful')}
                        className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                          feedback === 'not_helpful'
                            ? 'bg-amber-500 text-white'
                            : 'bg-white text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        Needs work
                      </button>
                    </div>

                    {response.escalation_suggested && escalationStatus !== 'submitted' && (
                      <div className="mt-4 rounded-2xl border border-indigo-200 bg-indigo-50 p-4 text-xs text-indigo-700">
                        {escalationOpenId === message.id ? (
                          <div className="space-y-3">
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
                                />
                              </label>
                            </div>
                            <div className="flex flex-wrap items-center gap-3">
                              <button
                                type="button"
                                onClick={() => submitEscalation(message.id)}
                                disabled={escalationSubmitting}
                                className="rounded-full bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition enabled:hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-indigo-300"
                              >
                                {escalationSubmitting ? 'Sending…' : 'Send to instructor'}
                              </button>
                              <button
                                type="button"
                                onClick={() => setEscalationOpenId(null)}
                                className="text-xs font-semibold text-indigo-500 underline-offset-2 hover:underline"
                              >
                                Back
                              </button>
                            </div>
                          </div>
                        ) : escalationStatus === 'opted_out' ? (
                          <span className="text-indigo-500">No follow-up requested.</span>
                        ) : (
                          <div className="flex flex-wrap items-center gap-3">
                            <span className="font-semibold text-indigo-800">
                              Need an instructor to take a look?
                            </span>
                            <button
                              type="button"
                              onClick={() => handleEscalationRequest(message.id)}
                              className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-indigo-600 shadow-sm transition hover:bg-indigo-100"
                            >
                              Yes, let&apos;s do it
                            </button>
                            <button
                              type="button"
                              onClick={() => handleCancelEscalation(message.id)}
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
            })}
            <div ref={transcriptEndRef} />
          </div>
        </div>

        <footer className="mt-6 border-t border-slate-100 pt-6">
          {error && (
            <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}
          <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <label className="flex-1">
              <span className="sr-only">Ask a question</span>
              <textarea
                ref={inputRef}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  courseLocked
                    ? 'Choose a course before you start typing.'
                    : `Ask something for ${activeCourse?.name ?? 'your course'}`
                }
                rows={3}
                className="w-full resize-y rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-800 shadow-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200 disabled:cursor-not-allowed disabled:bg-slate-100"
                disabled={courseLocked || loading}
              />
            </label>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!canSend}
                className="rounded-full bg-slate-900 px-6 py-3 text-sm font-semibold text-white transition enabled:hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {loading ? 'Sending…' : 'Send'}
              </button>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Responses stay within your course context and log feedback for quality checks.
          </p>
        </footer>
      </section>

      {toast && (
        <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 transform">
          <div
            className={`rounded-full px-4 py-2 text-sm font-semibold shadow ${
              toast.type === 'success'
                ? 'bg-emerald-600 text-white'
                : 'bg-rose-600 text-white'
            }`}
          >
            {toast.message}
          </div>
        </div>
      )}
    </Fragment>
  );
};

export default ChatPage;
