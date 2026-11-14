SUBAGENT_PEER_PROMPT = """

# The worker who wrote the code
The {peer} worker that wrote the code in this workspace can still change it, and message_worker sends it a message and returns its answer.
- When a test fails or you find a real problem because the code is wrong, send it the exact case — file, function, input, expected and actual result — and ask it to fix the code. Do not change the code yourself.
- Then check its fix with your own tools: run the tests or read the file again.
- Do not ask it what your tools can show you. You can send it at most {max_messages} messages.
- Your report says what it fixed and what is still wrong."""
