import re
import fnmatch
import posixpath
from typing import Callable, Optional

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolSearchFilesInput


class ToolSearchFiles(ToolBase[ToolSearchFilesInput, str]):
    """Finds text in the sandbox and returns the matching lines themselves, like a grep
    over the workspace.

    Returning the content rather than a list of file names saves a turn: the match
    arrives already readable, and read_file is only needed for the context around it.
    A glob narrows the search to the files that matter, and a regular expression is
    there for the cases plain text cannot express — both optional, because a small
    model does best when the simple call is the default.

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
            "Search the files in your workspace for a piece of text and get back the "
            "matching lines with their file and line number. Use it to find out what "
            "already exists, and where, before you draw a conclusion."
        )

    @property
    def input_schema(self) -> type[ToolSearchFilesInput]:
        return ToolSearchFilesInput

    def _matcher(self, input: ToolSearchFilesInput) -> Callable[[str], bool]:
        if input.is_regex:
            pattern = re.compile(input.query, re.IGNORECASE)
            return lambda line: pattern.search(line) is not None
        needle = input.query.lower()
        return lambda line: needle in line.lower()

    def _selected(self, path: str, path_glob: Optional[str]) -> bool:
        if not path_glob:
            return True
        target = path if "/" in path_glob else posixpath.basename(path)
        return fnmatch.fnmatch(target, path_glob)

    def execute(self, input: ToolSearchFilesInput) -> str:
        files = [
            current_file
            for current_file in self._sandbox_env.list_files()
            if self._selected(current_file, input.path_glob)
        ]

        if not files:
            if input.path_glob:
                return f"No workspace file matches '{input.path_glob}'."
            return "The workspace is empty — there is nothing to search yet."

        try:
            matches_line = self._matcher(input)
        except re.error as error:
            return f"'{input.query}' is not a valid regular expression: {error}."

        matches: list[str] = []
        for current_file in files:
            try:
                content = self._sandbox_env.read_file(current_file)
            except (OSError, ValueError):
                continue

            for index, current_line in enumerate(content.splitlines(), start = 1):
                if matches_line(current_line):
                    matches.append(
                        f"{current_file}:{index}: {current_line.strip()[:self.MAX_LINE_CHARS]}"
                    )
                    if len(matches) >= self.MAX_MATCHES:
                        return self._format(input.query, matches, truncated = True)

        return self._format(input.query, matches, truncated = False)

    def _format(self, query: str, matches: list[str], truncated: bool) -> str:
        if not matches:
            return f"No match for '{query}' in the workspace files searched."

        header = f"{len(matches)} match(es) for '{query}':"
        footer = "\n… more matches exist; narrow the query or the path_glob." if truncated else ""
        return header + "\n" + "\n".join(matches) + footer
