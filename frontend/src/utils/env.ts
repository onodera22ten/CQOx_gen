/**
 * Runtime-safe environment helpers.
 * Provides deterministic fallbacks when Vite build-time env vars
 * (e.g., VITE_API_URL) are missing, which is common in Docker deploys.
 */

const DEFAULT_LOCAL_API = 'http://localhost:8000';

const sanitizeUrl = (url: string) => url.replace(/\/+$/, '');

export const getApiUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL?.trim();
  if (envUrl && !envUrl.includes('localhost:8000')) {
    return sanitizeUrl(envUrl);
  }

  if (typeof window !== 'undefined') {
    // Use same-origin relative path when running in the browser.
    // Nginx (production) and Vite (development) both proxy /api -> backend.
    return '';
  }

  return DEFAULT_LOCAL_API;
};
