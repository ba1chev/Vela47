// The trace panel: one row per step of a run, completed when the step finishes, with
// the steps inside a layer, a subagent or a message between subagents folded under it.

// How each event type renders. Keyed by the TraceEventType values the backend sends,
// so adding a type here is the only frontend change a new event needs. A type that
// opens a row also opens a group: everything reported until it closes goes inside.
const RENDER = {
  pipeline_started:  { kind: "pipeline", opens: "Pipeline" },
  pipeline_finished: { kind: "pipeline", closes: "Pipeline" },
  layer_started:     { kind: "layer",    opens: true },
  layer_finished:    { kind: "layer",    closes: true },
  subagent_started:  { kind: "subagent", opens: true },
  subagent_finished: { kind: "subagent", closes: true },
  sandbox_acquired:  { kind: "sandbox",  skip: true },
  sandbox_released:  { kind: "sandbox",  skip: true },
  model_invoked:     { kind: "model" },
  tool_executed:     { kind: "tool" },
  a2a_started:       { kind: "a2a",      opens: true },
  a2a_finished:      { kind: "a2a",      closes: true },
  run_failed:        { kind: "error" },
};

// Rows still waiting for their matching *_finished event, keyed by type+label, and the
// groups the next row goes into, innermost last.
const openRows = new Map();
const openGroups = [];
let traceEvents = [];

// Results and instructions are often Markdown, which three clamped lines cannot render,
// so the trace shows them as plain text: no stars, hashes, backticks or link targets.
function plainText(text) {
  return String(text)
    .replace(/```[\w-]*/g, "")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/(\*\*|__)(.+?)\1/g, "$2")
    .replace(/(^|[^\w*])\*([^*\n]+)\*(?!\w)/g, "$1$2")
    .replace(/^\s{0,3}#{1,6}\s+/gm, "")
    .replace(/^\s{0,3}>\s?/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "• ")
    .replace(/\s+/g, " ")
    .trim();
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
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const seconds = Math.round(ms / 1000);
  return `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
}

function formatTokens(count) {
  return count >= 1000 ? `${(count / 1000).toFixed(1)}k tok` : `${count} tok`;
}

// What a whole run cost: how long the pipeline took and how many tokens its model calls
// used. Shown above the trace and under the answer the run produced.
function summarizeTrace(events) {
  let durationMs = null;
  let tokens = 0;
  for (const event of events) {
    if (event.type === "pipeline_finished") durationMs = event.duration_ms;
    if (event.type === "model_invoked") tokens += (event.payload && event.payload.total_tokens) || 0;
  }
  return [
    durationMs == null ? null : formatDuration(durationMs),
    tokens ? formatTokens(tokens) : null,
  ].filter(Boolean).join(" · ");
}

function setDetail(row, event) {
  const detail = detailFor(event);
  if (!detail) return;
  const text = plainText(detail);
  row.detail.textContent = text;
  row.detail.title = text;
}

function makeRow(event, spec, label) {
  const li = makeElement("li", "ev");
  li.dataset.kind = spec.kind;
  li.style.setProperty("--depth", String(openGroups.length));
  // The label of a subagent event is its type, which the stylesheet turns into a
  // per-type hue so the trace is colour-coded by who did the work.
  if (spec.kind === "subagent") li.dataset.agent = label;
  // A message between two subagents, "TEST → CODE", takes the hue of the one it reaches,
  // whose own model calls follow it in the trace.
  if (spec.kind === "a2a") li.dataset.agent = label.split(" → ").pop();

  const head = makeElement(spec.opens ? "button" : "div", "ev-head");
  if (spec.opens) {
    head.type = "button";
    head.setAttribute("aria-expanded", "true");
    head.addEventListener("click", () => toggleGroup(row));
  }

  const dot = makeElement("span", "dot");
  const wrap = makeElement("span", "label");
  const name = makeElement("span", "name");
  name.textContent = label;
  const count = makeElement("span", "count");
  const detail = makeElement("span", "detail");
  wrap.append(name, count, detail);
  const time = makeElement("span", "time");
  head.append(dot, wrap, time);
  li.append(head);

  const row = { li, head, detail, count, time, children: null };
  if (spec.opens) {
    row.children = makeElement("ol", "ev-children");
    li.dataset.open = "1";
    li.append(row.children);
  }
  return row;
}

function toggleGroup(row) {
  if (!row.children || !row.children.children.length) return;
  const open = row.li.dataset.open !== "1";
  row.li.dataset.open = open ? "1" : "0";
  row.head.setAttribute("aria-expanded", String(open));
}

// A finished group folds away when it holds only leaf steps, so the panel keeps the
// shape of the run in view instead of every model call; a group that failed stays open.
function finishGroup(row) {
  const steps = row.children.children.length;
  if (!steps) return;
  row.li.dataset.nested = "1";
  row.count.textContent = `${steps} ${steps === 1 ? "call" : "calls"}`;
  const holdsGroups = row.children.querySelector(":scope > .ev > .ev-children") !== null;
  if (!holdsGroups && row.li.dataset.kind !== "error") toggleGroup(row);
}

function addEvent(event) {
  const spec = RENDER[event.type];
  if (!spec || spec.skip) return;

  traceEvents.push(event);
  traceEmptyEl.hidden = true;
  traceSummaryEl.textContent = summarizeTrace(traceEvents);
  const label = spec.opens === "Pipeline" || spec.closes === "Pipeline"
    ? "Pipeline"
    : event.label;
  const key = `${spec.kind}:${label}`;

  // A *_finished event completes the row its *_started opened, rather than adding
  // a second line — so the trace reads as a list of steps, not a log of transitions.
  if (spec.closes && openRows.has(key)) {
    const row = openRows.get(key);
    openRows.delete(key);
    const at = openGroups.indexOf(row);
    if (at >= 0) openGroups.splice(at);
    row.li.dataset.live = "0";
    if (event.payload && event.payload.status === "error") row.li.dataset.kind = "error";
    setDetail(row, event);
    row.time.textContent = formatDuration(event.duration_ms);
    finishGroup(row);
    return;
  }

  const parent = openGroups.length ? openGroups[openGroups.length - 1] : null;
  const row = makeRow(event, spec, label);
  setDetail(row, event);

  if (spec.opens) {
    row.li.dataset.live = "1";
    openRows.set(key, row);
  } else {
    row.time.textContent = formatDuration(event.duration_ms);
  }

  (parent ? parent.children : eventsEl).appendChild(row.li);
  if (spec.opens) openGroups.push(row);
  scrollToEnd(eventsEl.parentElement);
}

// Steps still open when a run ends never reported a result.
function settleTrace() {
  for (const row of openRows.values()) row.li.dataset.live = "0";
  openRows.clear();
  openGroups.length = 0;
}

function clearTrace() {
  eventsEl.replaceChildren();
  settleTrace();
  traceEvents = [];
  traceSummaryEl.textContent = "";
  traceEmptyEl.hidden = false;
  for (const answer of messagesEl.querySelectorAll(".answer[data-traced]")) {
    delete answer.dataset.traced;
  }
}

// Draws the stored trace of an earlier answer, from the top and without the entrance
// animations a live run plays.
function renderTrace(events) {
  clearTrace();
  eventsEl.dataset.replay = "1";
  for (const event of events) addEvent(event);
  settleTrace();
  delete eventsEl.dataset.replay;
  pendingScrolls.delete(eventsEl.parentElement);
  eventsEl.parentElement.scrollTop = 0;
}
