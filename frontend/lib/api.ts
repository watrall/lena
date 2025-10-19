export interface AskResponse {
  question_id: string;
  answer: string;
  citations: Array<{
    title: string;
    section?: string | null;
    source_path: string;
  }>;
  confidence: number;
  escalation_suggested: boolean;
}

const API_BASE =
  (typeof window !== 'undefined' && window?.__LENA_API_BASE__) ||
  process.env.NEXT_PUBLIC_API_BASE ||
  'http://localhost:8000';

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}
