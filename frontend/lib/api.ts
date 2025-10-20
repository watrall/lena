// api.ts – typed fetch helpers for LENA endpoints with course-aware parameters.
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
  total_questions: number;
  average_confidence: number;
  helpful_rate: number;
  escalations: number;
  total_feedback?: number;
  last_updated: string;
}

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000').replace(/\/$/, '');

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
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
}) =>
  request<FeedbackResponse>('/feedback', {
    method: 'POST',
    body: JSON.stringify({
      question_id: payload.question_id,
      helpful: payload.helpful,
      course_id: payload.courseId,
      comment: payload.comment,
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
  request<InsightsSummary>(`/insights?course_id=${encodeURIComponent(courseId)}`);
