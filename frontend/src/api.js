// Same-origin by default (dev proxy / backend-served build).
// Set VITE_API_URL if the API lives on another host.
const BASE = import.meta.env.VITE_API_URL ?? "";

export async function getJSON(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ""}`);
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json()).detail ?? "";
    } catch {
      /* body was not JSON */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}