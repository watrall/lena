import { clearInstructorToken, getInstructorToken, setInstructorToken } from './instructorAuth';

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000').replace(/\/$/, '');

export type InstructorLoginResponse = {
  access_token: string;
  token_type: string;
  expires_at: string;
};

export type InstructorCourse = {
  id: string;
  name: string;
  code?: string | null;
  term?: string | null;
};

export type InstructorResource =
  | {
      id: string;
      course_id: string;
      type: 'file';
      original_name: string;
      source_path: string;
      created_at: string;
    }
  | {
      id: string;
      course_id: string;
      type: 'link';
      url: string;
      title?: string | null;
      source_path: string;
      created_at: string;
    };

function requireToken(): string {
  const token = getInstructorToken();
  if (!token) throw new Error('Instructor login required.');
  return token;
}

async function authFetch(path: string, init?: RequestInit): Promise<Response> {
  const token = requireToken();
  const headers = new Headers(init?.headers || undefined);
  headers.set('Authorization', `Bearer ${token}`);
  return fetch(`${API_BASE}${path}`, { cache: 'no-store', ...init, headers });
}

async function parseJsonOrThrow(response: Response) {
  if (response.ok) return response.json();
  let message = `Request failed with status ${response.status}`;
  try {
    const body = await response.json();
    message = body.detail || body.message || message;
  } catch {
    // ignore
  }
  if (response.status === 401) {
    clearInstructorToken();
  }
  throw new Error(message);
}

export async function instructorLogin(username: string, password: string) {
  const response = await fetch(`${API_BASE}/instructors/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
    cache: 'no-store',
  });
  const payload = (await parseJsonOrThrow(response)) as InstructorLoginResponse;
  setInstructorToken(payload.access_token, payload.expires_at);
  return payload;
}

export function instructorLogout() {
  clearInstructorToken();
}

export async function listInstructorCourses(): Promise<InstructorCourse[]> {
  const response = await authFetch('/instructors/courses');
  return (await parseJsonOrThrow(response)) as InstructorCourse[];
}

export async function createInstructorCourse(payload: InstructorCourse) {
  const response = await authFetch('/instructors/courses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseJsonOrThrow(response);
}

export async function deleteInstructorCourse(courseId: string) {
  const response = await authFetch(`/instructors/courses/${encodeURIComponent(courseId)}`, { method: 'DELETE' });
  return parseJsonOrThrow(response);
}

export async function listCourseResources(courseId: string): Promise<InstructorResource[]> {
  const response = await authFetch(`/instructors/courses/${encodeURIComponent(courseId)}/resources`);
  const payload = (await parseJsonOrThrow(response)) as { resources: InstructorResource[] };
  return payload.resources || [];
}

export async function uploadCourseResource(courseId: string, file: File) {
  const form = new FormData();
  form.append('file', file);
  const response = await authFetch(`/instructors/courses/${encodeURIComponent(courseId)}/resources/upload`, {
    method: 'POST',
    body: form,
  });
  return parseJsonOrThrow(response);
}

export async function addCourseLink(courseId: string, url: string, title?: string) {
  const response = await authFetch(`/instructors/courses/${encodeURIComponent(courseId)}/resources/link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, title: title || null }),
  });
  return parseJsonOrThrow(response);
}

export async function deleteCourseResource(courseId: string, resourceId: string) {
  const response = await authFetch(
    `/instructors/courses/${encodeURIComponent(courseId)}/resources/${encodeURIComponent(resourceId)}`,
    { method: 'DELETE' },
  );
  return parseJsonOrThrow(response);
}

export async function runIngest() {
  const response = await authFetch('/ingest/run', { method: 'POST' });
  return parseJsonOrThrow(response);
}

export type EscalationSummary = {
  total: number;
  unresolved: number;
  new: number;
};

export type EscalationStatus = 'new' | 'in_process' | 'contacted' | 'resolved';

export type EscalationRow = {
  id: string;
  student_name?: string | null;
  student_email?: string | null;
  question?: string | null;
  submitted_at?: string | null;
  last_viewed_at?: string | null;
  updated_at?: string | null;
  status?: EscalationStatus | null;
  notes?: string | null;
  contacted_at?: string | null;
  resolved_at?: string | null;
  confidence?: number | null;
  escalation_reason?: string | null;
};

export type EscalationEvent = {
  id: string;
  escalation_id: string;
  course_id: string;
  type: string;
  actor: string;
  at: string;
  meta?: Record<string, unknown>;
};

export async function fetchEscalationSummary(courseId: string): Promise<EscalationSummary> {
  const response = await authFetch(`/instructors/escalations/summary?course_id=${encodeURIComponent(courseId)}`);
  return (await parseJsonOrThrow(response)) as EscalationSummary;
}

export async function listEscalations(courseId: string): Promise<EscalationRow[]> {
  const response = await authFetch(`/instructors/escalations?course_id=${encodeURIComponent(courseId)}`);
  return (await parseJsonOrThrow(response)) as EscalationRow[];
}

export async function markEscalationViewed(courseId: string, escalationId: string): Promise<EscalationRow> {
  const response = await authFetch(
    `/instructors/escalations/${encodeURIComponent(escalationId)}/viewed?course_id=${encodeURIComponent(courseId)}`,
    { method: 'POST' },
  );
  return (await parseJsonOrThrow(response)) as EscalationRow;
}

export async function updateEscalation(
  courseId: string,
  escalationId: string,
  payload: { status?: EscalationStatus; notes?: string },
): Promise<EscalationRow> {
  const response = await authFetch(`/instructors/escalations/${encodeURIComponent(escalationId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ course_id: courseId, status: payload.status, notes: payload.notes }),
  });
  return (await parseJsonOrThrow(response)) as EscalationRow;
}

export async function logEscalationReplyInitiated(courseId: string, escalationId: string) {
  const response = await authFetch(
    `/instructors/escalations/${encodeURIComponent(escalationId)}/reply_initiated?course_id=${encodeURIComponent(courseId)}`,
    { method: 'POST' },
  );
  return parseJsonOrThrow(response);
}

export async function listEscalationEvents(courseId: string, escalationId: string): Promise<EscalationEvent[]> {
  const response = await authFetch(
    `/instructors/escalations/${encodeURIComponent(escalationId)}/events?course_id=${encodeURIComponent(courseId)}`,
  );
  const payload = (await parseJsonOrThrow(response)) as { events: EscalationEvent[] };
  return payload.events || [];
}
