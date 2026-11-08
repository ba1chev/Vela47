import pathlib
import tempfile

from app.intelligence.tools import ToolSearchFiles
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.tools import ToolSearchFilesInput


def make_tool():
    return ToolSearchFiles(SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run"))


class TestToolSearchFiles:
    def test_name_is_stable(self):
        assert make_tool().name == "search_files"

    def test_empty_workspace_says_so(self):
        assert "empty" in make_tool().execute(ToolSearchFilesInput(query = "anything"))

    def test_returns_the_matching_line_not_just_the_file(self):
        """A match that arrives readable saves the turn a read_file would cost."""
        tool = make_tool()
        tool._sandbox_env.write_file("sort.py", "def bubble(x):\n    return x\n")
        output = tool.execute(ToolSearchFilesInput(query = "bubble"))
        assert "sort.py:1:" in output and "def bubble(x):" in output

    def test_match_is_case_insensitive(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "BubbleSort\n")
        assert "1 match" in tool.execute(ToolSearchFilesInput(query = "bubblesort"))

    def test_no_match_is_reported_clearly(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "nothing here\n")
        assert "No match" in tool.execute(ToolSearchFilesInput(query = "absent"))

    def test_searches_every_file(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "needle\n")
        tool._sandbox_env.write_file("b/c.py", "needle\n")
        output = tool.execute(ToolSearchFilesInput(query = "needle"))
        assert "a.py" in output and "b/c.py" in output

    def test_results_are_capped(self):
        tool = make_tool()
        tool._sandbox_env.write_file("many.py", "hit\n" * (ToolSearchFiles.MAX_MATCHES + 20))
        output = tool.execute(ToolSearchFilesInput(query = "hit"))
        assert "output truncated" not in output
        assert "narrow the query" in output

    def test_a_glob_without_a_slash_matches_file_names(self):
        tool = make_tool()
        tool._sandbox_env.write_file("src/a.py", "needle\n")
        tool._sandbox_env.write_file("notes.md", "needle\n")
        output = tool.execute(ToolSearchFilesInput(query = "needle", path_glob = "*.py"))
        assert "src/a.py" in output and "notes.md" not in output

    def test_a_glob_with_a_slash_matches_paths(self):
        tool = make_tool()
        tool._sandbox_env.write_file("tests/test_a.py", "needle\n")
        tool._sandbox_env.write_file("src/a.py", "needle\n")
        output = tool.execute(ToolSearchFilesInput(query = "needle", path_glob = "tests/*"))
        assert "tests/test_a.py" in output and "src/a.py" not in output

    def test_a_glob_matching_nothing_says_so(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "x\n")
        assert "No workspace file matches '*.rs'" in tool.execute(ToolSearchFilesInput(query = "x", path_glob = "*.rs"))

    def test_a_regular_expression_can_be_searched(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "def quick_sort():\ndef merge_sort():\ndef helper():\n")
        output = tool.execute(ToolSearchFilesInput(query = "def (quick|merge)_sort", is_regex = True))
        assert "2 match(es)" in output and "helper" not in output

    def test_an_invalid_regular_expression_is_explained(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "x\n")
        assert "not a valid regular expression" in tool.execute(ToolSearchFilesInput(query = "(", is_regex = True))
