// Folding the conversations panel into a rail of icons on wide screens. It starts
// folded and the choice is remembered per browser. On narrow screens the same toggle
// closes the drawer instead, since a drawer is never folded.

const SIDEBAR_STORAGE_KEY = "vela47.sidebar";
const drawerQuery = window.matchMedia("(max-width: 1100px)");
const SIDEBAR_SHORTCUT = /Mac|iPhone|iPad/.test(navigator.platform) ? "\u2318B" : "Ctrl+B";

function sidebarOpen() {
  return appEl.dataset.sidebar !== "collapsed";
}

function labelSidebarToggle() {
  const label = drawerQuery.matches || sidebarOpen() ? "Close sidebar" : "Open sidebar";
  sidebarToggleEl.setAttribute("aria-label", label);
  sidebarToggleEl.title = `${label} (${SIDEBAR_SHORTCUT})`;
  sidebarToggleEl.setAttribute("aria-expanded", String(drawerQuery.matches || sidebarOpen()));
}

function setSidebar(open, remember = true) {
  if (open) delete appEl.dataset.sidebar;
  else appEl.dataset.sidebar = "collapsed";
  labelSidebarToggle();
  if (!remember) return;
  try { localStorage.setItem(SIDEBAR_STORAGE_KEY, open ? "open" : "collapsed"); } catch { /* not saved */ }
}

// Remembered as a convenience only: without storage the panel starts folded each time.
function loadSidebarChoice() {
  let saved = null;
  try { saved = localStorage.getItem(SIDEBAR_STORAGE_KEY); } catch { /* no storage */ }
  setSidebar(saved === "open", false);
}

function toggleSidebar() {
  if (drawerQuery.matches) toggleDrawer("sessions");
  else setSidebar(!sidebarOpen());
}

function flashDocuments() {
  const knowledgeEl = sessionsEl.querySelector(".knowledge");
  knowledgeEl.dataset.flash = "0";
  void knowledgeEl.offsetWidth;
  knowledgeEl.dataset.flash = "1";
}

sidebarToggleEl.addEventListener("click", toggleSidebar);
railNewChatEl.addEventListener("click", startNewChat);
railChatsEl.addEventListener("click", () => setSidebar(true));
railDocumentsEl.addEventListener("click", () => {
  setSidebar(true);
  flashDocuments();
});
drawerQuery.addEventListener("change", labelSidebarToggle);

// Ctrl+B, or Cmd+B on a Mac, as in most editors with a side panel.
document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() !== "b" || !(e.ctrlKey || e.metaKey) || e.altKey || e.shiftKey) return;
  if (appEl.hidden) return;
  e.preventDefault();
  toggleSidebar();
});
