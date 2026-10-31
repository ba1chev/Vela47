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

    def test_reports_what_it_wrote(self):
        result = make_tool().execute(ToolWriteFileInput(path = "a.py", content = "x = 1\n"))
        assert result == "Wrote a.py (1 lines)."

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
