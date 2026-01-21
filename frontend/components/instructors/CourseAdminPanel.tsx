'use client';

import { useEffect, useMemo, useState } from 'react';

import type { ActiveCourse } from '../../lib/course';
import {
  addCourseLink,
  createInstructorCourse,
  deleteCourseResource,
  deleteInstructorCourse,
  listCourseResources,
  listInstructorCourses,
  uploadCourseResource,
} from '../../lib/instructors';
import { setActiveCourse } from '../../lib/course';

type Props = {
  activeCourse: ActiveCourse | null;
};

type LoadState = 'idle' | 'loading' | 'error' | 'success';

export default function CourseAdminPanel({ activeCourse }: Props) {
  const [courses, setCourses] = useState<Array<{ id: string; name: string; code?: string | null; term?: string | null }>>([]);
  const [courseLoad, setCourseLoad] = useState<LoadState>('idle');
  const [courseError, setCourseError] = useState<string | null>(null);

  const [newId, setNewId] = useState('');
  const [newName, setNewName] = useState('');
  const [newCode, setNewCode] = useState('');
  const [newTerm, setNewTerm] = useState('');

  const [resources, setResources] = useState<any[]>([]);
  const [resourceLoad, setResourceLoad] = useState<LoadState>('idle');
  const [resourceError, setResourceError] = useState<string | null>(null);

  const [uploading, setUploading] = useState(false);
  const [linkUrl, setLinkUrl] = useState('');
  const [linkTitle, setLinkTitle] = useState('');
  const [linkSubmitting, setLinkSubmitting] = useState(false);

  const selectedCourseId = activeCourse?.id || '';

  const selectedCourse = useMemo(() => courses.find((c) => c.id === selectedCourseId) || null, [courses, selectedCourseId]);

  const refreshCourses = async () => {
    setCourseLoad('loading');
    setCourseError(null);
    try {
      const data = await listInstructorCourses();
      setCourses(data);
      setCourseLoad('success');
    } catch (err) {
      setCourseLoad('error');
      setCourseError(err instanceof Error ? err.message : 'Unable to load courses');
    }
  };

  const refreshResources = async (courseId: string) => {
    setResourceLoad('loading');
    setResourceError(null);
    try {
      const data = await listCourseResources(courseId);
      setResources(data);
      setResourceLoad('success');
    } catch (err) {
      setResourceLoad('error');
      setResourceError(err instanceof Error ? err.message : 'Unable to load resources');
    }
  };

  useEffect(() => {
    refreshCourses();
  }, []);

  useEffect(() => {
    setResources([]);
    setResourceError(null);
    setResourceLoad('idle');
    if (!selectedCourseId) return;
    refreshResources(selectedCourseId);
  }, [selectedCourseId]);

  const handleCreateCourse = async () => {
    setCourseError(null);
    const id = newId.trim();
    const name = newName.trim();
    if (!id || !name) return;
    try {
      await createInstructorCourse({
        id,
        name,
        code: newCode.trim() || null,
        term: newTerm.trim() || null,
      });
      setNewId('');
      setNewName('');
      setNewCode('');
      setNewTerm('');
      await refreshCourses();
      setActiveCourse({ id, name, code: newCode.trim() || null, term: newTerm.trim() || null });
    } catch (err) {
      setCourseError(err instanceof Error ? err.message : 'Unable to create course');
    }
  };

  const handleDeleteCourse = async () => {
    if (!selectedCourseId) return;
    if (!confirm(`Delete course "${selectedCourse?.name || selectedCourseId}"? This removes uploaded resources and vectors.`)) {
      return;
    }
    try {
      await deleteInstructorCourse(selectedCourseId);
      setActiveCourse(null);
      await refreshCourses();
    } catch (err) {
      setCourseError(err instanceof Error ? err.message : 'Unable to delete course');
    }
  };

  const handleUpload = async (file: File) => {
    if (!selectedCourseId) return;
    setUploading(true);
    setResourceError(null);
    try {
      await uploadCourseResource(selectedCourseId, file);
      await refreshResources(selectedCourseId);
    } catch (err) {
      setResourceError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleAddLink = async () => {
    if (!selectedCourseId) return;
    setLinkSubmitting(true);
    setResourceError(null);
    try {
      await addCourseLink(selectedCourseId, linkUrl.trim(), linkTitle.trim() || undefined);
      setLinkUrl('');
      setLinkTitle('');
      await refreshResources(selectedCourseId);
    } catch (err) {
      setResourceError(err instanceof Error ? err.message : 'Link add failed');
    } finally {
      setLinkSubmitting(false);
    }
  };

  const handleDeleteResource = async (resourceId: string) => {
    if (!selectedCourseId) return;
    if (!confirm('Delete this resource?')) return;
    setResourceError(null);
    try {
      await deleteCourseResource(selectedCourseId, resourceId);
      await refreshResources(selectedCourseId);
    } catch (err) {
      setResourceError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  return (
    <section className="flex w-full flex-1 flex-col gap-6 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100 md:p-8">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-semibold text-slate-900 md:text-2xl">Course management</h1>
          <p className="text-sm text-slate-600">Add or retire courses and manage uploaded resources without touching the server filesystem.</p>
        </div>
        <button
          type="button"
          onClick={refreshCourses}
          disabled={courseLoad === 'loading'}
          className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:bg-slate-100"
        >
          Refresh list
        </button>
      </header>

      {courseError && (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700">{courseError}</div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-800">Add a course</h2>
          <div className="mt-4 grid gap-3">
            <input
              value={newId}
              onChange={(e) => setNewId(e.target.value)}
              placeholder="Course ID (e.g., anth305)"
              className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
            />
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Course name"
              className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
            />
            <div className="grid gap-3 md:grid-cols-2">
              <input
                value={newCode}
                onChange={(e) => setNewCode(e.target.value)}
                placeholder="Code (optional)"
                className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
              />
              <input
                value={newTerm}
                onChange={(e) => setNewTerm(e.target.value)}
                placeholder="Term (optional)"
                className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
              />
            </div>
            <button
              type="button"
              onClick={handleCreateCourse}
              disabled={!newId.trim() || !newName.trim()}
              className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white transition enabled:hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              Create course
            </button>
            <p className="text-xs text-slate-500">
              Course ID must be letters/numbers with optional <code className="text-slate-700">_</code> or <code className="text-slate-700">-</code>.
            </p>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-800">Retire selected course</h2>
          <p className="mt-2 text-sm text-slate-600">
            Selected course: <span className="font-semibold text-slate-800">{selectedCourse?.name || '(none selected)'}</span>
          </p>
          <button
            type="button"
            onClick={handleDeleteCourse}
            disabled={!selectedCourseId}
            className="mt-4 rounded-full border border-rose-200 bg-rose-50 px-5 py-2 text-sm font-semibold text-rose-800 transition enabled:hover:border-rose-300 enabled:hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Delete course
          </button>
          <p className="mt-3 text-xs text-slate-500">
            Deletes the course entry, uploaded files, and vector embeddings for that course.
          </p>
        </div>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">Resources for selected course</h2>
            <p className="mt-1 text-xs text-slate-500">Uploads and link snapshots are stored under storage/uploads.</p>
          </div>
          <button
            type="button"
            onClick={() => selectedCourseId && refreshResources(selectedCourseId)}
            disabled={!selectedCourseId || resourceLoad === 'loading'}
            className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:bg-slate-100"
          >
            Refresh resources
          </button>
        </div>

        {!selectedCourseId && (
          <div className="mt-4 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
            Choose an active course in the header to manage its resources.
          </div>
        )}

        {selectedCourseId && resourceError && (
          <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700">{resourceError}</div>
        )}

        {selectedCourseId && (
          <div className="mt-4 grid gap-6 lg:grid-cols-2">
            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-slate-800">Upload a document</h3>
              <p className="mt-1 text-xs text-slate-500">Best results with .txt, .md, or other text-based files.</p>
              <input
                type="file"
                disabled={uploading}
                className="mt-3 block w-full text-sm text-slate-600 file:mr-4 file:rounded-full file:border-0 file:bg-slate-100 file:px-4 file:py-2 file:text-xs file:font-semibold file:text-slate-700 hover:file:bg-slate-200"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  handleUpload(file);
                  e.target.value = '';
                }}
              />
              {uploading && <p className="mt-2 text-xs text-slate-500">Uploading…</p>}
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-slate-800">Add a link snapshot</h3>
              <p className="mt-1 text-xs text-slate-500">LENA fetches the page text and stores a snapshot for ingestion.</p>
              <div className="mt-3 grid gap-2">
                <input
                  value={linkUrl}
                  onChange={(e) => setLinkUrl(e.target.value)}
                  placeholder="https://…"
                  className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
                />
                <input
                  value={linkTitle}
                  onChange={(e) => setLinkTitle(e.target.value)}
                  placeholder="Title (optional)"
                  className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
                />
                <button
                  type="button"
                  onClick={handleAddLink}
                  disabled={!linkUrl.trim() || linkSubmitting}
                  className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white transition enabled:hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {linkSubmitting ? 'Adding…' : 'Add link'}
                </button>
              </div>
            </div>
          </div>
        )}

        {selectedCourseId && (
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-slate-800">Current resources</h3>
            {resourceLoad === 'loading' && (
              <div className="mt-3 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
                Loading resources…
              </div>
            )}
            {resourceLoad !== 'loading' && resources.length === 0 && (
              <div className="mt-3 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
                No resources yet.
              </div>
            )}
            {resources.length > 0 && (
              <ul className="mt-3 space-y-2">
                {resources.map((r) => (
                  <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-slate-800">
                        {r.type === 'file' ? r.original_name : r.title || r.url}
                      </p>
                      <p className="truncate text-xs text-slate-500">{r.source_path}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteResource(r.id)}
                      className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                    >
                      Delete
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

