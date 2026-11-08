import pytest
import pathlib
import tempfile

from app.intelligence.tools import ToolListFiles
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.tools import ToolListFilesInput


def make_tool(files = None):
    env = SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run")
    for current_path, current_content in (files or {}).items():
        env.write_file(current_path, current_content)
    return ToolListFiles(env)


class TestToolListFiles:
    def test_name_is_stable(self):
        assert make_tool().name == "list_files"

    def test_an_empty_workspace_says_so(self):
        assert "empty" in make_tool().execute(ToolListFilesInput())

    def test_the_tree_lists_directories_first_with_line_counts(self):
        tool = make_tool({"main.py": "a\nb\n", "src/sort.py": "x\n", "tests/test_sort.py": "t\nt\nt\n"})
        assert tool.execute(ToolListFilesInput()) == (
            "3 file(s) under the workspace:\n"
            "src/\n"
            "  sort.py (1 lines)\n"
            "tests/\n"
            "  test_sort.py (3 lines)\n"
            "main.py (2 lines)"
        )

    def test_directories_past_the_depth_are_folded_into_a_count(self):
        tool = make_tool({"a/b/c/d.py": "x", "a/b/c/e.py": "x", "a/f.py": "x"})
        assert tool.execute(ToolListFilesInput(depth = 2)) == (
            "3 file(s) under the workspace:\n"
            "a/\n"
            "  b/ (2 files)\n"
            "  f.py (1 lines)"
        )

    def test_a_subdirectory_can_be_listed_on_its_own(self):
        tool = make_tool({"src/sort.py": "x", "main.py": "y"})
        assert tool.execute(ToolListFilesInput(path = "src")) == "1 file(s) under src/:\nsort.py (1 lines)"

    def test_an_unknown_directory_is_reported(self):
        tool = make_tool({"a.py": "x"})
        assert "is not a directory" in tool.execute(ToolListFilesInput(path = "nope"))

    def test_a_path_outside_the_workspace_is_refused(self):
        with pytest.raises(ValueError):
            make_tool({"a.py": "x"}).execute(ToolListFilesInput(path = "../.."))

    def test_the_listing_is_capped(self):
        tool = make_tool({f"f{index:03d}.txt": "x" for index in range(ToolListFiles.MAX_ENTRIES + 5)})
        assert "stops at 200 entries" in tool.execute(ToolListFilesInput())
