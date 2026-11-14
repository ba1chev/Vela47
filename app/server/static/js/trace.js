// The trace panel: one row per step of a run, completed when the step finishes.

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
  a2a_started:       { kind: "a2a",      depth: 2, opens: true },
  a2a_finished:      { kind: "a2a",      depth: 2, closes: true },
  run_failed:        { kind: "error",    depth: 0 },
};

// Rows still waiting for their matching *_finished event, keyed by type+label.
const openRows = new Map();

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
    case "a2a_started":
      return p.message || "";
    case "a2a_finished":
      return p.status === "error" ? `failed: ${p.result || ""}` : (p.result || "");
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
  // A message between two subagents, "TEST → CODE", takes the hue of the one it reaches,
  // whose own model calls follow it in the trace.
  if (spec.kind === "a2a") li.dataset.agent = label.split(" → ").pop();

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
  scrollToEnd(eventsEl.parentElement);
}

function clearTrace() {
  eventsEl.replaceChildren();
  openRows.clear();
  traceEmptyEl.hidden = false;
}
