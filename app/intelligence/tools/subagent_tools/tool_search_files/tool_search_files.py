from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolSearchFilesInput


class ToolSearchFiles(ToolBase[ToolSearchFilesInput, str]):
    """Finds text in the sandbox and returns the matching lines themselves.

    Returning the content rather than a list of file names is the whole point. A
    subagent owns exactly one tool, so one that answered "it is in sort.py" would
    leave it with no way to open sort.py — the match has to arrive already readable.

    Results are capped because they are fed straight back into a context window;
    an unbounded match list would evict the task the agent is working on."""

    MAX_MATCHES = 40
    MAX_LINE_CHARS = 200

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__()
        self._sandbox_env: SandboxEnv = sandbox_env

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return (
            "Search every file in your workspace for a piece of text and get back the "
            "matching lines with their file and line number. Use it to find out what "
            "already exists before you draw a conclusion."
        )

    @property
    def input_schema(self) -> type[ToolSearchFilesInput]:
        return ToolSearchFilesInput

    def execute(self, input: ToolSearchFilesInput) -> str:
        files = self._sandbox_env.list_files()

        if not files:
            return "The workspace is empty — there is nothing to search yet."

        needle = input.query.lower()
        matches: list[str] = []

        for current_file in files:
            try:
                content = self._sandbox_env.read_file(current_file)
            except (OSError, ValueError):
                continue

            for index, current_line in enumerate(content.splitlines(), start = 1):
                if needle in current_line.lower():
                    matches.append(
                        f"{current_file}:{index}: {current_line.strip()[:self.MAX_LINE_CHARS]}"
                    )
                    if len(matches) >= self.MAX_MATCHES:
                        return self._format(input.query, matches, truncated = True)

        return self._format(input.query, matches, truncated = False)

    def _format(self, query: str, matches: list[str], truncated: bool) -> str:
        if not matches:
            return f"No match for '{query}' in any of the workspace files."

        header = f"{len(matches)} match(es) for '{query}':"
        footer = "\n… more matches exist; narrow the query." if truncated else ""
        return header + "\n" + "\n".join(matches) + footer
