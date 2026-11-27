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
  tool_started:      { kind: "tool",     opens: true },
  tool_executed:     { kind: "tool",     closes: true },
  a2a_started:       { kind: "a2a",      opens: true },
  a2a_finished:      { kind: "a2a",      closes: true },
  security_checked:  { kind: "check" },
  security_flagged:  { kind: "security" },
  run_failed:        { kind: "error" },
  step_started:      { kind: "step",     opens: true },
  step_finished:     { kind: "step",     closes: true },
  step_recorded:     { kind: "step" },
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

function plural(count, noun) {
  return `${count} ${noun}${count === 1 ? "" : "s"}`;
}

function detailFor(event) {
  const p = event.payload || {};
  switch (event.type) {
    case "layer_finished":
      return [
        p.steps ? plural(p.steps, "step") : null,
        p.tasks ? plural(p.tasks, "task") : null,
        p.results ? plural(p.results, "result") : null,
        p.flagged ? `${p.flagged} flagged` : null,
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
    case "tool_started":
      return p.args ? Object.entries(p.args).map(([key, value]) => `${key}: ${typeof value === "string" ? value : JSON.stringify(value)}`).join(" · ") : "";
    case "security_checked":
      return [
        "clean",
        p.signatures ? plural(p.signatures.length, "signature") : null,
        p.characters != null ? `${p.characters} chars` : null,
        p.invisible_characters ? `${p.invisible_characters} invisible removed` : null,
        p.hidden_characters ? `${p.hidden_characters} hidden decoded` : null,
        p.normalized ? "normalised" : null,
      ].filter(Boolean).join(" · ");
    case "tool_executed":
      return p.status === "error" ? `error: ${p.result || ""}` : (p.result || "");
    case "a2a_started":
      return p.message || "";
    case "a2a_finished":
      return p.status === "error" ? `failed: ${p.result || ""}` : (p.result || "");
    case "pipeline_finished":
      return p.results ? `${plural(p.results, "result")} merged` : "";
    case "step_started":
    case "step_finished":
    case "step_recorded":
      return p.status === "error" ? `failed: ${p.error || ""}` : (p.detail || "");
    case "security_flagged":
      return Object.entries(p.matches || {}).map(([name, text]) => `${name}: ${text}`).join(" · ");
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
// used, and how many prompt attacks the security monitor found in what it read. Shown
// above the trace and under the answer the run produced.
function summarizeTrace(events) {
  let durationMs = null;
  let tokens = 0;
  let findings = 0;
  for (const event of events) {
    if (event.type === "pipeline_finished") durationMs = event.duration_ms;
    if (event.type === "model_invoked") tokens += (event.payload && event.payload.total_tokens) || 0;
    if (event.type === "security_flagged") findings += 1;
  }
  return [
    durationMs == null ? null : formatDuration(durationMs),
    tokens ? formatTokens(tokens) : null,
    findings ? `${findings} security ${findings === 1 ? "finding" : "findings"}` : null,
  ].filter(Boolean).join(" · ");
}

// A security finding is shown exactly as found: its evidence may be the very Markdown,
// an image link for one, that plain text would strip away.
function setDetail(row, event) {
  const detail = detailFor(event);
  if (!detail) return;
  const text = event.type === "security_flagged" ? detail : plainText(detail);
  row.detail.textContent = text;
  row.detail.title = text;
}

function makeRow(event, spec, label, depth) {
  const li = makeElement("li", "ev");
  li.dataset.kind = spec.kind;
  li.style.setProperty("--depth", String(depth));
  // A step names what it is in its category, which the stylesheet colours by.
  if (spec.kind === "step" && event.payload && event.payload.category) {
    li.dataset.category = event.payload.category;
  }
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

  const row = { li, head, detail, count, time, depth, children: null };
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
  const children = [...row.children.children];
  if (!children.length) return;
  row.li.dataset.nested = "1";
  const onlyCalls = children.every((child) => ["model", "tool"].includes(child.dataset.kind));
  row.count.textContent = plural(children.length, onlyCalls ? "call" : "step");
  const holdsGroups = row.children.querySelector(":scope > .ev > .ev-children") !== null;
  if (!holdsGroups && row.li.dataset.kind !== "error") toggleGroup(row);
}

// A *_finished event completes the row its *_started opened, rather than adding a
// second line — so the trace reads as a list of steps, not a log of transitions.
function completeRow(row, event) {
  row.li.dataset.live = "0";
  if (event.payload && event.payload.status === "error") row.li.dataset.kind = "error";
  setDetail(row, event);
  row.time.textContent = formatDuration(event.duration_ms);
  finishGroup(row);
}

function placeRow(row, parent) {
  (parent ? parent.children : eventsEl).appendChild(row.li);
  scrollToEnd(eventsEl.parentElement);
}

function labelFor(event, spec) {
  return spec.opens === "Pipeline" || spec.closes === "Pipeline" ? "Pipeline" : event.label;
}

// Rows of open spans by span id, and the parent of every span seen, so an event whose
// parent is not drawn (a sandbox lease, say) still lands under the nearest one that is.
const spanRows = new Map();
const spanParents = new Map();

function rowFor(spanId) {
  let id = spanId;
  while (id && !spanRows.has(id)) id = spanParents.get(id);
  return id ? spanRows.get(id) : null;
}

// Events with span ids form an exact tree, however the run interleaves them.
function addSpanEvent(event, spec) {
  const label = labelFor(event, spec);
  if (spec.closes) {
    const row = spanRows.get(event.span_id);
    if (row) {
      completeRow(row, event);
      return;
    }
  }

  const parent = rowFor(event.parent_id);
  const row = makeRow(event, spec, label, parent ? parent.depth + 1 : 0);
  setDetail(row, event);
  if (spec.opens) {
    row.li.dataset.live = "1";
    spanRows.set(event.span_id, row);
  } else {
    row.time.textContent = formatDuration(event.duration_ms);
  }
  placeRow(row, parent);
}

// Traces stored before events carried span ids: the tree is rebuilt from the order
// of the events, each *_started opening a group until its *_finished arrives.
function addOrderedEvent(event, spec) {
  const label = labelFor(event, spec);
  const key = `${spec.kind}:${label}`;

  if (spec.closes && openRows.has(key)) {
    const row = openRows.get(key);
    openRows.delete(key);
    const at = openGroups.indexOf(row);
    if (at >= 0) openGroups.splice(at);
    completeRow(row, event);
    return;
  }

  const parent = openGroups.length ? openGroups[openGroups.length - 1] : null;
  const row = makeRow(event, spec, label, openGroups.length);
  setDetail(row, event);
  if (spec.opens) {
    row.li.dataset.live = "1";
    openRows.set(key, row);
  } else {
    row.time.textContent = formatDuration(event.duration_ms);
  }
  placeRow(row, parent);
  if (spec.opens) openGroups.push(row);
}

function addEvent(event) {
  const spec = RENDER[event.type];
  if (event.span_id) spanParents.set(event.span_id, event.parent_id || null);
  if (!spec || spec.skip) return;

  traceEvents.push(event);
  traceEmptyEl.hidden = true;
  traceSummaryEl.textContent = summarizeTrace(traceEvents);
  if (event.span_id) addSpanEvent(event, spec);
  else addOrderedEvent(event, spec);
}

// Steps still open when a run ends never reported a result.
function settleTrace() {
  for (const row of [...openRows.values(), ...spanRows.values()]) row.li.dataset.live = "0";
  openRows.clear();
  openGroups.length = 0;
  spanRows.clear();
  spanParents.clear();
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
