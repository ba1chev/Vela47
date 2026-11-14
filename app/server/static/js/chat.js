// Sending a message and following the run's event stream until the answer.

function setStatus(state, text) {
  statusEl.dataset.state = state;
  statusEl.textContent = text;
}

function setBusy(busy) {
  sendEl.disabled = busy;
  inputEl.disabled = busy;
  if (busy) appEl.dataset.busy = "1";
  else delete appEl.dataset.busy;
}

function finish(placeholder) {
  if (stream) { stream.close(); stream = null; }
  if (placeholder && placeholder.isConnected) placeholder.remove();
  // Any step still open when the stream ends never reported a result.
  for (const row of openRows.values()) row.li.dataset.live = "0";
  openRows.clear();
  setBusy(false);
  inputEl.focus();
}

async function send(message) {
  addMessage(message, "user");
  const placeholder = addThinking();
  setBusy(true);
  setStatus("running", "running");

  // A session can expire while the page is open, and EventSource cannot tell a 401
  // from a dropped connection — so it is checked before every stream instead.
  const check = await api("/api/auth/me");
  if (!check.ok) {
    finish(placeholder);
    setStatus("idle", "idle");
    showGate(EXPIRED);
    return;
  }

  const agent = agentSelectEl.value;
  const params = new URLSearchParams({ message, agent });
  if (currentSessionId) params.set("session_id", currentSessionId);
  stream = new EventSource(`/api/chat/stream?${params}`);

  stream.addEventListener("trace", (e) => addEvent(JSON.parse(e.data)));

  // The first frame names the conversation. A new one is shown in the list straight
  // away; the server only stores it once the answer is complete, so a failed run
  // forgets it again.
  let createdSessionId = null;
  stream.addEventListener("session", (e) => {
    const session = JSON.parse(e.data);
    currentSessionId = session.id;
    if (session.new) {
      createdSessionId = session.id;
      sessions = [{ ...session, updated_at: new Date().toISOString() }, ...sessions];
      renderSessions();
    }
    markActive();
  });

  // The first chunk replaces the thinking dots with a real bubble. Markdown can only be
  // rendered whole, so the chunks are collected and the bubble is rendered again at
  // most once a frame, however many chunks arrive in between.
  let streamed = null;
  let streamedMarkdown = "";
  let renderPending = false;
  stream.addEventListener("chunk", (e) => {
    const { text } = JSON.parse(e.data);
    if (!text) return;
    if (!streamed) {
      placeholder.remove();
      streamed = addMessage("", "ai");
      streamed.dataset.agent = agent;
    }
    streamedMarkdown += text;
    if (renderPending) return;
    renderPending = true;
    requestAnimationFrame(() => {
      renderPending = false;
      renderAnswer(streamed, streamedMarkdown);
      scrollToEnd(messagesEl);
    });
  });

  stream.addEventListener("answer", (e) => {
    const { content, agent: answeredBy, sources } = JSON.parse(e.data);
    // The answer is rendered once more in full, since the last chunks may still be
    // waiting for their frame; without chunks it is the only render.
    if (streamed) {
      renderAnswer(streamed, streamedMarkdown || content || "(empty answer)");
    } else {
      placeholder.remove();
      streamed = addMessage(content || "(empty answer)", "ai");
    }
    streamed.dataset.agent = answeredBy || agent;
    if (sources && sources.length) renderSources(sources);
    setStatus("idle", "idle");
    finish(null);
    loadSessions();
  });

  stream.addEventListener("error", (e) => {
    // EventSource reuses "error" for transport failures, which carry no data.
    const text = e.data
      ? JSON.parse(e.data).message
      : "Connection to the server was lost.";
    placeholder.remove();
    addMessage(text, "err");
    setStatus("error", "error");
    if (createdSessionId && currentSessionId === createdSessionId) currentSessionId = null;
    finish(null);
    loadSessions();
  });
}

formEl.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = inputEl.value.trim();
  if (!message || sendEl.disabled) return;
  inputEl.value = "";
  inputEl.style.height = "auto";
  send(message);
});

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    formEl.requestSubmit();
  }
});

inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = `${Math.min(inputEl.scrollHeight, 180)}px`;
});

document.getElementById("clear").addEventListener("click", clearTrace);
