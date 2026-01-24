'use client';

import { useEffect, useMemo, useState } from 'react';

import type { ActiveCourse } from '../../lib/course';
import { getInstructorToken } from '../../lib/instructorAuth';
import { fetchEscalationSummary, instructorLogin, instructorLogout, runIngest } from '../../lib/instructors';
import ExportDataModal from '../insights/ExportDataModal';
import CourseAdminPanel from './CourseAdminPanel';
import InstructorLoginModal from './InstructorLoginModal';
import InsightsDashboard from '../insights/InsightsDashboard';
import EscalationsInbox from './EscalationsInbox';

type Props = {
  activeCourse: ActiveCourse | null;
};

type Tab = 'insights' | 'escalations' | 'admin';
type EscalationDelta = { newDelta?: number; unresolvedDelta?: number; newAbsolute?: number; unresolvedAbsolute?: number };

export default function InstructorsPage({ activeCourse }: Props) {
  const [tab, setTab] = useState<Tab>('insights');
  const [token, setToken] = useState<string | null>(null);
  const [escalationCount, setEscalationCount] = useState<{ unresolved: number; new: number } | null>(null);
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
  const canUseEscalations = Boolean(activeCourse?.id);

  const refreshEscalationCounts = async (courseId: string) => {
    try {
      const summary = await fetchEscalationSummary(courseId);
      setEscalationCount({ unresolved: summary.unresolved, new: summary.new });
    } catch {
      setEscalationCount(null);
    }
  };

  useEffect(() => {
    if (!token || !activeCourse?.id) {
      setEscalationCount(null);
      return;
    }
    void refreshEscalationCounts(activeCourse.id);
  }, [activeCourse?.id, token]);

  const applyEscalationDelta = (delta?: EscalationDelta) => {
    if (!delta) {
      if (activeCourse?.id) void refreshEscalationCounts(activeCourse.id);
      return;
    }
    setEscalationCount((prev) => {
      const current = prev ?? { unresolved: 0, new: 0 };
      let nextNew = current.new;
      let nextUnresolved = current.unresolved;
      if (typeof delta.newAbsolute === 'number') nextNew = delta.newAbsolute;
      else if (typeof delta.newDelta === 'number') nextNew = Math.max(0, nextNew + delta.newDelta);
      if (typeof delta.unresolvedAbsolute === 'number') nextUnresolved = delta.unresolvedAbsolute;
      else if (typeof delta.unresolvedDelta === 'number') nextUnresolved = Math.max(0, nextUnresolved + delta.unresolvedDelta);
      return { new: nextNew, unresolved: nextUnresolved };
    });
  };

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
        <section className="lena-card lena-card-padding">
          <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-6">
            <div className="flex flex-col gap-1">
              <h1 className="lena-title">Instructors</h1>
              <p className="lena-subtitle">{subtitle}</p>
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
                    className="lena-button-secondary"
                  >
                    Switch account
                  </button>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="lena-button-secondary"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={() => setLoginOpen(true)}
                  className="lena-button-primary"
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
                  className={`lena-tab ${tab === 'insights' ? 'lena-tab-active' : 'lena-tab-inactive'}`}
                >
                  Insights
                </button>
                <button
                  type="button"
                  onClick={() => setTab('escalations')}
                  className={`lena-tab ${tab === 'escalations' ? 'lena-tab-active' : 'lena-tab-inactive'}`}
                >
                  <span className="flex items-center gap-2">
                    Escalations
                    {canUseEscalations && escalationCount && escalationCount.new > 0 && (
                      <span
                        className="rounded-full bg-rose-600 px-2 py-0.5 text-[11px] font-semibold text-white"
                        title={`${escalationCount.new} new escalations`}
                      >
                        {escalationCount.new}
                      </span>
                    )}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setTab('admin')}
                  className={`lena-tab ${tab === 'admin' ? 'lena-tab-active' : 'lena-tab-inactive'}`}
                >
                  Course admin
                </button>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => setExportOpen(true)}
                  className="lena-button-secondary"
                >
                  Export data
                </button>
                <button
                  type="button"
                  onClick={handleRunIngest}
                  disabled={ingestState === 'running'}
                  className="lena-button-primary"
                >
                  {ingestState === 'running' ? 'Ingesting…' : 'Run ingest'}
                </button>
              </div>
            </div>
          )}

          {token && ingestMessage && (
            <div
              className={`mt-4 ${ingestState === 'error' ? 'lena-alert-error' : 'lena-alert-success'}`}
            >
              {ingestMessage}
            </div>
          )}

          <ExportDataModal open={exportOpen} activeCourse={activeCourse} onClose={() => setExportOpen(false)} />

          {!token && (
            <div className="mt-6 lena-callout">
              Sign in to access instructor tools.
            </div>
          )}
        </section>

        {token && tab === 'insights' && (
          <>
            {!canUseInsights ? (
              <div className="lena-callout">
                Choose a course in the header to load its insights dashboard.
              </div>
            ) : (
              <InsightsDashboard activeCourse={activeCourse} />
            )}
          </>
        )}

        {token && tab === 'escalations' && (
          <>
            {!activeCourse ? (
              <div className="lena-callout">
                Choose a course in the header to load its escalation inbox.
              </div>
            ) : (
              <EscalationsInbox
                activeCourse={activeCourse}
                onCountsChange={(delta) => applyEscalationDelta(delta)}
              />
            )}
          </>
        )}

        {token && tab === 'admin' && <CourseAdminPanel activeCourse={activeCourse} />}
      </div>
    </>
  );
}
