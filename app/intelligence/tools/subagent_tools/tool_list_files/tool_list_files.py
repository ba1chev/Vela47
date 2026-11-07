import posixpath

from app.intelligence.tools import ToolBase
from app.intelligence.sandbox import SandboxEnv
from app.intelligence.tools import ToolListFilesInput


class ToolListFiles(ToolBase[ToolListFilesInput, str]):
    """Shows the workspace as an indented tree with each file's line count — the
    directory_tree of MCP's filesystem server, cut down to what an agent needs.

    It is the first thing an agent should call in a workspace another subagent wrote
    into: the files a CODE step left behind are what a TEST step has to import, and
    guessing their names wastes a turn on every wrong guess. Line counts tell it which
    files are worth reading whole and which need paging.

    The tree is built from list_files(), so it shows exactly what the other tools can
    reach — caches and oversized files the sandbox skips are skipped here too. Depth and
    entry count are capped, and directories past the depth are folded into a count, so
    a large workspace still fits in a context window."""

    MAX_ENTRIES = 200

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__()
        self._sandbox_env: SandboxEnv = sandbox_env

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return (
            "List the files in your workspace as a tree, with how many lines each has. "
            "Call it first to see what exists — including what earlier steps wrote — "
            "before you read, write or test anything."
        )

    @property
    def input_schema(self) -> type[ToolListFilesInput]:
        return ToolListFilesInput

    def _line_count(self, path: str) -> str:
        try:
            return f"{len(self._sandbox_env.read_file(path).splitlines())} lines"
        except (OSError, ValueError):
            return "unreadable"

    def _tree(self, paths: dict[str, str]) -> dict:
        tree: dict = {}
        for current_relative, current_full in paths.items():
            node = tree
            parts = current_relative.split("/")
            for current_part in parts[:-1]:
                node = node.setdefault(current_part + "/", {})
            node[parts[-1]] = current_full
        return tree

    def _count(self, node: dict) -> int:
        return sum(
            self._count(current_child) if isinstance(current_child, dict) else 1
            for current_child in node.values()
        )

    def _render(self, node: dict, level: int, depth: int, lines: list[str]) -> None:
        names = sorted(node, key = lambda name: (not isinstance(node[name], dict), name))
        for current_name in names:
            if len(lines) >= self.MAX_ENTRIES:
                return
            child = node[current_name]
            indent = "  " * level
            if not isinstance(child, dict):
                lines.append(f"{indent}{current_name} ({self._line_count(child)})")
            elif level + 1 >= depth:
                lines.append(f"{indent}{current_name} ({self._count(child)} files)")
            else:
                lines.append(f"{indent}{current_name}")
                self._render(child, level + 1, depth, lines)

    def execute(self, input: ToolListFilesInput) -> str:
        root = posixpath.normpath(input.path.strip() or ".")
        if root.startswith("..") or posixpath.isabs(root):
            raise ValueError(f"Path '{input.path}' points outside the workspace and was refused.")
        prefix = "" if root == "." else root + "/"

        files = self._sandbox_env.list_files()
        if not files:
            return "The workspace is empty — nothing has been written yet."

        selected = {
            current_file[len(prefix):]: current_file
            for current_file in files
            if current_file.startswith(prefix)
        }
        if not selected:
            return f"'{input.path}' is not a directory in the workspace."

        lines: list[str] = []
        self._render(self._tree(selected), 0, input.depth, lines)

        header = f"{len(selected)} file(s) under {root + '/' if prefix else 'the workspace'}:"
        footer = (
            f"\n… the listing stops at {self.MAX_ENTRIES} entries; list a subdirectory to see the rest."
            if len(lines) >= self.MAX_ENTRIES
            else ""
        )
        return header + "\n" + "\n".join(lines) + footer
