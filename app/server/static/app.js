const gateEl = document.getElementById("gate");
const gateFormEl = document.getElementById("gate-form");
const gateNameEl = document.getElementById("gate-name");
const gatePasswordEl = document.getElementById("gate-password");
const gateErrorEl = document.getElementById("gate-error");
const gateSubmitEl = document.getElementById("gate-submit");
const gateGuestEl = document.getElementById("gate-guest");

const appEl = document.getElementById("app");
const sessionListEl = document.getElementById("session-list");
const sessionsEmptyEl = document.getElementById("sessions-empty");
const newChatEl = document.getElementById("new-chat");
const drawerToggleEl = document.getElementById("drawer-toggle");
const agentSelectEl = document.getElementById("agent-select");

const knowledgeFileEl = document.getElementById("knowledge-file");
const uploadLabelEl = document.getElementById("upload-label");
const linkToggleEl = document.getElementById("link-toggle");
const linkFormEl = document.getElementById("link-form");
const linkUrlEl = document.getElementById("link-url");
const linkSubmitEl = document.getElementById("link-submit");
const usageEl = document.getElementById("usage");
const usageFillEl = document.getElementById("usage-fill");
const usageTextEl = document.getElementById("usage-text");
const knowledgeErrorEl = document.getElementById("knowledge-error");
const knowledgeListEl = document.getElementById("knowledge-list");
const knowledgeEmptyEl = document.getElementById("knowledge-empty");

const accountEl = document.getElementById("account");
const identityEl = document.getElementById("identity");
const accountMenuEl = document.getElementById("account-menu");
const accountNameEl = document.getElementById("account-name");
const accountRoleEl = document.getElementById("account-role");
const switchFormEl = document.getElementById("account-switch");
const switchPasswordEl = document.getElementById("switch-password");
const switchErrorEl = document.getElementById("switch-error");
const switchSubmitEl = document.getElementById("switch-submit");
const menuSwitchEl = document.getElementById("menu-switch");
const menuCreateUserEl = document.getElementById("menu-create-user");
const menuSignInEl = document.getElementById("menu-sign-in");
const menuSignOutEl = document.getElementById("menu-sign-out");

const createUserDialogEl = document.getElementById("create-user-dialog");
const createUserFormEl = document.getElementById("create-user-form");
const newUserNameEl = document.getElementById("new-user-name");
const newUserPasswordEl = document.getElementById("new-user-password");
const newUserTypeEl = document.getElementById("new-user-type");
const createUserErrorEl = document.getElementById("create-user-error");
const createUserOkEl = document.getElementById("create-user-ok");
const createUserSubmitEl = document.getElementById("create-user-submit");

const messagesEl = document.getElementById("messages");
const eventsEl = document.getElementById("events");
const traceEmptyEl = document.getElementById("trace-empty");
const emptyEl = document.getElementById("empty");
const emptyTitleEl = document.getElementById("empty-title");
const emptyHintEl = document.getElementById("empty-hint");
const statusEl = document.getElementById("status");
const formEl = document.getElementById("composer");
const inputEl = document.getElementById("input");
const sendEl = document.getElementById("send");

const EXPIRED = "Your session has expired — sign in again.";
const AGENT_STORAGE_KEY = "vela47.agent";

// What the empty chat says depends on who will answer it.
const EMPTY_TEXT = {
  deep: {
    title: "Ask something that needs more than one step.",
    hint: "The pipeline plans it, splits it into tasks, runs a subagent per task, then merges the results.",
  },
  rag: {
    title: "Ask about your documents.",
    hint: "The RAG agent searches them by meaning and by words, reranks what it finds, and answers with citations.",
  },
};

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

// Who is signed in, as /api/auth/me describes them, and the conversations they own.
// currentSessionId is null for a chat that has not been sent yet — the server creates
// the conversation with its first message, so an unsent chat exists only here.
let me = null;
let sessions = [];
let currentSessionId = null;
let knowledge = { documents: [], usage: null };

// ---------- server ----------

// One place that talks JSON to the server, so every caller gets the same shape back
// and can tell a 401 — sign in again — from any other failure.
async function api(path, { method = "GET", body } = {}) {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  if (response.status !== 204) {
    try { data = await response.json(); } catch { data = null; }
  }
  return { ok: response.ok, status: response.status, data };
}

// FastAPI reports its own validation failures as a list, everything else as a string.
function errorText(result, fallback) {
  const detail = result.data && result.data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join("; ");
  return fallback;
}

// ---------- gate ----------

function showGate(message) {
  closeMenu();
  closeDrawer();
  if (createUserDialogEl.open) createUserDialogEl.close();
  me = null;
  sessions = [];
  currentSessionId = null;
  knowledge = { documents: [], usage: null };
  closeLinkForm();
  appEl.hidden = true;
  gateEl.hidden = false;
  gateErrorEl.textContent = message || "";
  gateErrorEl.hidden = !message;
  gatePasswordEl.value = "";
  gateSubmitEl.disabled = false;
  gateGuestEl.disabled = false;
  gateNameEl.focus();
}

async function enterApp(identity) {
  me = identity;
  gateEl.hidden = true;
  appEl.hidden = false;
  renderIdentity();
  startNewChat();
  await Promise.all([loadSessions(), loadKnowledge()]);
}

async function signInWith(path, body) {
  gateSubmitEl.disabled = true;
  gateGuestEl.disabled = true;
  gateErrorEl.hidden = true;

  const result = await api(path, { method: "POST", body });
  if (result.ok) {
    await enterApp(result.data);
    return;
  }

  gateErrorEl.textContent = errorText(result, "Could not sign in.");
  gateErrorEl.hidden = false;
  gateSubmitEl.disabled = false;
  gateGuestEl.disabled = false;
  gatePasswordEl.select();
}

gateFormEl.addEventListener("submit", (e) => {
  e.preventDefault();
  const name = gateNameEl.value.trim();
  const password = gatePasswordEl.value;
  if (!name || !password) {
    gateErrorEl.textContent = "Enter your name and password.";
    gateErrorEl.hidden = false;
    return;
  }
  signInWith("/api/auth/login", { name, password });
});

gateGuestEl.addEventListener("click", () => signInWith("/api/auth/guest"));

// ---------- account ----------

function renderIdentity() {
  const isGuest = me.entity_type === "guest";
  identityEl.dataset.role = me.role;
  identityEl.textContent = isGuest ? "guest" : `${me.name} · ${me.role}`;
  accountNameEl.textContent = isGuest ? "Guest" : me.name;
  accountRoleEl.textContent = me.role;

  // Only an admin entity can hold both roles, so only an admin ever sees the switch.
  menuSwitchEl.hidden = me.entity_type !== "admin";
  menuSwitchEl.textContent = me.role === "admin" ? "Work as user" : "Work as admin";
  menuCreateUserEl.hidden = me.role !== "admin";
  menuSignInEl.hidden = !isGuest;
  menuSignOutEl.hidden = isGuest;
}

function openMenu() {
  accountMenuEl.hidden = false;
  identityEl.setAttribute("aria-expanded", "true");
}

function closeMenu() {
  accountMenuEl.hidden = true;
  identityEl.setAttribute("aria-expanded", "false");
  switchFormEl.hidden = true;
  switchPasswordEl.value = "";
  switchErrorEl.hidden = true;
}

identityEl.addEventListener("click", () => {
  if (accountMenuEl.hidden) openMenu();
  else closeMenu();
});

document.addEventListener("click", (e) => {
  if (!accountMenuEl.hidden && !accountEl.contains(e.target)) closeMenu();
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (!accountMenuEl.hidden) {
    closeMenu();
    identityEl.focus();
  }
  closeDrawer();
});

// Switching role is a fresh sign-in: the role is fixed inside the session token, and
// the server asks for the password again before handing out admin rights.
menuSwitchEl.addEventListener("click", () => {
  switchSubmitEl.textContent = me.role === "admin" ? "Switch to user" : "Switch to admin";
  switchFormEl.hidden = false;
  switchErrorEl.hidden = true;
  switchPasswordEl.focus();
});

switchFormEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const role = me.role === "admin" ? "user" : "admin";
  switchSubmitEl.disabled = true;
  const result = await api("/api/auth/login", {
    method: "POST",
    body: { name: me.name, password: switchPasswordEl.value, role },
  });
  switchSubmitEl.disabled = false;

  if (!result.ok) {
    switchErrorEl.textContent = errorText(result, "Could not switch role.");
    switchErrorEl.hidden = false;
    switchPasswordEl.select();
    return;
  }

  me = result.data;
  renderIdentity();
  closeMenu();
});

async function signOut() {
  if (stream) return;
  await api("/api/auth/logout", { method: "POST" });
  clearMessages();
  clearTrace();
  showGate();
}

menuSignOutEl.addEventListener("click", signOut);
menuSignInEl.addEventListener("click", signOut);

// ---------- create user ----------

menuCreateUserEl.addEventListener("click", () => {
  closeMenu();
  createUserFormEl.reset();
  createUserErrorEl.hidden = true;
  createUserOkEl.hidden = true;
  createUserDialogEl.showModal();
  newUserNameEl.focus();
});

document.getElementById("create-user-cancel").addEventListener("click", () => {
  createUserDialogEl.close();
});

createUserFormEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  createUserErrorEl.hidden = true;
  createUserOkEl.hidden = true;
  createUserSubmitEl.disabled = true;

  const result = await api("/api/iam/entities", {
    method: "POST",
    body: {
      type: newUserTypeEl.value,
      name: newUserNameEl.value.trim(),
      password: newUserPasswordEl.value,
    },
  });
  createUserSubmitEl.disabled = false;

  if (result.status === 401) {
    showGate(EXPIRED);
    return;
  }
  if (!result.ok) {
    createUserErrorEl.textContent = errorText(result, "Could not create the user.");
    createUserErrorEl.hidden = false;
    return;
  }

  // The dialog stays open after success so several accounts can be made in a row.
  createUserOkEl.textContent = `Created ${result.data.type} “${result.data.name}”.`;
  createUserOkEl.hidden = false;
  newUserNameEl.value = "";
  newUserPasswordEl.value = "";
  newUserNameEl.focus();
});

// ---------- conversations ----------

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

// ---------- agent ----------

// Remembered per browser, as a convenience only: storage can be unavailable, and then
// the picker simply starts on the deep agent every time.
function loadAgentChoice() {
  try {
    const saved = localStorage.getItem(AGENT_STORAGE_KEY);
    if (saved && EMPTY_TEXT[saved]) agentSelectEl.value = saved;
  } catch { /* no storage: keep the default */ }
  renderEmptyText();
}

function renderEmptyText() {
  const text = EMPTY_TEXT[agentSelectEl.value] || EMPTY_TEXT.deep;
  emptyTitleEl.textContent = text.title;
  emptyHintEl.textContent = text.hint;
}

agentSelectEl.addEventListener("change", () => {
  try { localStorage.setItem(AGENT_STORAGE_KEY, agentSelectEl.value); } catch { /* not saved */ }
  renderEmptyText();
});

// ---------- documents ----------

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(bytes < 10 * 1024 ? 1 : 0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// The limit is drawn from what the server reports with every listing and upload, so
// the bar always shows the storage as it is now rather than as it was at sign-in.
function renderUsage() {
  const usage = knowledge.usage;
  if (!usage) {
    usageFillEl.style.width = "0";
    usageTextEl.textContent = "";
    return;
  }
  const share = Math.min(1, usage.used_bytes / usage.max_bytes);
  usageFillEl.style.width = `${(share * 100).toFixed(1)}%`;
  usageEl.dataset.level = share >= 0.85 ? "high" : "normal";
  const count = knowledge.documents.length;
  usageTextEl.textContent =
    `${formatBytes(usage.used_bytes)} of ${formatBytes(usage.max_bytes)} · ` +
    `${count} ${count === 1 ? "document" : "documents"}`;
}

function makeKnowledgeItem(doc, pending) {
  const li = makeElement("li", "knowledge-item");
  if (pending) li.dataset.pending = "1";

  const info = makeElement("div", "knowledge-info");
  const name = makeElement("span", "knowledge-name");
  name.textContent = doc.title;
  name.title = doc.title;
  const meta = makeElement("span", "knowledge-meta");
  meta.textContent = pending
    ? "indexing…"
    : `${formatBytes(doc.size_bytes)} · ${doc.chunk_count} ${doc.chunk_count === 1 ? "chunk" : "chunks"}`;
  info.append(name, meta);
  li.append(info);

  if (!pending) {
    const remove = makeElement("button", "ghost knowledge-delete");
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Delete “${doc.title}”`);
    remove.addEventListener("click", () => deleteDocument(remove, doc.id));
    li.append(remove);
  }
  return li;
}

function makeElement(tag, className) {
  const element = document.createElement(tag);
  element.className = className;
  return element;
}

function renderKnowledge(pendingTitle) {
  const items = knowledge.documents.map((current) => makeKnowledgeItem(current, false));
  if (pendingTitle) items.unshift(makeKnowledgeItem({ title: pendingTitle }, true));
  knowledgeListEl.replaceChildren(...items);
  knowledgeEmptyEl.hidden = items.length > 0;
  renderUsage();
}

async function loadKnowledge() {
  const result = await api("/api/knowledge");
  if (result.status === 401) {
    showGate(EXPIRED);
    return;
  }
  if (result.ok) knowledge = result.data;
  renderKnowledge();
}

function showKnowledgeError(text) {
  knowledgeErrorEl.textContent = text;
  knowledgeErrorEl.hidden = !text;
}

// PDF and Word files cannot be read as text in the browser, so they travel as base64
// and the server extracts their text. Everything else is read here and sent as text.
const BINARY_EXTENSIONS = [".pdf", ".docx"];
const PAGE_EXTENSIONS = [".html", ".htm"];

function hasExtension(file, extensions) {
  const name = file.name.toLowerCase();
  return extensions.some((extension) => name.endsWith(extension));
}

// btoa takes a string of bytes, and spreading a whole file into one call would overflow
// the argument limit, so the bytes are converted a slice at a time.
function toBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let index = 0; index < bytes.length; index += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
  }
  return btoa(binary);
}

// Shared by uploads and links: shows the document as pending while the server reads,
// chunks and embeds it, then redraws the list from what the server now holds.
async function addDocument(path, body, label) {
  uploadLabelEl.dataset.busy = "1";
  linkSubmitEl.disabled = true;
  renderKnowledge(label);
  const result = await api(path, { method: "POST", body });
  delete uploadLabelEl.dataset.busy;
  linkSubmitEl.disabled = false;

  if (result.status === 401) {
    showGate(EXPIRED);
    return false;
  }
  if (!result.ok) showKnowledgeError(errorText(result, `“${label}” could not be added.`));
  await loadKnowledge();
  return result.ok;
}

// Limits are checked first against what the server last reported, which turns the
// common failure into an instant message instead of a refused upload; the server checks
// them again, since it is the one that has to be right. Only plain text can be measured
// here — how much text a page, a PDF or a Word file holds is known once it is extracted.
async function uploadDocument(file) {
  showKnowledgeError("");
  const usage = knowledge.usage;

  if (usage && usage.max_upload_bytes && file.size > usage.max_upload_bytes) {
    showKnowledgeError(`“${file.name}” is ${formatBytes(file.size)}; a file may be at most ${formatBytes(usage.max_upload_bytes)}.`);
    return;
  }

  const binary = hasExtension(file, BINARY_EXTENSIONS);
  const body = { title: file.name, content_type: file.type || null };
  try {
    if (binary) body.content_base64 = toBase64(await file.arrayBuffer());
    else body.content = await file.text();
  } catch {
    showKnowledgeError(`“${file.name}” could not be read.`);
    return;
  }

  if (!binary && body.content.includes("\u0000")) {
    showKnowledgeError(`“${file.name}” is not a text file. Upload text, Markdown, HTML, PDF or Word (.docx).`);
    return;
  }
  if (!binary && !hasExtension(file, PAGE_EXTENSIONS)) {
    const size = new TextEncoder().encode(body.content).length;
    if (usage && size > usage.max_file_bytes) {
      showKnowledgeError(`“${file.name}” is ${formatBytes(size)}; one document may be at most ${formatBytes(usage.max_file_bytes)}.`);
      return;
    }
    if (usage && usage.used_bytes + size > usage.max_bytes) {
      showKnowledgeError(`“${file.name}” does not fit in the ${formatBytes(usage.max_bytes - usage.used_bytes)} you have left.`);
      return;
    }
  }

  await addDocument("/api/knowledge", body, file.name);
}

knowledgeFileEl.addEventListener("change", () => {
  const file = knowledgeFileEl.files && knowledgeFileEl.files[0];
  knowledgeFileEl.value = "";
  if (file) uploadDocument(file);
});

function closeLinkForm() {
  linkFormEl.hidden = true;
  linkToggleEl.setAttribute("aria-expanded", "false");
  linkUrlEl.value = "";
}

linkToggleEl.addEventListener("click", () => {
  if (!linkFormEl.hidden) {
    closeLinkForm();
    return;
  }
  linkFormEl.hidden = false;
  linkToggleEl.setAttribute("aria-expanded", "true");
  linkUrlEl.focus();
});

// The page is fetched by the server, which only reaches public addresses, so the form
// only checks that this is a full web address before asking.
linkFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = linkUrlEl.value.trim();
  showKnowledgeError("");
  if (!/^https?:\/\/\S+$/i.test(url)) {
    showKnowledgeError("Enter a full address, starting with https://.");
    linkUrlEl.focus();
    return;
  }
  if (await addDocument("/api/knowledge/url", { url }, url)) closeLinkForm();
});

linkUrlEl.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeLinkForm();
    linkToggleEl.focus();
  }
});

async function deleteDocument(button, id) {
  if (!confirmTwice(button)) return;
  showKnowledgeError("");
  const result = await api(`/api/knowledge/${encodeURIComponent(id)}`, { method: "DELETE" });
  if (result.status === 401) {
    showGate(EXPIRED);
    return;
  }
  await loadKnowledge();
}

// ---------- drawer ----------

function openDrawer() {
  appEl.dataset.drawer = "open";
  drawerToggleEl.setAttribute("aria-expanded", "true");
}

function closeDrawer() {
  delete appEl.dataset.drawer;
  drawerToggleEl.setAttribute("aria-expanded", "false");
}

drawerToggleEl.addEventListener("click", (e) => {
  e.stopPropagation();
  if (appEl.dataset.drawer === "open") closeDrawer();
  else openDrawer();
});

document.addEventListener("click", (e) => {
  if (appEl.dataset.drawer !== "open") return;
  if (!document.getElementById("sessions").contains(e.target)) closeDrawer();
});

// ---------- chat ----------

function setStatus(state, text) {
  statusEl.dataset.state = state;
  statusEl.textContent = text;
}

function setBusy(busy) {
  sendEl.disabled = busy;
  inputEl.disabled = busy;
  if (busy) appEl.dataset.busy = "1";
  else delete appEl.dataset.busy;
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

function clearTrace() {
  eventsEl.replaceChildren();
  openRows.clear();
  traceEmptyEl.hidden = false;
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

function finish(placeholder) {
  if (stream) { stream.close(); stream = null; }
  if (placeholder && placeholder.isConnected) placeholder.remove();
  // Any step still open when the stream ends never reported a result.
  for (const row of openRows.values()) row.li.dataset.live = "0";
  openRows.clear();
  setBusy(false);
  inputEl.focus();
}

async function send(message) {
  addMessage(message, "user");
  const placeholder = addThinking();
  setBusy(true);
  setStatus("running", "running");

  // A session can expire while the page is open, and EventSource cannot tell a 401
  // from a dropped connection — so it is checked before every stream instead.
  const check = await api("/api/auth/me");
  if (!check.ok) {
    finish(placeholder);
    setStatus("idle", "idle");
    showGate(EXPIRED);
    return;
  }

  const agent = agentSelectEl.value;
  const params = new URLSearchParams({ message, agent });
  if (currentSessionId) params.set("session_id", currentSessionId);
  stream = new EventSource(`/api/chat/stream?${params}`);

  stream.addEventListener("trace", (e) => addEvent(JSON.parse(e.data)));

  // The first frame names the conversation. A new one is shown in the list straight
  // away; the server only stores it once the answer is complete, so a failed run
  // forgets it again.
  let createdSessionId = null;
  stream.addEventListener("session", (e) => {
    const session = JSON.parse(e.data);
    currentSessionId = session.id;
    if (session.new) {
      createdSessionId = session.id;
      sessions = [{ ...session, updated_at: new Date().toISOString() }, ...sessions];
      renderSessions();
    }
    markActive();
  });

  // The first chunk replaces the thinking dots with a real bubble; the rest append
  // to it, so the answer is written into the page as the model produces it.
  let streamed = null;
  stream.addEventListener("chunk", (e) => {
    const { text } = JSON.parse(e.data);
    if (!text) return;
    if (!streamed) {
      placeholder.remove();
      streamed = addMessage("", "ai");
      streamed.dataset.agent = agent;
    }
    streamed.textContent += text;
    messagesEl.scrollTop = messagesEl.scrollHeight;
  });

  stream.addEventListener("answer", (e) => {
    const { content, agent: answeredBy, sources } = JSON.parse(e.data);
    // With chunks the bubble is already complete, so the final frame only has to
    // cover the case where nothing streamed at all.
    if (streamed) {
      if (!streamed.textContent) streamed.textContent = content || "(empty answer)";
    } else {
      placeholder.remove();
      streamed = addMessage(content || "(empty answer)", "ai");
    }
    streamed.dataset.agent = answeredBy || agent;
    if (sources && sources.length) renderSources(sources);
    setStatus("idle", "idle");
    finish(null);
    loadSessions();
  });

  stream.addEventListener("error", (e) => {
    // EventSource reuses "error" for transport failures, which carry no data.
    const text = e.data
      ? JSON.parse(e.data).message
      : "Connection to the server was lost.";
    placeholder.remove();
    addMessage(text, "err");
    setStatus("error", "error");
    if (createdSessionId && currentSessionId === createdSessionId) currentSessionId = null;
    finish(null);
    loadSessions();
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

document.getElementById("clear").addEventListener("click", clearTrace);

// ---------- start ----------

// An existing session cookie skips the gate; anything else — no cookie, an expired
// one, a server restarted with a new signing key — lands on it.
async function boot() {
  loadAgentChoice();
  const result = await api("/api/auth/me");
  if (result.ok) await enterApp(result.data);
  else showGate();
}

boot();
