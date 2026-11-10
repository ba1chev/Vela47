from typing import Optional

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import unified_diff
from app.intelligence.tools import ToolEditFileInput
from app.intelligence.tools import python_syntax_warning


class ToolEditFile(ToolBase[ToolEditFileInput, str]):
    """Changes part of an existing file by replacing exact text, as the edit tools of
    coding agents do, and answers with a unified diff. Text is matched by content, never
    by line number, and must occur exactly once unless replace_all is set, so an
    ambiguous edit is refused with the count.

    Whole lines are matched with their indentation ignored and the replacement is
    re-indented to where it lands, because small models reproduce code but not its
    whitespace. When only old_text's first line lost its indentation, only new_text's
    first line is moved; otherwise all of new_text is moved by the first line's error.
    Text that is only part of a line is matched exactly. Nothing is written unless the
    edit applies."""

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

    def _offset(self, written_line: str, file_line: str) -> int:
        return len(self._indentation(file_line)) - len(self._indentation(written_line))

    def _shift(self, line: str, offset: int, unit: str) -> str:
        if not line.strip() or offset == 0:
            return line
        if offset > 0:
            return unit * offset + line
        return line[min(-offset, len(self._indentation(line))):]

    def _reindent(self, new_lines: list[str], old_lines: list[str], matched_lines: list[str]) -> list[str]:
        pairs = [
            (current_old, current_matched)
            for current_old, current_matched in zip(old_lines, matched_lines)
            if current_old.strip()
        ]
        first = next((index for index, current_line in enumerate(new_lines) if current_line.strip()), None)
        if not pairs or first is None or self._indentation(new_lines[first]) == self._indentation(pairs[0][1]):
            return new_lines

        offset = self._offset(*pairs[0])
        only_first_was_off = len(pairs) > 1 and all(self._offset(*current_pair) == 0 for current_pair in pairs[1:])
        unit = "\t" if any(self._indentation(current_matched).startswith("\t") for _, current_matched in pairs) else " "
        return [
            self._shift(current_line, offset, unit)
            if index == first or not only_first_was_off
            else current_line
            for index, current_line in enumerate(new_lines)
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
        matched_lines = lines[start:start + len(wanted)]
        new_lines = new_text.strip("\n").split("\n") if new_text.strip("\n") else []
        replacement = self._reindent(new_lines, old_lines, matched_lines)
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
