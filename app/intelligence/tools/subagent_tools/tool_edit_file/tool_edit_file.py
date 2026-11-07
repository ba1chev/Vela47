from typing import Optional

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import unified_diff
from app.intelligence.tools import ToolEditFileInput
from app.intelligence.tools import python_syntax_warning


class ToolEditFile(ToolBase[ToolEditFileInput, str]):
    """Changes part of an existing file by replacing exact text, the way the edit tools of
    MCP's filesystem server and of coding agents do, and answers with a unified diff.

    Replacement is by content, never by line number: line numbers go stale with every
    edit, while the text the agent just read is what it actually means to change. The
    text has to occur exactly once, so an ambiguous edit is refused with the count
    instead of landing in the wrong place — unless replace_all says every occurrence is
    meant.

    Whole lines are matched with their indentation ignored, and the replacement is
    re-indented to where it lands. Small models reproduce code reliably but not its
    whitespace — they drop the leading indentation of the first line, or of all of them
    — and an otherwise correct edit failing over a tab, or landing with its second line
    at the wrong depth, is the commonest way this tool would be useless. Text that is
    only part of a line is matched exactly instead.

    Nothing is written unless the edit applies. The diff shows the agent what it really
    changed — the only reliable check that an edit did what was intended."""

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__()
        self._sandbox_env: SandboxEnv = sandbox_env

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return (
            "Change part of an existing file by replacing old_text with new_text, and get "
            "back a diff of what changed. Read the file first and copy old_text from it "
            "exactly, with enough lines that it appears only once. Prefer this to "
            "rewriting a whole file when only part of it needs to change."
        )

    @property
    def input_schema(self) -> type[ToolEditFileInput]:
        return ToolEditFileInput

    def _indentation(self, line: str) -> str:
        return line[:len(line) - len(line.lstrip())]

    def _reindent(self, new_lines: list[str], old_indent: str, file_indent: str) -> list[str]:
        first = next((current_line for current_line in new_lines if current_line.strip()), "")
        if self._indentation(first) == file_indent:
            return new_lines
        return [
            file_indent + current_line[len(old_indent):]
            if current_line.strip() and current_line.startswith(old_indent)
            else current_line
            for current_line in new_lines
        ]

    def _replace_lines(self, content: str, old_text: str, new_text: str) -> tuple[Optional[str], int]:
        lines = content.split("\n")
        old_lines = old_text.strip("\n").split("\n")
        wanted = [current_line.strip() for current_line in old_lines]
        starts = [
            index
            for index in range(len(lines) - len(wanted) + 1)
            if [current_line.strip() for current_line in lines[index:index + len(wanted)]] == wanted
        ]
        if len(starts) != 1:
            return None, len(starts)

        start = starts[0]
        new_lines = new_text.strip("\n").split("\n") if new_text.strip("\n") else []
        replacement = self._reindent(new_lines, self._indentation(old_lines[0]), self._indentation(lines[start]))
        return "\n".join(lines[:start] + replacement + lines[start + len(wanted):]), 1

    def _apply(self, content: str, input: ToolEditFileInput) -> tuple[Optional[str], str]:
        count = content.count(input.old_text)
        if input.replace_all:
            if count == 0:
                return None, f"old_text was not found in {input.path}, so nothing was replaced."
            return content.replace(input.old_text, input.new_text), ""

        replaced, line_matches = self._replace_lines(content, input.old_text, input.new_text)
        if replaced is not None:
            return replaced, ""
        if count == 1:
            return content.replace(input.old_text, input.new_text), ""
        if count > 1:
            return None, (
                f"old_text appears {count} times in {input.path}. Include more of the "
                f"surrounding lines so it matches exactly once, or set replace_all to true "
                f"to change every occurrence."
            )
        if line_matches > 1:
            return None, (
                f"old_text matches {line_matches} places in {input.path} once indentation is "
                f"ignored. Include more of the surrounding lines so it matches only one."
            )
        return None, (
            f"old_text was not found in {input.path}. Read the file again and copy the "
            f"lines you want to change exactly as they appear."
        )

    def execute(self, input: ToolEditFileInput) -> str:
        try:
            content = self._sandbox_env.read_file(input.path)
        except FileNotFoundError:
            return (
                f"'{input.path}' does not exist, so there is nothing to edit. Create it as "
                f"a whole file instead."
            )

        if input.old_text == input.new_text:
            return "old_text and new_text are identical, so nothing would change."

        updated, refusal = self._apply(content, input)
        if updated is None:
            return refusal

        written = self._sandbox_env.write_file(input.path, updated)
        diff = unified_diff(written, content, updated)
        return f"Edited {written}:\n{diff}" + python_syntax_warning(written, updated)
