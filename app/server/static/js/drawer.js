// The conversation list as a drawer on narrow screens.

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
