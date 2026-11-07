import pathlib
import tempfile

from app.intelligence.tools import ToolWriteFile
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.tools import ToolWriteFileInput


def make_tool():
    return ToolWriteFile(SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run"))


class TestToolWriteFile:
    def test_name_is_stable(self):
        assert make_tool().name == "write_file"

    def test_reports_a_new_file_as_created(self):
        result = make_tool().execute(ToolWriteFileInput(path = "a.py", content = "x = 1\n"))
        assert result == "Created a.py (1 lines)."

    def test_reports_an_existing_file_as_replaced_with_its_old_length(self):
        tool = make_tool()
        tool.execute(ToolWriteFileInput(path = "a.txt", content = "a\nb\nc\n"))
        result = tool.execute(ToolWriteFileInput(path = "a.txt", content = "a\n"))
        assert result == "Replaced a.txt (1 lines, previously 3)."

    def test_python_that_does_not_parse_is_written_and_flagged(self):
        tool = make_tool()
        result = tool.execute(ToolWriteFileInput(path = "a.py", content = "def f(:\n    pass\n"))
        assert "not valid Python — line 1" in result and tool._sandbox_env.read_file("a.py").startswith("def f(")

    def test_files_that_are_not_python_are_not_checked(self):
        result = make_tool().execute(ToolWriteFileInput(path = "notes.md", content = "def f(:"))
        assert "Warning" not in result

    def test_counts_lines(self):
        tool = make_tool()
        result = tool.execute(ToolWriteFileInput(path = "a.py", content = "a\nb\nc\n"))
        assert "3 lines" in result

    def test_content_lands_in_the_sandbox(self):
        tool = make_tool()
        tool.execute(ToolWriteFileInput(path = "src/a.py", content = "hello"))
        assert tool._sandbox_env.read_file("src/a.py") == "hello"

    def test_writing_twice_replaces(self):
        tool = make_tool()
        tool.execute(ToolWriteFileInput(path = "a.py", content = "first"))
        tool.execute(ToolWriteFileInput(path = "a.py", content = "second"))
        assert tool._sandbox_env.read_file("a.py") == "second"

    def test_escaping_the_sandbox_is_refused(self):
        import pytest
        with pytest.raises(ValueError):
            make_tool().execute(ToolWriteFileInput(path = "../out.py", content = "owned"))
