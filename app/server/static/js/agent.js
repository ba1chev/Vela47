// The agent picker and what the empty chat says for each agent.

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
