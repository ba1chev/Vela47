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

function addMessage(text, variant) {
  emptyEl.hidden = true;
  const div = document.createElement("div");
  div.className = `msg ${variant}`;
  div.textContent = text;
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
