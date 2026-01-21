'use client';

import { useEffect, useState } from 'react';

type Props = {
  open: boolean;
  submitting: boolean;
  error?: string | null;
  onClose?: () => void;
  onSubmit: (username: string, password: string) => void;
};

export default function InstructorLoginModal({ open, submitting, error, onClose, onSubmit }: Props) {
  const [username, setUsername] = useState('demo');
  const [password, setPassword] = useState('demo');

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/60 px-4 py-8">
      <div role="dialog" aria-modal="true" className="relative w-full max-w-lg rounded-3xl bg-white p-8 shadow-xl">
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="absolute right-4 top-4 rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close instructor login"
            disabled={submitting}
          >
            ✕
          </button>
        )}

        <div className="mb-6 flex flex-col gap-2">
          <h2 className="text-xl font-semibold text-slate-900">Instructor login</h2>
          <p className="text-sm text-slate-600">
            This login is for demonstration only. It is not production authentication and does not implement role-based
            access controls.
          </p>
        </div>

        {error && (
          <div className="mb-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">
            {error}
          </div>
        )}

        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit(username.trim(), password);
          }}
        >
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-800" htmlFor="instructor-username">
              Username
            </label>
            <input
              id="instructor-username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              disabled={submitting}
              className="lena-input"
              autoComplete="username"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-800" htmlFor="instructor-password">
              Password
            </label>
            <input
              id="instructor-password"
              value={password}
              type="password"
              onChange={(event) => setPassword(event.target.value)}
              disabled={submitting}
              className="lena-input"
              autoComplete="current-password"
            />
          </div>

          <div className="lena-alert-warn text-xs">
            Demo credentials are listed in the repository README.
          </div>

          <button
            type="submit"
            disabled={submitting || username.trim().length === 0 || password.length === 0}
            className="lena-button-primary w-full px-5 py-2 text-sm"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}
