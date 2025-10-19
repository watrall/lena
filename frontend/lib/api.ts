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

export interface Insights {
  total_questions: number;
  average_confidence: number;
  helpful_rate: number;
  total_feedback: number;
  last_updated: string;
}

const API_BASE =
  (typeof window !== 'undefined' && (window as any)?.__LENA_API_BASE__) ||
  process.env.NEXT_PUBLIC_API_BASE ||
  'http://localhost:8000';

async function handle<T>(promise: Promise<Response>): Promise<T> {
  const response = await promise;
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `API error: ${response.status}`);
  }
  return response.json();
}

export function askQuestion(question: string): Promise<AskResponse> {
  return handle<AskResponse>(
    fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    }),
  );
}

export function submitFeedback(payload: {
  question_id: string;
  helpful: boolean;
  comment?: string;
  question?: string;
  answer?: string;
  citations?: Citation[];
  confidence?: number;
}): Promise<FeedbackResponse> {
  return handle<FeedbackResponse>(
    fetch(`${API_BASE}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  );
}

export function fetchFaq(): Promise<FAQEntry[]> {
  return handle<FAQEntry[]>(fetch(`${API_BASE}/faq`));
}

export function fetchInsights(): Promise<Insights> {
  return handle<Insights>(fetch(`${API_BASE}/insights`));
}
