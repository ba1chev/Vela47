// The "Create user" dialog an admin opens from the account menu.

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
