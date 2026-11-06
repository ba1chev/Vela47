const messagesEl = document.getElementById("messages");
const eventsEl = document.getElementById("events");
const traceEmptyEl = document.getElementById("trace-empty");
const emptyEl = document.getElementById("empty");
const statusEl = document.getElementById("status");
const formEl = document.getElementById("composer");
const inputEl = document.getElementById("input");
const sendEl = document.getElementById("send");

// How each event type renders. Keyed by the TraceEventType values the backend sends,
// so adding a type here is the only frontend change a new event needs.
const RENDER = {
  pipeline_started:  { kind: "pipeline", depth: 0, opens: "Pipeline" },
  pipeline_finished: { kind: "pipeline", depth: 0, closes: "Pipeline" },
  layer_started:     { kind: "layer",    depth: 1, opens: true },
  layer_finished:    { kind: "layer",    depth: 1, closes: true },
  subagent_started:  { kind: "subagent", depth: 2, opens: true },
  subagent_finished: { kind: "subagent", depth: 2, closes: true },
  sandbox_acquired:  { kind: "sandbox",  depth: 2, skip: true },
  sandbox_released:  { kind: "sandbox",  depth: 2, skip: true },
  model_invoked:     { kind: "model",    depth: 2 },
  tool_executed:     { kind: "tool",     depth: 2 },
  run_failed:        { kind: "error",    depth: 0 },
};

// Rows still waiting for their matching *_finished event, keyed by type+label.
const openRows = new Map();
let stream = null;

function setStatus(state, text) {
  statusEl.dataset.state = state;
  statusEl.textContent = text;
}

function detailFor(event) {
  const p = event.payload || {};
  switch (event.type) {
    case "layer_finished":
      return [
        p.steps ? `${p.steps} steps` : null,
        p.tasks ? `${p.tasks} tasks` : null,
        p.results ? `${p.results} results` : null,
      ].filter(Boolean).join(" · ");
    case "subagent_started":
      return p.instruction || "";
    case "subagent_finished":
      return p.status === "error" ? `failed: ${p.result || ""}` : (p.result || "");
    case "model_invoked":
      return [
        p.total_tokens ? `${p.total_tokens} tok` : null,
        (p.tool_calls && p.tool_calls.length) ? `→ ${p.tool_calls.join(", ")}` : null,
      ].filter(Boolean).join(" · ");
    case "tool_executed":
      return p.status === "error" ? `error: ${p.result || ""}` : (p.result || "");
    case "pipeline_finished":
      return p.results ? `${p.results} results merged` : "";
    default:
      return "";
  }
}

function formatDuration(ms) {
  if (ms == null) return "";
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`;
}

function makeRow(event, spec, label) {
  const li = document.createElement("li");
  li.className = "ev";
  li.dataset.kind = spec.kind;
  li.dataset.depth = String(spec.depth);
  // The label of a subagent event is its type, which the stylesheet turns into a
  // per-type hue so the trace is colour-coded by who did the work.
  if (spec.kind === "subagent") li.dataset.agent = label;

  const dot = document.createElement("span");
  dot.className = "dot";

  const wrap = document.createElement("span");
  wrap.className = "label";
  const name = document.createElement("span");
  name.className = "name";
  name.textContent = label;
  wrap.appendChild(name);

  const detail = document.createElement("span");
  detail.className = "detail";
  wrap.appendChild(detail);

  const time = document.createElement("span");
  time.className = "time";

  li.append(dot, wrap, time);
  return { li, detail, time };
}

function addEvent(event) {
  const spec = RENDER[event.type];
  if (!spec || spec.skip) return;

  traceEmptyEl.hidden = true;
  const label = spec.opens === "Pipeline" || spec.closes === "Pipeline"
    ? "Pipeline"
    : event.label;
  const key = `${spec.kind}:${label}`;

  // A *_finished event completes the row its *_started opened, rather than adding
  // a second line — so the trace reads as a list of steps, not a log of transitions.
  if (spec.closes && openRows.has(key)) {
    const row = openRows.get(key);
    openRows.delete(key);
    row.li.dataset.live = "0";
    if (event.payload && event.payload.status === "error") {
      row.li.dataset.kind = "error";
    }
    const detail = detailFor(event);
    if (detail) row.detail.textContent = detail;
    row.time.textContent = formatDuration(event.duration_ms);
    return;
  }

  const row = makeRow(event, spec, label);
  const detail = detailFor(event);
  if (detail) row.detail.textContent = detail;

  if (spec.opens) {
    row.li.dataset.live = "1";
    openRows.set(key, row);
  } else {
    row.time.textContent = formatDuration(event.duration_ms);
  }

  eventsEl.appendChild(row.li);
  eventsEl.parentElement.scrollTop = eventsEl.parentElement.scrollHeight;
}

function addMessage(text, variant) {
  if (emptyEl) emptyEl.hidden = true;
  const div = document.createElement("div");
  div.className = `msg ${variant}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function addThinking() {
  if (emptyEl) emptyEl.hidden = true;
  const div = document.createElement("div");
  div.className = "msg ai thinking";
  div.innerHTML = "<i></i><i></i><i></i>";
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function finish(placeholder) {
  if (stream) { stream.close(); stream = null; }
  if (placeholder && placeholder.isConnected) placeholder.remove();
  // Any step still open when the stream ends never reported a result.
  for (const row of openRows.values()) row.li.dataset.live = "0";
  openRows.clear();
  sendEl.disabled = false;
  inputEl.disabled = false;
  inputEl.focus();
}

// Every request runs as some principal, and EventSource cannot say why it failed — a
// 401 looks exactly like a dropped connection. So a session is made sure of before each
// stream: whoever is signed in stays signed in, and a visitor with no session, or one
// whose session has expired, quietly becomes a guest.
async function ensureSession() {
  const me = await fetch("/api/auth/me");
  if (me.ok) return;
  const guest = await fetch("/api/auth/guest", { method: "POST" });
  if (!guest.ok) throw new Error("Could not open a guest session.");
}

async function send(message) {
  addMessage(message, "user");
  const placeholder = addThinking();
  sendEl.disabled = true;
  inputEl.disabled = true;
  setStatus("running", "running");

  try {
    await ensureSession();
  } catch (err) {
    placeholder.remove();
    addMessage(err.message, "err");
    setStatus("error", "error");
    finish(null);
    return;
  }

  stream = new EventSource(`/api/chat/stream?message=${encodeURIComponent(message)}`);

  stream.addEventListener("trace", (e) => addEvent(JSON.parse(e.data)));

  // The first chunk replaces the thinking dots with a real bubble; the rest append
  // to it, so the answer is written into the page as the model produces it.
  let streamed = null;
  stream.addEventListener("chunk", (e) => {
    const { text } = JSON.parse(e.data);
    if (!text) return;
    if (!streamed) {
      placeholder.remove();
      streamed = addMessage("", "ai");
    }
    streamed.textContent += text;
    messagesEl.scrollTop = messagesEl.scrollHeight;
  });

  stream.addEventListener("answer", (e) => {
    const { content } = JSON.parse(e.data);
    // With chunks the bubble is already complete, so the final frame only has to
    // cover the case where nothing streamed at all.
    if (streamed) {
      if (!streamed.textContent) streamed.textContent = content || "(empty answer)";
    } else {
      placeholder.remove();
      addMessage(content || "(empty answer)", "ai");
    }
    setStatus("idle", "idle");
    finish(null);
  });

  stream.addEventListener("error", (e) => {
    // EventSource reuses "error" for transport failures, which carry no data.
    const text = e.data
      ? JSON.parse(e.data).message
      : "Connection to the server was lost.";
    placeholder.remove();
    addMessage(text, "err");
    setStatus("error", "error");
    finish(null);
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

document.getElementById("clear").addEventListener("click", () => {
  eventsEl.replaceChildren();
  openRows.clear();
  traceEmptyEl.hidden = false;
});

inputEl.focus();
