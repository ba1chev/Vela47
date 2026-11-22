// Sending a message, following the run's event stream until the answer, and stopping it.

function setStatus(state, text) {
  statusEl.dataset.state = state;
  statusEl.textContent = text;
}

// While a run works the composer keeps taking text, so the next question can be written
// while the answer is still coming; only sending waits, and the send button stops the run.
function setBusy(busy) {
  sendEl.setAttribute("aria-label", busy ? "Stop" : "Send");
  sendEl.dataset.mode = busy ? "stop" : "send";
  for (const input of agentSwitchEl.querySelectorAll("input")) input.disabled = busy;
  if (busy) {
    appEl.dataset.busy = "1";
    traceToggleEl.dataset.live = "1";
  } else {
    delete appEl.dataset.busy;
    delete traceToggleEl.dataset.live;
  }
}

function formatElapsed(ms) {
  const seconds = Math.floor(ms / 1000);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

function titleCase(text) {
  return text.charAt(0) + text.slice(1).toLowerCase();
}

// What the placeholder says, read off the same events the trace draws: the layer the
// run is in and, among the subagents, which step of how many and the tool it last used.
function trackProgress(progress, event) {
  const p = event.payload || {};
  switch (event.type) {
    case "layer_started":
      progress.layer = event.label;
      progress.tool = null;
      break;
    case "layer_finished":
      if (p.tasks) progress.tasks = p.tasks;
      break;
    case "subagent_started":
      progress.step += 1;
      progress.subagent = titleCase(event.label);
      progress.tool = null;
      break;
    case "tool_executed":
      progress.tool = event.label;
      break;
    case "a2a_started":
      progress.tool = event.label;
      break;
    default:
      return;
  }
  let text = `${progress.layer || "Working"}…`;
  if (progress.subagent && progress.layer === "Subagents") {
    const of = progress.tasks ? ` of ${progress.tasks}` : "";
    text = `${progress.subagent} · step ${progress.step}${of}`;
  }
  if (progress.tool) text += ` · ${progress.tool}`;
  progress.label.textContent = text;
}

function endRun() {
  if (!run) return null;
  const ended = run;
  run = null;
  if (stream) { stream.close(); stream = null; }
  clearInterval(ended.timer);
  if (ended.placeholder.isConnected) ended.placeholder.remove();
  settleTrace();
  setBusy(false);
  inputEl.focus();
  return ended;
}

// A conversation the server has not stored yet disappears from the list again when its
// first run fails or is stopped, since the server only stores it with its first answer.
function forgetUnsavedSession(ended) {
  if (ended.createdSessionId && currentSessionId === ended.createdSessionId) currentSessionId = null;
  loadSessions();
}

// Asking again removes the failed attempt, question included, and sends it once more.
function retryWith(message, element) {
  return () => {
    if (run) return;
    const question = element.previousElementSibling;
    if (question && question.classList.contains("user")) question.remove();
    element.remove();
    send(message);
  };
}

// Stopping closes the stream. The server notices the closed connection and drops the
// run's result instead of storing it; work already handed to a model or a sandbox
// finishes in the background.
function stopRun() {
  const ended = endRun();
  if (!ended) return;
  setStatus("idle", "idle");
  if (ended.streamed) {
    const wrap = ended.streamed.parentElement;
    delete ended.streamed.dataset.streaming;
    const note = makeElement("span", "meta-stats stopped");
    note.textContent = "Stopped · not saved";
    wrap.append(metaRow(note, metaAction("Retry", retryWith(ended.message, wrap))));
  } else {
    const notice = addNotice("Stopped before an answer arrived. Nothing was saved.", "stopped");
    notice.append(metaRow(metaAction("Retry", retryWith(ended.message, notice))));
  }
  forgetUnsavedSession(ended);
}

function metaRow(...children) {
  const meta = makeElement("div", "msg-meta");
  meta.append(...children);
  return meta;
}

function failRun(text) {
  const ended = endRun();
  if (!ended) return;
  if (ended.streamed) ended.streamed.parentElement.remove();
  const notice = addNotice(text, "err");
  notice.append(metaRow(metaAction("Retry", retryWith(ended.message, notice))));
  setStatus("error", "error");
  forgetUnsavedSession(ended);
}

async function send(message) {
  addMessage(message, "user");
  clearTrace();
  const placeholder = addThinking();
  const startedAt = Date.now();
  const progress = {
    label: placeholder.querySelector(".thinking-label"),
    layer: null, tasks: null, step: 0, subagent: null, tool: null,
  };
  const timeEl = placeholder.querySelector(".thinking-time");
  run = {
    message, placeholder, streamed: null, createdSessionId: null, events: [],
    timer: setInterval(() => { timeEl.textContent = formatElapsed(Date.now() - startedAt); }, 1000),
  };
  const current = run;
  setBusy(true);
  setStatus("running", "running");

  // A session can expire while the page is open, and EventSource cannot tell a 401
  // from a dropped connection — so it is checked before every stream instead.
  const check = await api("/api/auth/me");
  if (run !== current) return;
  if (check.status === 0) {
    failRun("The server could not be reached.");
    return;
  }
  if (!check.ok) {
    endRun();
    setStatus("idle", "idle");
    showGate(EXPIRED);
    return;
  }

  const agent = currentAgent();
  const params = new URLSearchParams({ message, agent });
  if (currentSessionId) params.set("session_id", currentSessionId);
  stream = new EventSource(`/api/chat/stream?${params}`);

  stream.addEventListener("trace", (e) => {
    const event = JSON.parse(e.data);
    current.events.push(event);
    addEvent(event);
    trackProgress(progress, event);
  });

  // The first frame names the conversation. A new one is shown in the list straight
  // away; the server only stores it once the answer is complete, so a failed run
  // forgets it again.
  stream.addEventListener("session", (e) => {
    const session = JSON.parse(e.data);
    currentSessionId = session.id;
    if (session.new) {
      current.createdSessionId = session.id;
      sessions = [{ ...session, updated_at: new Date().toISOString() }, ...sessions];
      renderSessions();
    }
    markActive();
  });

  // The first chunk replaces the thinking dots with a real bubble. Markdown can only be
  // rendered whole, so the chunks are collected and the bubble is rendered again at
  // most once a frame, however many chunks arrive in between.
  let streamedMarkdown = "";
  let renderPending = false;
  stream.addEventListener("chunk", (e) => {
    const { text } = JSON.parse(e.data);
    if (!text || run !== current) return;
    if (!current.streamed) {
      placeholder.remove();
      current.streamed = addAnswer("", agent);
      current.streamed.dataset.streaming = "1";
    }
    streamedMarkdown += text;
    if (renderPending) return;
    renderPending = true;
    requestAnimationFrame(() => {
      renderPending = false;
      if (run !== current) return;
      renderAnswer(current.streamed, streamedMarkdown);
      scrollToEnd(messagesEl);
    });
  });

  stream.addEventListener("answer", (e) => {
    const { content, agent: answeredBy, sources } = JSON.parse(e.data);
    // The answer is rendered once more in full, since the last chunks may still be
    // waiting for their frame; without chunks it is the only render.
    let bubble = current.streamed;
    if (bubble) {
      renderAnswer(bubble, streamedMarkdown || content || "(empty answer)");
      delete bubble.dataset.streaming;
    } else {
      bubble = addAnswer(content || "(empty answer)", answeredBy || agent);
    }
    bubble.dataset.agent = answeredBy || agent;
    endRun();
    completeAnswer(bubble, { sources: sources || [], trace: current.events });
    bubble.parentElement.dataset.traced = "1";
    setStatus("idle", "idle");
    loadSessions();
  });

  stream.addEventListener("error", (e) => {
    // EventSource reuses "error" for transport failures, which carry no data.
    const text = e.data
      ? JSON.parse(e.data).message
      : "Connection to the server was lost.";
    failRun(text);
  });
}

function submitMessage(text) {
  const message = text.trim();
  if (!message || run) return false;
  send(message);
  return true;
}

formEl.addEventListener("submit", (e) => {
  e.preventDefault();
  if (run) {
    stopRun();
    return;
  }
  if (submitMessage(inputEl.value)) {
    inputEl.value = "";
    inputEl.style.height = "auto";
  }
});

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    if (!run) formEl.requestSubmit();
  }
});

inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = `${Math.min(inputEl.scrollHeight, 180)}px`;
});

document.getElementById("clear").addEventListener("click", clearTrace);
