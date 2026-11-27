// The list of conversations and opening, starting and deleting one.

function relativeTime(iso) {
  const seconds = (Date.now() - new Date(iso).getTime()) / 1000;
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return new Date(iso).toLocaleDateString();
}

const PENCIL_ICON = `<svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true">
  <path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16zM13.5 6.5l4 4" fill="none" stroke="currentColor"
        stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

function makeSessionItem(session) {
  const li = document.createElement("li");
  li.className = "session-item";
  li.dataset.id = session.id;
  li.dataset.active = session.id === currentSessionId ? "1" : "0";

  const open = document.createElement("button");
  open.type = "button";
  open.className = "session-open";
  const title = document.createElement("span");
  title.className = "session-title";
  title.textContent = session.title;
  const time = document.createElement("span");
  time.className = "session-time";
  time.textContent = relativeTime(session.updated_at);
  open.append(title, time);
  open.addEventListener("click", () => openSession(session.id));
  open.addEventListener("dblclick", () => startRename(li, session));
  open.addEventListener("keydown", (e) => {
    if (e.key === "F2") startRename(li, session);
  });

  const rename = document.createElement("button");
  rename.type = "button";
  rename.className = "ghost session-edit";
  rename.innerHTML = PENCIL_ICON;
  rename.setAttribute("aria-label", `Rename “${session.title}”`);
  rename.title = "Rename";
  rename.addEventListener("click", () => startRename(li, session));

  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "ghost session-delete";
  remove.textContent = "×";
  remove.setAttribute("aria-label", `Delete “${session.title}”`);
  remove.addEventListener("click", () => deleteSession(remove, session.id));

  li.append(open, rename, remove);
  return li;
}

function renderSessions() {
  sessionListEl.replaceChildren(...sessions.map(makeSessionItem));
  sessionsEmptyEl.hidden = sessions.length > 0;
}

function markActive() {
  for (const item of sessionListEl.children) {
    item.dataset.active = item.dataset.id === currentSessionId ? "1" : "0";
  }
}

async function loadSessions() {
  const result = await api("/api/sessions");
  if (result.status === 401) {
    showGate(EXPIRED);
    return;
  }
  sessions = result.ok ? result.data : [];
  renderSessions();
}

function clearMessages() {
  messagesEl.replaceChildren(emptyEl);
  emptyEl.hidden = false;
  messagesEl.dataset.stick = "1";
  jumpEl.hidden = true;
}

function startNewChat() {
  if (run) return;
  currentSessionId = null;
  clearMessages();
  clearTrace();
  markActive();
  closeDrawer();
  inputEl.focus();
}

async function openSession(id) {
  if (run) return;
  const result = await api(`/api/sessions/${encodeURIComponent(id)}`);
  if (result.status === 401) {
    showGate(EXPIRED);
    return;
  }
  if (!result.ok) {
    await loadSessions();
    return;
  }

  currentSessionId = id;
  clearMessages();
  clearTrace();
  let lastAnswer = null;
  for (const message of result.data.messages) {
    if (message.role === "human") {
      addMessage(message.content, "user");
      continue;
    }
    const bubble = addAnswer(message.content, message.agent);
    completeAnswer(bubble, { sources: message.sources || [], trace: message.trace || [] });
    lastAnswer = bubble.parentElement;
  }
  // The trace panel shows how the latest answer came about, as it did when it arrived.
  if (lastAnswer && lastAnswer.trace.length) {
    renderTrace(lastAnswer.trace);
    lastAnswer.dataset.traced = "1";
  }
  scrollToEnd(messagesEl, true);
  markActive();
  closeDrawer();
  inputEl.focus();
}

// Renaming happens in place: the title becomes a field, Enter or leaving it saves,
// Escape puts the old title back. The list shows the new title at once and returns to
// the old one if the server refuses it.
function startRename(li, session) {
  if (li.dataset.editing === "1") return;
  li.dataset.editing = "1";

  const open = li.querySelector(".session-open");
  const input = makeElement("input", "session-rename");
  input.value = session.title;
  input.maxLength = 200;
  input.setAttribute("aria-label", "Conversation title");
  input.spellcheck = false;
  open.hidden = true;
  li.prepend(input);
  input.focus();
  input.select();

  let finished = false;
  const finish = (save, refocus) => {
    if (finished) return;
    finished = true;
    const title = input.value.split(/\s+/).filter(Boolean).join(" ");
    input.remove();
    open.hidden = false;
    delete li.dataset.editing;
    if (save && title && title !== session.title) renameSession(session, title, refocus);
    else if (refocus) open.focus();
  };

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      finish(true, true);
    } else if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      finish(false, true);
    }
  });
  input.addEventListener("blur", () => finish(true, false));
}

async function renameSession(session, title, refocus) {
  const previous = session.title;
  session.title = title;
  renderSessions();

  const result = await api(`/api/sessions/${encodeURIComponent(session.id)}`, {
    method: "PATCH",
    body: { title },
  });
  if (result.status === 401) {
    showGate(EXPIRED);
    return;
  }
  if (!result.ok) {
    session.title = previous;
    renderSessions();
    return;
  }
  session.title = result.data.title;
  renderSessions();
  if (refocus) sessionListEl.querySelector(`[data-id="${session.id}"] .session-open`)?.focus();
}

// Deleting asks twice: the first click arms the button for a few seconds, the second
// one deletes. Returns whether this click was the second.
function confirmTwice(button) {
  if (button.dataset.confirm === "1") return true;
  button.dataset.confirm = "1";
  button.textContent = "delete?";
  setTimeout(() => {
    if (!button.isConnected) return;
    button.dataset.confirm = "0";
    button.textContent = "×";
  }, 3000);
  return false;
}

async function deleteSession(button, id) {
  if (!confirmTwice(button)) return;

  const result = await api(`/api/sessions/${encodeURIComponent(id)}`, { method: "DELETE" });
  if (result.status === 401) {
    showGate(EXPIRED);
    return;
  }
  if (id === currentSessionId) startNewChat();
  await loadSessions();
}

newChatEl.addEventListener("click", startNewChat);
