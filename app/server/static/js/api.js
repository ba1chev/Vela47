// Talking to the server.

// One place that talks JSON to the server, so every caller gets the same shape back
// and can tell a 401 — sign in again — from any other failure.
async function api(path, { method = "GET", body } = {}) {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  if (response.status !== 204) {
    try { data = await response.json(); } catch { data = null; }
  }
  return { ok: response.ok, status: response.status, data };
}

// FastAPI reports its own validation failures as a list, everything else as a string.
function errorText(result, fallback) {
  const detail = result.data && result.data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join("; ");
  return fallback;
}
