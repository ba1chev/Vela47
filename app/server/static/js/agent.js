// The agent switch in the composer and what the empty chat says for each agent.

const AGENT_STORAGE_KEY = "vela47.agent";

// What the empty chat says depends on who will answer it. The examples are sent as
// they are when clicked, so each one is a question the agent can actually take on.
const EMPTY_TEXT = {
  deep: {
    title: "Ask something that needs more than one step.",
    hint: "The pipeline plans it, splits it into tasks, runs a subagent per task, then merges the results.",
    examples: [
      "Write and test a Python function that checks for primes",
      "What is the square root of 1764, and is it a prime number?",
      "Compare asyncio and threads for I/O-bound work in Python",
    ],
  },
  rag: {
    title: "Ask about your documents.",
    hint: "The RAG agent searches them by meaning and by words, reranks what it finds, and answers with citations.",
    examples: [
      "Summarize the key points of my documents",
      "Which topics do my documents cover?",
      "List any numbers, limits or deadlines my documents mention",
    ],
  },
  ragWithoutDocuments: {
    title: "Add a document first.",
    hint: "The RAG agent answers only from your own documents. Upload a file or add a link under Documents, then ask about it.",
    examples: [],
  },
};

function currentAgent() {
  const checked = agentSwitchEl.querySelector("input:checked");
  return checked ? checked.value : "deep";
}

function setAgent(agent) {
  const input = agentSwitchEl.querySelector(`input[value="${agent}"]`);
  if (input) input.checked = true;
  renderEmptyText();
}

// Remembered per browser, as a convenience only: storage can be unavailable, and then
// the switch simply starts on the deep agent every time.
function loadAgentChoice() {
  try {
    const saved = localStorage.getItem(AGENT_STORAGE_KEY);
    if (saved === "deep" || saved === "rag") setAgent(saved);
  } catch { /* no storage: keep the default */ }
  renderEmptyText();
}

function renderEmptyText() {
  let text = EMPTY_TEXT[currentAgent()] || EMPTY_TEXT.deep;
  if (currentAgent() === "rag" && me && knowledge.documents.length === 0) {
    text = EMPTY_TEXT.ragWithoutDocuments;
  }
  emptyTitleEl.textContent = text.title;
  emptyHintEl.textContent = text.hint;

  const chips = text.examples.map((example) => {
    const chip = makeElement("button", "suggestion");
    chip.type = "button";
    chip.textContent = example;
    chip.addEventListener("click", () => submitMessage(example));
    return chip;
  });
  suggestionsEl.replaceChildren(...chips);
  suggestionsEl.hidden = chips.length === 0;
}

agentSwitchEl.addEventListener("change", () => {
  try { localStorage.setItem(AGENT_STORAGE_KEY, currentAgent()); } catch { /* not saved */ }
  renderEmptyText();
  inputEl.focus();
});
