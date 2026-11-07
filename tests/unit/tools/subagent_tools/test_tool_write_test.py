import pathlib
import tempfile

from app.intelligence.tools import ToolWriteTest
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.tools import ToolWriteTestInput


def make_tool():
    return ToolWriteTest(SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run"))


class TestToolWriteTest:
    def test_name_is_stable(self):
        assert make_tool().name == "write_test"

    def test_an_already_correct_path_is_left_alone(self):
        result = make_tool().execute(
            ToolWriteTestInput(path = "tests/test_sort.py", content = "def test_x(): pass\n"))
        assert result == "Wrote tests/test_sort.py (1 lines)."

    def test_a_bare_name_is_given_the_convention(self):
        tool = make_tool()
        tool.execute(ToolWriteTestInput(path = "sort", content = "def test_x(): pass\n"))
        assert tool._sandbox_env.list_files() == ["tests/test_sort.py"]

    def test_a_rename_is_reported_back(self):
        result = make_tool().execute(
            ToolWriteTestInput(path = "sort", content = "def test_x(): pass\n"))
        assert "renamed from 'sort'" in result

    def test_a_missing_extension_is_added(self):
        tool = make_tool()
        tool.execute(ToolWriteTestInput(path = "test_sort", content = "x"))
        assert tool._sandbox_env.list_files() == ["tests/test_sort.py"]

    def test_an_absolute_path_cannot_escape(self):
        tool = make_tool()
        tool.execute(ToolWriteTestInput(path = "/etc/evil", content = "x"))
        assert tool._sandbox_env.list_files() == ["tests/test_evil.py"]

    def test_content_is_written_verbatim(self):
        tool = make_tool()
        tool.execute(ToolWriteTestInput(path = "test_a.py", content = "assert True\n"))
        assert tool._sandbox_env.read_file("tests/test_a.py") == "assert True\n"

    def test_a_test_that_does_not_parse_is_flagged(self):
        result = make_tool().execute(ToolWriteTestInput(path = "test_a.py", content = "def test_x(:\n"))
        assert "tests/test_a.py is not valid Python" in result
