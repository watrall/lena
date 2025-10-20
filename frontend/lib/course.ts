// course.ts – stores the active course in localStorage and broadcasts changes.
import type { CourseSummary } from './api';

export type ActiveCourse = Pick<CourseSummary, 'id' | 'name' | 'code' | 'term'>;

type CourseListener = (course: ActiveCourse | null) => void;

const STORAGE_KEY = 'lena.activeCourse';
const listeners = new Set<CourseListener>();

const isBrowser = () => typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';

function parseStoredCourse(raw: string | null): ActiveCourse | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as ActiveCourse;
    if (!parsed?.id || !parsed?.name) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function notify(course: ActiveCourse | null) {
  listeners.forEach((listener) => listener(course));
}

export function getActiveCourse(): ActiveCourse | null {
  if (!isBrowser()) return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  return parseStoredCourse(raw);
}

export function setActiveCourse(next: ActiveCourse | null) {
  if (!isBrowser()) return;
  if (next) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } else {
    window.localStorage.removeItem(STORAGE_KEY);
  }
  notify(next);
}

export function subscribeToCourse(listener: CourseListener) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

if (isBrowser()) {
  window.addEventListener('storage', (event) => {
    if (event.key !== STORAGE_KEY) return;
    notify(parseStoredCourse(event.newValue));
  });
}
