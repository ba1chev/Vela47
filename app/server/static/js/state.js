// What the page knows across all of its parts: the open stream, who is signed in,
// their conversations and their documents.

const EXPIRED = "Your session has expired — sign in again.";

let stream = null;

// Who is signed in, as /api/auth/me describes them, and the conversations they own.
// currentSessionId is null for a chat that has not been sent yet — the server creates
// the conversation with its first message, so an unsent chat exists only here.
let me = null;
let sessions = [];
let currentSessionId = null;
let knowledge = { documents: [], usage: null };
