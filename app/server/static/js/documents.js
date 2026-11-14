// The documents panel: upload, URL import, deletion and quota usage.

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
// chunks and embeds it, then redraws the list from what the server now holds. A
// request that never gets an answer — the server restarting mid-upload — is reported
// like a refusal, so the buttons are always given back.
async function addDocument(path, body, label) {
  uploadLabelEl.dataset.busy = "1";
  linkSubmitEl.disabled = true;
  renderKnowledge(label);
  let result;
  try {
    result = await api(path, { method: "POST", body });
  } catch {
    result = { ok: false, status: 0, data: null };
  } finally {
    delete uploadLabelEl.dataset.busy;
    linkSubmitEl.disabled = false;
  }

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
