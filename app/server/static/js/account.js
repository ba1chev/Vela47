// The identity pill and its menu: role switch, sign in and sign out.

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
