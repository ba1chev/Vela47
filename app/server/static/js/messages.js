// Messages, answers with their sources and actions, and the thinking placeholder.

// A run sends many small events a second. Scrolling after each one makes the browser
// lay the page out again every time, so requests are collected and every list that
// asked is scrolled once, on the next frame.
const pendingScrolls = new Set();
const STICK_DISTANCE = 80;

function isNearEnd(element) {
  return element.scrollHeight - element.scrollTop - element.clientHeight < STICK_DISTANCE;
}

// A list follows new content only while it is scrolled to its end: someone who scrolled
// up to read an earlier part is left where they are, and the chat offers a way back.
function followScroll(element) {
  element.dataset.stick = "1";
  element.addEventListener("scroll", () => {
    element.dataset.stick = isNearEnd(element) ? "1" : "0";
    if (element === messagesEl) renderJump();
  }, { passive: true });
}

function scrollToEnd(element, force = false) {
  if (force) element.dataset.stick = "1";
  if (pendingScrolls.size === 0) {
    requestAnimationFrame(() => {
      for (const current of pendingScrolls) {
        if (current.dataset.stick !== "0") current.scrollTop = current.scrollHeight;
      }
      pendingScrolls.clear();
      renderJump();
    });
  }
  pendingScrolls.add(element);
}

function renderJump() {
  jumpEl.hidden = messagesEl.dataset.stick !== "0" || isNearEnd(messagesEl);
}

followScroll(messagesEl);
followScroll(eventsEl.parentElement);

jumpEl.addEventListener("click", () => {
  messagesEl.dataset.stick = "1";
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: REDUCED_MOTION ? "auto" : "smooth" });
});

// An agent answers in Markdown. marked turns it into HTML and DOMPurify then strips
// anything that could run, so neither the model nor a page it read can put a script or
// a handler into the page. Links open in a new tab. Without the two libraries the
// answer is shown as plain text.
function renderAnswer(element, text) {
  element.source = text;
  if (typeof marked === "undefined" || typeof DOMPurify === "undefined") {
    element.textContent = text;
    return;
  }
  element.classList.add("markdown");
  element.innerHTML = DOMPurify.sanitize(marked.parse(text, { gfm: true }));
  for (const link of element.querySelectorAll("a")) {
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  }
}

function addMessage(text, variant) {
  emptyEl.hidden = true;
  const div = makeElement("div", `msg ${variant}`);
  div.textContent = text;
  messagesEl.appendChild(div);
  scrollToEnd(messagesEl, variant === "user");
  return div;
}

// An answer is its bubble plus what belongs to it, kept together: the sources it cites
// and a line with what the run cost and what can be done with the answer.
function addAnswer(text, agent) {
  emptyEl.hidden = true;
  const wrap = makeElement("article", "answer");
  const bubble = makeElement("div", "msg ai");
  if (agent) bubble.dataset.agent = agent;
  renderAnswer(bubble, text);
  wrap.append(bubble);
  messagesEl.appendChild(wrap);
  scrollToEnd(messagesEl);
  return bubble;
}

// Completes an answer once it is whole: its sources, its citations made clickable, and
// the line under it. The run's trace stays with the answer, so it can be shown again.
function completeAnswer(bubble, { sources = [], trace = [] } = {}) {
  const wrap = bubble.parentElement;
  wrap.trace = trace;
  if (sources.length) {
    const box = renderSources(wrap, sources);
    linkCitations(bubble, box, sources);
  }

  const meta = makeElement("div", "msg-meta");
  const stats = summarizeTrace(trace);
  if (stats) {
    const span = makeElement("span", "meta-stats");
    span.textContent = stats;
    meta.append(span);
  }
  meta.append(metaAction("Copy", (button) => copyText(button, bubble.source || bubble.textContent)));
  if (trace.length) meta.append(metaAction("Trace", () => showAnswerTrace(wrap)));
  wrap.append(meta);
  scrollToEnd(messagesEl);
}

function metaAction(label, onClick) {
  const button = makeElement("button", "meta-action");
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", () => onClick(button));
  return button;
}

async function copyText(button, text) {
  const label = button.textContent;
  try {
    await navigator.clipboard.writeText(text);
    button.textContent = "Copied";
  } catch {
    button.textContent = "Copy failed";
  }
  setTimeout(() => { button.textContent = label; }, 1500);
}

function showAnswerTrace(wrap) {
  renderTrace(wrap.trace || []);
  wrap.dataset.traced = "1";
  if (window.matchMedia("(max-width: 880px)").matches) openDrawer("trace");
}

// Something went wrong or the run was stopped: said in the chat, where the caller adds
// a way to ask the same question again.
function addNotice(text, variant) {
  emptyEl.hidden = true;
  const wrap = makeElement("div", "answer");
  const bubble = makeElement("div", `msg ${variant}`);
  bubble.textContent = text;
  wrap.append(bubble);
  messagesEl.appendChild(wrap);
  scrollToEnd(messagesEl);
  return wrap;
}

// While a run works the placeholder says which step it is on and how long it has
// taken, since a deep run can stay silent for minutes before the answer arrives.
function addThinking() {
  emptyEl.hidden = true;
  const div = makeElement("div", "msg ai thinking");
  const dots = makeElement("span", "dots");
  dots.innerHTML = "<i></i><i></i><i></i>";
  const label = makeElement("span", "thinking-label");
  label.textContent = "Starting…";
  const time = makeElement("span", "thinking-time");
  div.append(dots, label, time);
  div.setAttribute("role", "status");
  messagesEl.appendChild(div);
  scrollToEnd(messagesEl, true);
  return div;
}

// The passages a RAG answer was written from, under the answer, numbered as the
// answer cites them — so "[2]" can always be checked against what it came from.
// Folded by default: the answer comes first, and the titles in the summary tell
// which documents it drew on.
function renderSources(wrap, sources) {
  const box = makeElement("details", "sources");
  const summary = makeElement("summary", "sources-summary");
  const titles = [...new Set(sources.map((source) => source.title))];
  const shown = titles.slice(0, 2).join(", ") + (titles.length > 2 ? ` +${titles.length - 2}` : "");
  summary.textContent = `${sources.length} ${sources.length === 1 ? "source" : "sources"} · ${shown}`;
  box.append(summary);

  for (const source of sources) {
    const item = makeElement("div", "source");
    item.dataset.index = String(source.index);
    const head = makeElement("span", "source-head");
    const score = source.score == null ? "" : ` · relevance ${source.score}/10`;
    head.textContent = titles.length > 1
      ? `[${source.index}] ${source.title}${score}`
      : `[${source.index}]${score}`;
    const excerpt = makeElement("span", "source-excerpt");
    excerpt.textContent = source.excerpt;
    item.append(head, excerpt);
    box.append(item);
  }
  wrap.append(box);
  return box;
}

// "[2]" in an answer becomes a button that opens the sources and points at passage 2.
// Only numbers the answer really has a source for are linked, and never inside code
// or an existing link.
function linkCitations(bubble, box, sources) {
  const byIndex = new Map(sources.map((source) => [String(source.index), source]));
  const walker = document.createTreeWalker(bubble, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) => node.parentElement.closest("code, pre, a")
      ? NodeFilter.FILTER_REJECT
      : NodeFilter.FILTER_ACCEPT,
  });
  const nodes = [];
  while (walker.nextNode()) {
    if (/\[\d+\]/.test(walker.currentNode.nodeValue)) nodes.push(walker.currentNode);
  }

  for (const node of nodes) {
    const parts = node.nodeValue.split(/(\[\d+\])/);
    const fragment = document.createDocumentFragment();
    for (const part of parts) {
      const match = part.match(/^\[(\d+)\]$/);
      const source = match && byIndex.get(match[1]);
      if (!source) {
        if (part) fragment.append(part);
        continue;
      }
      const cite = makeElement("button", "cite");
      cite.type = "button";
      cite.textContent = match[1];
      cite.title = source.title;
      cite.setAttribute("aria-label", `Source ${match[1]}: ${source.title}`);
      cite.addEventListener("click", () => focusSource(box, match[1]));
      fragment.append(cite);
    }
    node.replaceWith(fragment);
  }
}

function focusSource(box, index) {
  box.open = true;
  const item = box.querySelector(`.source[data-index="${index}"]`);
  if (!item) return;
  item.dataset.flash = "0";
  void item.offsetWidth;
  item.dataset.flash = "1";
  item.scrollIntoView({ block: "nearest", behavior: REDUCED_MOTION ? "auto" : "smooth" });
}
