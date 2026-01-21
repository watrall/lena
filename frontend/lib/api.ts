import { getInstructorToken } from './instructorAuth';

export interface CourseSummary {
  id: string;
  name: string;
  code?: string | null;
  term?: string | null;
}

export interface Citation {
  title: string;
  section?: string | null;
  source_path: string;
}

export interface AskResponse {
  question_id: string;
  answer: string;
  citations: Citation[];
  confidence: number;
  escalation_suggested: boolean;
}

export interface FeedbackResponse {
  ok: boolean;
  review_enqueued: boolean;
}

export interface FAQEntry {
  question: string;
  answer: string;
  source_path?: string | null;
  updated_at?: string | null;
}

export interface InsightsSummary {
  totals: {
    questions: number;
    helpful_rate: number;
    average_confidence: number;
    escalations: number;
  };
  top_questions: Array<{ label: string; count: number }>;
  daily_volume: Array<{ date: string; count: number }>;
  confidence_trend: Array<{ date: string; confidence: number }>;
  escalations: Array<{
    question: string;
    student: string;
    submitted_at: string;
    delivered: boolean;
  }>;
  pain_points: Array<{ label: string; change: number }>;
  last_updated: string;
}

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000').replace(/\/$/, '');

/**
 * Make an HTTP request to the API backend.
 *
 * @param path - API endpoint path (e.g., '/ask')
 * @param init - Optional fetch configuration
 * @returns Parsed JSON response
 * @throws Error if request fails or returns non-OK status
 */
const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
      cache: 'no-store',
      ...init,
    });
  } catch (err) {
    throw new Error('Network error. Check that the API is reachable and CORS allows this origin.');
  }

  if (!response.ok) {
    let message: string;
    try {
      const body = await response.json();
      message = body.detail || body.message || `Request failed with status ${response.status}`;
    } catch {
      message = `Request failed with status ${response.status}`;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
};

export const getCourses = () => request<CourseSummary[]>('/courses');

export const askQuestion = (payload: { question: string; courseId: string }) =>
  request<AskResponse>('/ask', {
    method: 'POST',
    body: JSON.stringify({ question: payload.question, course_id: payload.courseId }),
  });

export const submitFeedback = (payload: {
  question_id: string;
  helpful: boolean;
  courseId: string;
  comment?: string;
  question?: string;
  answer?: string;
  citations?: Citation[];
  confidence?: number;
}) =>
  request<FeedbackResponse>('/feedback', {
    method: 'POST',
    body: JSON.stringify({
      question_id: payload.question_id,
      helpful: payload.helpful,
      course_id: payload.courseId,
      comment: payload.comment,
      question: payload.question,
      answer: payload.answer,
      citations: payload.citations,
      confidence: payload.confidence,
    }),
  });

export const requestEscalation = (payload: {
  question_id: string;
  question: string;
  student_name: string;
  student_email: string;
  courseId: string;
}) =>
  request('/escalations/request', {
    method: 'POST',
    body: JSON.stringify({
      question_id: payload.question_id,
      question: payload.question,
      student_name: payload.student_name,
      student_email: payload.student_email,
      course_id: payload.courseId,
    }),
  });

export const fetchFaq = (courseId: string) =>
  request<FAQEntry[]>(`/faq?course_id=${encodeURIComponent(courseId)}`);

export const fetchInsights = (courseId: string) =>
  request<InsightsSummary>(`/insights?course_id=${encodeURIComponent(courseId)}`, {
    headers: (() => {
      const token = getInstructorToken();
      return token ? { Authorization: `Bearer ${token}` } : {};
    })(),
  });

export type ExportRangeKind = '7d' | '30d' | 'custom' | 'all';
export type ExportFormat = 'json' | 'csv';

export type ExportComponent =
  | 'insights_totals'
  | 'insights_top_questions'
  | 'insights_daily_volume'
  | 'insights_confidence_trend'
  | 'insights_pain_points'
  | 'insights_escalations'
  | 'raw_interactions'
  | 'raw_answers'
  | 'raw_review_queue'
  | 'raw_faq'
  | 'raw_escalations';

export async function exportData(payload: {
  courseId: string; // course_id or 'all'
  components: ExportComponent[];
  format: ExportFormat;
  range: ExportRangeKind;
  startDate?: string;
  endDate?: string;
  tz?: string;
  includePii: boolean;
  includePiiConfirm?: string;
}): Promise<{ blob: Blob; filename: string }> {
  const params = new URLSearchParams();
  params.set('course_id', payload.courseId);
  params.set('format', payload.format);
  params.set('range', payload.range);
  if (payload.startDate) params.set('start_date', payload.startDate);
  if (payload.endDate) params.set('end_date', payload.endDate);
  if (payload.tz) params.set('tz', payload.tz);
  if (payload.includePii) {
    params.set('include_pii', 'true');
    if (payload.includePiiConfirm) params.set('include_pii_confirm', payload.includePiiConfirm);
  }
  for (const component of payload.components) {
    params.append('components', component);
  }

  const token = getInstructorToken();
  const response = await fetch(`${API_BASE}/admin/export?${params.toString()}`, {
    cache: 'no-store',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });

  if (!response.ok) {
    let message = `Export failed with status ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename="([^"]+)"/i);
  const filename = match?.[1] || 'lena_export.bin';

  const blob = await response.blob();
  return { blob, filename };
}
