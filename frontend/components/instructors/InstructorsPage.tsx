'use client';

import { useEffect, useMemo, useState } from 'react';

import type { ActiveCourse } from '../../lib/course';
import { getInstructorToken } from '../../lib/instructorAuth';
import { instructorLogin, instructorLogout, runIngest } from '../../lib/instructors';
import ExportDataModal from '../insights/ExportDataModal';
import CourseAdminPanel from './CourseAdminPanel';
import InstructorLoginModal from './InstructorLoginModal';
import InsightsDashboard from '../insights/InsightsDashboard';

type Props = {
  activeCourse: ActiveCourse | null;
};

type Tab = 'insights' | 'admin';

export default function InstructorsPage({ activeCourse }: Props) {
  const [tab, setTab] = useState<Tab>('insights');
  const [token, setToken] = useState<string | null>(null);
  const [loginOpen, setLoginOpen] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginSubmitting, setLoginSubmitting] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [ingestState, setIngestState] = useState<'idle' | 'running' | 'error' | 'success'>('idle');
  const [ingestMessage, setIngestMessage] = useState<string | null>(null);

  useEffect(() => {
    const existing = getInstructorToken();
    setToken(existing);
    setLoginOpen(!existing);
  }, []);

  const canUseInsights = Boolean(activeCourse?.id);

  const subtitle = useMemo(() => {
    if (!token) return 'Sign in to view insights and manage courses.';
    if (!activeCourse) return 'Choose a course in the header to view course-specific insights and manage resources.';
    return `Signed in · Managing ${activeCourse.name}`;
  }, [activeCourse, token]);

  const handleLogin = async (username: string, password: string) => {
    setLoginSubmitting(true);
    setLoginError(null);
    try {
      await instructorLogin(username, password);
      const next = getInstructorToken();
      setToken(next);
      setLoginOpen(false);
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'Unable to sign in');
    } finally {
      setLoginSubmitting(false);
    }
  };

  const handleLogout = () => {
    instructorLogout();
    setToken(null);
    setLoginOpen(true);
  };

  const handleRunIngest = async () => {
    setIngestState('running');
    setIngestMessage(null);
    try {
      const result = await runIngest();
      setIngestState('success');
      setIngestMessage(`Indexed ${result?.counts?.docs ?? 0} docs, ${result?.counts?.chunks ?? 0} chunks.`);
    } catch (err) {
      setIngestState('error');
      setIngestMessage(err instanceof Error ? err.message : 'Ingestion failed');
    }
  };

  return (
    <>
      <InstructorLoginModal
        open={loginOpen}
        submitting={loginSubmitting}
        error={loginError}
        onSubmit={handleLogin}
        onClose={token ? () => setLoginOpen(false) : undefined}
      />

      <div className="flex w-full flex-1 flex-col gap-6">
        <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100 md:p-8">
          <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-6">
            <div className="flex flex-col gap-1">
              <h1 className="text-xl font-semibold text-slate-900 md:text-2xl">Instructors</h1>
              <p className="text-sm text-slate-600">{subtitle}</p>
              <p className="text-xs text-slate-500">
                Demo-only access control. Credentials are documented in the repo README.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {token ? (
                <>
                  <button
                    type="button"
                    onClick={() => setLoginOpen(true)}
                    className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                  >
                    Switch account
                  </button>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={() => setLoginOpen(true)}
                  className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-slate-700"
                >
                  Sign in
                </button>
              )}
            </div>
          </header>

          {token && (
            <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setTab('insights')}
                  className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
                    tab === 'insights'
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  Insights
                </button>
                <button
                  type="button"
                  onClick={() => setTab('admin')}
                  className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
                    tab === 'admin' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  Course admin
                </button>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => setExportOpen(true)}
                  className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                >
                  Export data
                </button>
                <button
                  type="button"
                  onClick={handleRunIngest}
                  disabled={ingestState === 'running'}
                  className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition enabled:hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {ingestState === 'running' ? 'Ingesting…' : 'Run ingest'}
                </button>
              </div>
            </div>
          )}

          {token && ingestMessage && (
            <div
              className={`mt-4 rounded-2xl border px-4 py-3 text-sm ${
                ingestState === 'error'
                  ? 'border-rose-200 bg-rose-50 text-rose-700'
                  : 'border-emerald-200 bg-emerald-50 text-emerald-800'
              }`}
            >
              {ingestMessage}
            </div>
          )}

          <ExportDataModal open={exportOpen} activeCourse={activeCourse} onClose={() => setExportOpen(false)} />

          {!token && (
            <div className="mt-6 rounded-3xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
              Sign in to access instructor tools.
            </div>
          )}
        </section>

        {token && tab === 'insights' && (
          <>
            {!canUseInsights ? (
              <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
                Choose a course in the header to load its insights dashboard.
              </div>
            ) : (
              <InsightsDashboard activeCourse={activeCourse} />
            )}
          </>
        )}

        {token && tab === 'admin' && <CourseAdminPanel activeCourse={activeCourse} />}
      </div>
    </>
  );
}
