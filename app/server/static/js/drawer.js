// The panes that slide over the chat on narrow screens: the conversations from the left
// and the trace from the right, one at a time, over a scrim that closes them.

const DRAWERS = {
  sessions: { toggle: drawerToggleEl, open: "Hide conversations", closed: "Show conversations" },
  trace: { toggle: traceToggleEl, open: "Hide trace", closed: "Show trace" },
};

function openDrawer(name = "sessions") {
  closeDrawer();
  const drawer = DRAWERS[name];
  appEl.dataset.drawer = name;
  drawer.toggle.setAttribute("aria-expanded", "true");
  drawer.toggle.setAttribute("aria-label", drawer.open);
  scrimEl.hidden = false;
}

function closeDrawer() {
  delete appEl.dataset.drawer;
  scrimEl.hidden = true;
  for (const drawer of Object.values(DRAWERS)) {
    drawer.toggle.setAttribute("aria-expanded", "false");
    drawer.toggle.setAttribute("aria-label", drawer.closed);
  }
}

function toggleDrawer(name) {
  if (appEl.dataset.drawer === name) closeDrawer();
  else openDrawer(name);
}

drawerToggleEl.addEventListener("click", () => toggleDrawer("sessions"));
traceToggleEl.addEventListener("click", () => toggleDrawer("trace"));
scrimEl.addEventListener("click", closeDrawer);
