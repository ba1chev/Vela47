// The sign-in gate shown before the app.

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
