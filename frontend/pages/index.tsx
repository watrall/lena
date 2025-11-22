// index.tsx – main chat surface for course-scoped questions, citations, and escalation.
import { Fragment, useEffect, useMemo, useRef, useState } from 'react';

import type { NextPage } from 'next';

import { ChatInput } from '../components/chat/ChatInput';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatMessage as ChatMessageType } from '../components/chat/types';
import { askQuestion, requestEscalation, submitFeedback } from '../lib/api';
import type { ActiveCourse } from '../lib/course';

type PageProps = {
  activeCourse: ActiveCourse | null;
};

type ToastState =
  | {
    type: 'success' | 'error';
    message: string;
  }
  | null;

const ChatPage: NextPage<PageProps> = ({ activeCourse }) => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackPendingIds, setFeedbackPendingIds] = useState<Set<string>>(() => new Set());
  const [escalationOpenId, setEscalationOpenId] = useState<string | null>(null);
  const [escalationSubmitting, setEscalationSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);
  const [escalationError, setEscalationError] = useState<string | null>(null);

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
    setMessages([]);
    setInput('');
    setToast(null);
    setEscalationOpenId(null);
    setEscalationError(null);
  }, [activeCourse?.id]);

  const lastAssistantMessage = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const candidate = messages[i];
      if (candidate.role === 'assistant') {
        return candidate;
      }
    }
    return undefined;
  }, [messages]);

  const handleSubmit = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    if (!activeCourse) {
      setToast({ type: 'error', message: 'Pick a course first so I know how to answer.' });
      return;
    }

    const userMessage: ChatMessageType = {
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

      const assistantMessage: ChatMessageType = {
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
    if (!activeCourse) return;
    const target = messages.find(
      (message) => message.role === 'assistant' && message.id === messageId,
    );
    if (!target || target.role !== 'assistant') return;
    if (feedbackPendingIds.has(messageId)) return;

    setFeedbackPendingIds((current) => {
      const next = new Set(current);
      next.add(messageId);
      return next;
    });
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
        question: target.questionText,
        answer: target.response.answer,
        citations: target.response.citations,
        confidence: target.response.confidence,
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
      setFeedbackPendingIds((current) => {
        const next = new Set(current);
        next.delete(messageId);
        return next;
      });
    }
  };

  const handleEscalationRequest = (messageId: string) => {
    const target = messages.find(
      (message) => message.role === 'assistant' && message.id === messageId,
    );
    if (!target || target.role !== 'assistant') return;
    setEscalationOpenId(messageId);
    setEscalationError(null);
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
    setEscalationError(null);
  };

  const submitEscalation = async (messageId: string, name: string, email: string) => {
    if (!activeCourse) return;
    const target = messages.find(
      (message) => message.role === 'assistant' && message.id === messageId,
    );
    if (!target || target.role !== 'assistant') return;

    setEscalationError(null);
    setEscalationSubmitting(true);
    setError(null);

    try {
      await requestEscalation({
        question_id: messageId,
        question: target.questionText,
        student_name: name,
        student_email: email,
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
      setEscalationError(null);
      setToast({ type: 'success', message: 'Thanks. We flagged this for your instructor.' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Could not reach the instructor queue.';
      setEscalationError(message);
      setToast({ type: 'error', message });
    } finally {
      setEscalationSubmitting(false);
    }
  };

  const courseLocked = !activeCourse;

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

            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onToggleCitations={toggleCitations}
                onFeedback={handleFeedback}
                onEscalationRequest={handleEscalationRequest}
                onCancelEscalation={handleCancelEscalation}
                onSubmitEscalation={submitEscalation}
                escalationOpenId={escalationOpenId}
                escalationSubmitting={escalationSubmitting}
                escalationError={escalationError}
                feedbackPendingIds={feedbackPendingIds}
              />
            ))}
            <div ref={transcriptEndRef} />
          </div>
        </div>

        <footer className="mt-6 border-t border-slate-100 pt-6">
          {error && (
            <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}
          <ChatInput
            input={input}
            setInput={setInput}
            onSubmit={handleSubmit}
            loading={loading}
            disabled={courseLocked}
            inputRef={inputRef}
            placeholder={
              courseLocked
                ? 'Choose a course before you start typing.'
                : `Ask something for ${activeCourse?.name ?? 'your course'}`
            }
          />
          <p className="mt-2 text-xs text-slate-400">
            Responses stay within your course context and log feedback for quality checks.
          </p>
        </footer>
      </section>

      {toast && (
        <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 transform">
          <div
            role="status"
            aria-live={toast.type === 'error' ? 'assertive' : 'polite'}
            className={`rounded-full px-4 py-2 text-sm font-semibold shadow ${toast.type === 'success' ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white'
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
