'use client';

import { useMemo, useState } from 'react';

import type { AskResponse } from '../lib/api';
import { askQuestion, submitFeedback } from '../lib/api';

type Message =
  | {
      id: string;
      role: 'user';
      text: string;
      timestamp: Date;
    }
  | {
      id: string;
      role: 'assistant';
      text: string;
      timestamp: Date;
      answer: AskResponse;
      showSources: boolean;
      question: string;
      feedback?: 'helpful' | 'not_helpful';
    };

function formatTimestamp(date: Date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function Chat() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackPending, setFeedbackPending] = useState<string | null>(null);

  const lastAnswer = useMemo(
    () => messages.findLast((message) => message.role === 'assistant'),
    [messages],
  );

  const handleSubmit = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    const question: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      text: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, question]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await askQuestion(trimmed);
      const assistant: Message = {
        id: response.question_id,
        role: 'assistant',
        text: response.answer,
        timestamp: new Date(),
        answer: response,
        showSources: true,
        question: trimmed,
      };
      setMessages((prev) => [...prev, assistant]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const toggleSources = (id: string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.role === 'assistant' && message.id === id
          ? { ...message, showSources: !message.showSources }
          : message,
      ),
    );
  };

  const handleFeedback = async (id: string, feedback: 'helpful' | 'not_helpful') => {
    const target = messages.find((message) => message.role === 'assistant' && message.id === id);
    if (!target || target.role !== 'assistant') return;

    const optimistic = messages.map((message) =>
      message.role === 'assistant' && message.id === id
        ? { ...message, feedback }
        : message,
    );
    setMessages(optimistic);
    setFeedbackPending(id);
    setError(null);

    try {
      await submitFeedback({
        question_id: id,
        helpful: feedback === 'helpful',
        question: target.question,
        answer: target.text,
        citations: target.answer.citations,
        confidence: target.answer.confidence,
      });
    } catch (err) {
      setMessages((prev) =>
        prev.map((message) =>
          message.role === 'assistant' && message.id === id
            ? { ...message, feedback: undefined }
            : message,
        ),
      );
      setError(err instanceof Error ? err.message : 'Unable to send feedback');
    } finally {
      setFeedbackPending(null);
    }
  };

  return (
    <div className="chat-card">
      <div className="chat-header">
        <div>
          <h1>LENA Pilot Assistant</h1>
          <p className="bubble-meta">
            Ask about course logistics, policies, and scheduling. Responses include citations so you can verify the source.
          </p>
        </div>
        {lastAnswer && lastAnswer.role === 'assistant' && (
          <span className="confidence">
            Confidence: {(lastAnswer.answer.confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>

      <div className="chat-history">
        {messages.length === 0 && (
          <div className="empty-state">
            Start the conversation with a question like &ldquo;When is Assignment 1 due?&rdquo;
          </div>
        )}
        {messages.map((message) => (
          <div key={message.id} className={`bubble ${message.role}`}>
            <div>{message.text}</div>
            <div className="bubble-meta">
              {message.role === 'assistant' ? 'LENA' : 'You'} · {formatTimestamp(message.timestamp)}
            </div>
            {message.role === 'assistant' && (
              <>
                <div className="bubble-actions">
                  <button
                    className="bubble-button"
                    onClick={() => toggleSources(message.id)}
                    type="button"
                  >
                    {message.showSources ? 'Hide sources' : 'Show sources'}
                  </button>
                  <button
                    className="bubble-button"
                    onClick={() => handleFeedback(message.id, 'helpful')}
                    type="button"
                    disabled={feedbackPending === message.id}
                  >
                    👍 Helpful
                  </button>
                  <button
                    className="bubble-button"
                    onClick={() => handleFeedback(message.id, 'not_helpful')}
                    type="button"
                    disabled={feedbackPending === message.id}
                  >
                    👎 Not helpful
                  </button>
                </div>
                {message.showSources && (
                  <div className="sources">
                    <div>Sources cited:</div>
                    <ul>
                      {message.answer.citations.map((citation, idx) => (
                        <li key={`${message.id}-citation-${idx}`}>
                          <strong>{citation.title}</strong>
                          {citation.section && <span> — {citation.section}</span>}
                          <span>{` (${citation.source_path})`}</span>
                        </li>
                      ))}
                    </ul>
                    {message.answer.escalation_suggested && (
                      <div className="bubble-meta">
                        Confidence is low; consider escalating to instructor support.
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </div>

      <div className="composer">
        <textarea
          placeholder="Ask about course policies, due dates, or resources..."
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              handleSubmit();
            }
          }}
          disabled={loading}
        />
        <button type="button" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Thinking…' : 'Ask LENA'}
        </button>
      </div>

      {error && (
        <div className="bubble-meta" role="alert">
          Unable to reach the assistant: {error}
        </div>
      )}
    </div>
  );
}
