'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

import type { CourseSummary } from '../lib/api';
import { getCourses } from '../lib/api';
import { setActiveCourse } from '../lib/course';

interface CoursePickerModalProps {
  open: boolean;
  forceSelection?: boolean;
  activeCourseId?: string | null;
  onClose: () => void;
}

type LoadState = 'idle' | 'loading' | 'error' | 'success';

export default function CoursePickerModal({
  open,
  forceSelection = false,
  activeCourseId,
  onClose,
}: CoursePickerModalProps) {
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [loadState, setLoadState] = useState<LoadState>('idle');
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(activeCourseId ?? null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setSelectedCourseId(activeCourseId ?? null);
  }, [activeCourseId, open]);

  useEffect(() => {
    if (!open || loadState !== 'idle') return;

    let cancelled = false;
    const fetchCourses = async () => {
      setLoadState('loading');
      setErrorMessage(null);
      try {
        const data = await getCourses();
        if (cancelled) return;
        setCourses(data);
        setLoadState('success');
        if (!activeCourseId && data.length > 0) {
          setSelectedCourseId(data[0].id);
        }
      } catch (error) {
        if (cancelled) return;
        setLoadState('error');
        setErrorMessage(error instanceof Error ? error.message : 'Unable to load courses');
      }
    };

    fetchCourses();
    return () => {
      cancelled = true;
    };
  }, [activeCourseId, loadState, open]);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  const selectedCourse = useMemo(
    () => courses.find((course) => course.id === selectedCourseId) ?? null,
    [courses, selectedCourseId],
  );

  const handleConfirm = useCallback(() => {
    if (!selectedCourse) return;
    setActiveCourse({
      id: selectedCourse.id,
      name: selectedCourse.name,
      code: selectedCourse.code ?? null,
      term: selectedCourse.term ?? null,
    });
    onClose();
  }, [onClose, selectedCourse]);

  const handleRetry = () => {
    setLoadState('idle');
  };

  if (!open) return null;

  const canDismiss = !forceSelection;
  const isLoading = loadState === 'loading';

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/60 px-4 py-8">
      <div
        role="dialog"
        aria-modal="true"
        className="relative w-full max-w-lg rounded-3xl bg-white p-8 shadow-xl"
      >
        {canDismiss && (
          <button
            type="button"
            onClick={onClose}
            className="absolute right-4 top-4 rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close course picker"
          >
            ✕
          </button>
        )}

        <div className="mb-6 flex flex-col gap-2">
          <h2 className="text-xl font-semibold text-slate-900">Choose your course</h2>
          <p className="text-sm text-slate-600">
            LENA scopes every answer to a single course. Pick the class you want to explore. You can
            switch later from the header.
          </p>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 py-12 text-sm font-medium text-slate-500">
            Fetching course list…
          </div>
        )}

        {loadState === 'error' && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            <p className="font-semibold">Couldn&apos;t load courses</p>
            <p className="mt-1">{errorMessage}</p>
            <button
              type="button"
              className="mt-4 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
              onClick={handleRetry}
            >
              Try again
            </button>
          </div>
        )}

        {loadState === 'success' && courses.length === 0 && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            No courses are available yet. Check back once your instructor publishes the pilot.
          </div>
        )}

        {loadState === 'success' && courses.length > 0 && (
          <ul className="flex max-h-64 flex-col gap-2 overflow-y-auto pr-2">
            {courses.map((course) => {
              const isActive = selectedCourseId === course.id;
              return (
                <li key={course.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedCourseId(course.id)}
                    className={`flex w-full flex-col gap-1 rounded-2xl border px-4 py-3 text-left transition ${isActive
                      ? 'border-slate-900 bg-slate-900 text-white shadow-sm'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                      }`}
                  >
                    <span className="text-sm font-semibold">
                      {course.code ? `${course.code} · ${course.name}` : course.name}
                    </span>
                    {course.term && (
                      <span className={`text-xs ${isActive ? 'text-slate-100/90' : 'text-slate-500'}`}>
                        {course.term}
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}

        <div className="mt-6 flex justify-end gap-3">
          {canDismiss && (
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
            >
              Cancel
            </button>
          )}
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!selectedCourse || isLoading}
            className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white transition enabled:hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {selectedCourse ? 'Use this course' : 'Select a course'}
          </button>
        </div>
      </div>
    </div>
  );
}
