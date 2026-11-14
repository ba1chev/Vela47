// The list of conversations and opening, starting and deleting one.

function relativeTime(iso) {
  const seconds = (Date.now() - new Date(iso).getTime()) / 1000;
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return new Date(iso).toLocaleDateString();
}

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

  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "ghost session-delete";
  remove.textContent = "×";
  remove.setAttribute("aria-label", `Delete “${session.title}”`);
  remove.addEventListener("click", () => deleteSession(remove, session.id));

  li.append(open, remove);
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
}

function startNewChat() {
  if (stream) return;
  currentSessionId = null;
  clearMessages();
  clearTrace();
  markActive();
  closeDrawer();
  inputEl.focus();
}

async function openSession(id) {
  if (stream) return;
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
  for (const message of result.data.messages) {
    const bubble = addMessage(message.content, message.role === "human" ? "user" : "ai");
    if (message.role === "ai" && message.agent) bubble.dataset.agent = message.agent;
    if (message.sources && message.sources.length) renderSources(message.sources);
  }
  markActive();
  closeDrawer();
  inputEl.focus();
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
