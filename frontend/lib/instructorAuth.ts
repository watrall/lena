const STORAGE_KEY = 'lena.instructorAuth';

type StoredAuth = {
  token: string;
  expiresAt: string;
};

const isBrowser = () => typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';

export function getInstructorToken(): string | null {
  if (!isBrowser()) return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as StoredAuth;
    if (!parsed?.token || !parsed?.expiresAt) return null;
    const expires = Date.parse(parsed.expiresAt);
    if (!Number.isFinite(expires) || expires <= Date.now()) {
      window.localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed.token;
  } catch {
    return null;
  }
}

export function setInstructorToken(token: string, expiresAt: string) {
  if (!isBrowser()) return;
  const next: StoredAuth = { token, expiresAt };
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
}

export function clearInstructorToken() {
  if (!isBrowser()) return;
  window.localStorage.removeItem(STORAGE_KEY);
}

