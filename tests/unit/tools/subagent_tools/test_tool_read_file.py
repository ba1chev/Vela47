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
