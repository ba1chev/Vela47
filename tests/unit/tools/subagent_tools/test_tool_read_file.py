import pathlib
import tempfile

from app.intelligence.tools import ToolReadFile
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.tools import ToolReadFileInput


def make_tool():
    return ToolReadFile(SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run"))


class TestToolReadFile:
    def test_name_is_stable(self):
        assert make_tool().name == "read_file"

    def test_numbers_the_lines(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "first\nsecond\n")
        output = tool.execute(ToolReadFileInput(path = "a.py"))
        assert "1  first" in output and "2  second" in output

    def test_reports_the_line_count(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "x\ny\n")
        assert "a.py (2 lines)" in tool.execute(ToolReadFileInput(path = "a.py"))

    def test_empty_file_is_reported_as_empty(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "")
        assert "empty" in tool.execute(ToolReadFileInput(path = "a.py"))

    def test_a_miss_lists_what_does_exist(self):
        tool = make_tool()
        tool._sandbox_env.write_file("real.py", "x")
        output = tool.execute(ToolReadFileInput(path = "wrong.py"))
        assert "does not exist" in output and "real.py" in output

    def test_a_miss_in_an_empty_workspace_says_so(self):
        assert "empty" in make_tool().execute(ToolReadFileInput(path = "wrong.py"))

    def test_a_long_file_comes_back_in_parts_with_where_to_continue(self):
        tool = make_tool()
        tool._sandbox_env.write_file("long.py", "\n".join(f"line {index}" for index in range(1, 301)))
        output = tool.execute(ToolReadFileInput(path = "long.py"))
        assert output.startswith("long.py (lines 1-250 of 300):")
        assert "line 250" in output and "line 251" not in output
        assert "Call read_file with start_line=251 to continue." in output

    def test_start_line_continues_a_long_file(self):
        tool = make_tool()
        tool._sandbox_env.write_file("long.py", "\n".join(f"line {index}" for index in range(1, 301)))
        output = tool.execute(ToolReadFileInput(path = "long.py", start_line = 251))
        assert output.startswith("long.py (lines 251-300 of 300):") and "251  line 251" in output
        assert "continue" not in output

    def test_end_line_reads_only_the_range_asked_for(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "a\nb\nc\nd\n")
        output = tool.execute(ToolReadFileInput(path = "a.py", start_line = 2, end_line = 3))
        assert output == "a.py (lines 2-3 of 4):\n2  b\n3  c"

    def test_a_start_past_the_end_is_explained(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "a\n")
        assert "has 1 lines" in tool.execute(ToolReadFileInput(path = "a.py", start_line = 5))

    def test_an_end_before_the_start_is_explained(self):
        tool = make_tool()
        tool._sandbox_env.write_file("a.py", "a\nb\nc\n")
        assert "comes before" in tool.execute(ToolReadFileInput(path = "a.py", start_line = 3, end_line = 1))
