// Loaded last: everything above is defined, so the page can start.

// An existing session cookie skips the gate; anything else — no cookie, an expired
// one, a server restarted with a new signing key — lands on it.
async function boot() {
  loadAgentChoice();
  const result = await api("/api/auth/me");
  if (result.ok) await enterApp(result.data);
  else showGate();
}

boot();
