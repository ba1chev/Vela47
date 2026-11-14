// Messages, the thinking placeholder and RAG sources in the chat.

// A run sends many small events a second. Scrolling after each one makes the browser
// lay the page out again every time, so requests are collected and every list that
// asked is scrolled once, on the next frame.
const pendingScrolls = new Set();

function scrollToEnd(element) {
  if (pendingScrolls.size === 0) {
    requestAnimationFrame(() => {
      for (const current of pendingScrolls) current.scrollTop = current.scrollHeight;
      pendingScrolls.clear();
    });
  }
  pendingScrolls.add(element);
}

// An agent answers in Markdown. marked turns it into HTML and DOMPurify then strips
// anything that could run, so neither the model nor a page it read can put a script or
// a handler into the page. Links open in a new tab. Without the two libraries the
// answer is shown as plain text.
function renderAnswer(element, text) {
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
  const div = document.createElement("div");
  div.className = `msg ${variant}`;
  if (variant === "ai") renderAnswer(div, text);
  else div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function addThinking() {
  emptyEl.hidden = true;
  const div = document.createElement("div");
  div.className = "msg ai thinking";
  div.innerHTML = "<i></i><i></i><i></i>";
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

// The passages a RAG answer was written from, under the answer, numbered as the
// answer cites them — so "[2]" can always be checked against what it came from.
function renderSources(sources) {
  const box = makeElement("div", "sources");
  for (const source of sources) {
    const item = makeElement("div", "source");
    const head = makeElement("span", "source-head");
    const score = source.score == null ? "" : ` · relevance ${source.score}/10`;
    head.textContent = `[${source.index}] ${source.title}${score}`;
    const excerpt = makeElement("span", "source-excerpt");
    excerpt.textContent = source.excerpt;
    item.append(head, excerpt);
    box.append(item);
  }
  messagesEl.appendChild(box);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return box;
}
