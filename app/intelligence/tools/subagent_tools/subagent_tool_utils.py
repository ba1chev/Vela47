import ast
import difflib


def python_syntax_warning(path: str, content: str) -> str:
    """A sentence to append to a write's result when a Python file does not parse, empty
    otherwise. The file is written either way — refusing would lose the work — but the
    agent learns about the mistake on this turn, while it still remembers what it meant,
    rather than from a failing test or a reviewer much later."""
    if not path.endswith(".py"):
        return ""
    try:
        ast.parse(content, filename = path)
    except SyntaxError as error:
        return (
            f"\nWarning: {path} is not valid Python — line {error.lineno}: {error.msg}. "
            f"Fix it before relying on the file."
        )
    return ""


def unified_diff(path: str, before: str, after: str, max_lines: int = 60) -> str:
    """The change between two versions of a file as a unified diff, capped so an edit that
    touches a whole file cannot flood the context window it is reported into."""
    lines = list(difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        fromfile = f"a/{path}", tofile = f"b/{path}", lineterm = "", n = 2
    ))
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"… {len(lines) - max_lines} more diff lines."]
    return "\n".join(lines)
