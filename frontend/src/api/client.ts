const API_BASE = "/api/v1";

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    let detail = text || response.statusText;
    try {
      const body = JSON.parse(text);
      if (body?.detail) {
        detail =
          typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      /* keep text */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export { API_BASE };
