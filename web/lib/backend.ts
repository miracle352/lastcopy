/** Local development proxy only. Hosted UI does not expose the private evidence API. */
export function localRequest(request: Request): boolean {
  return ['127.0.0.1:3000','localhost:3000'].includes(request.headers.get('host')?.toLowerCase() ?? '');
}

export function backendOrigin(): string | null {
  if (process.env.VERCEL) return null;
  const value = process.env.API_ORIGIN ?? "http://127.0.0.1:8000";
  try {
    const url = new URL(value);
    if (!['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname) || url.protocol !== 'http:' || url.username || url.password || url.search || url.hash || url.pathname !== '/') return null;
    return url.origin;
  } catch { return null; }
}
