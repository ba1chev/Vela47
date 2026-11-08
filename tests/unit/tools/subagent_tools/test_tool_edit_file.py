import pytest
import pathlib
import tempfile

from app.intelligence.tools import ToolEditFile
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.tools import ToolEditFileInput

SOURCE = "def area(width, height):\n    return width * height\n\n\ndef perimeter(width, height):\n    return 2 * (width + height)\n"
CLASS_SOURCE = "class Shape:\n    def area(self):\n        return self.width * self.height\n\n    def perimeter(self):\n        return 2 * (self.width + self.height)\n"


def make_tool(content = SOURCE):
    env = SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run")
    env.write_file("shapes.py", content)
    return ToolEditFile(env)


def edit(tool, old_text, new_text, path = "shapes.py", replace_all = False):
    return tool.execute(ToolEditFileInput(path = path, old_text = old_text, new_text = new_text, replace_all = replace_all))


class TestToolEditFile:
    def test_name_is_stable(self):
        assert make_tool().name == "edit_file"

    def test_a_unique_match_is_replaced_and_the_diff_returned(self):
        tool = make_tool()
        output = edit(tool, "return width * height", "return round(width * height, 2)")
        assert tool._sandbox_env.read_file("shapes.py").splitlines()[1] == "    return round(width * height, 2)"
        assert output.startswith("Edited shapes.py:") and "-    return width * height" in output
        assert "+    return round(width * height, 2)" in output

    def test_an_ambiguous_match_is_refused_with_the_count(self):
        tool = make_tool()
        output = edit(tool, "width, height", "w, h")
        assert "appears 2 times" in output and tool._sandbox_env.read_file("shapes.py") == SOURCE

    def test_replace_all_changes_every_occurrence(self):
        tool = make_tool()
        edit(tool, "width", "w", replace_all = True)
        assert "width" not in tool._sandbox_env.read_file("shapes.py")

    def test_text_that_is_not_there_is_refused_and_nothing_written(self):
        tool = make_tool()
        assert "was not found" in edit(tool, "return width / height", "x")
        assert tool._sandbox_env.read_file("shapes.py") == SOURCE

    def test_a_match_with_the_wrong_indentation_still_applies_with_the_files_indentation(self):
        tool = make_tool()
        edit(tool, "return 2 * (width + height)", "if width < 0:\n    raise ValueError(width)\nreturn 2 * (width + height)")
        lines = tool._sandbox_env.read_file("shapes.py").splitlines()
        assert lines[5:8] == ["    if width < 0:", "        raise ValueError(width)", "    return 2 * (width + height)"]

    def test_a_replacement_already_at_the_files_indentation_is_left_as_written(self):
        tool = make_tool()
        edit(tool, "return width * height", "    product = width * height\n    return product")
        assert tool._sandbox_env.read_file("shapes.py").splitlines()[1:3] == ["    product = width * height", "    return product"]

    def test_a_first_line_copied_without_its_indentation_leaves_the_rest_at_their_depth(self):
        tool = make_tool(CLASS_SOURCE)
        edit(tool, "def area(self):\n        return self.width * self.height", "def area(self):\n        return round(self.width * self.height, 2)")
        lines = tool._sandbox_env.read_file("shapes.py").splitlines()
        assert lines[1:3] == ["    def area(self):", "        return round(self.width * self.height, 2)"]

    def test_a_method_added_after_a_first_line_without_indentation_stays_a_sibling(self):
        tool = make_tool(CLASS_SOURCE)
        edit(
            tool,
            "def area(self):\n        return self.width * self.height",
            "def area(self):\n        return self.width * self.height\n\n    def is_square(self):\n        return self.width == self.height"
        )
        lines = tool._sandbox_env.read_file("shapes.py").splitlines()
        assert lines[1:6] == [
            "    def area(self):", "        return self.width * self.height", "",
            "    def is_square(self):", "        return self.width == self.height"
        ]

    def test_a_block_copied_without_any_indentation_is_shifted_as_a_whole(self):
        tool = make_tool(CLASS_SOURCE)
        edit(tool, "def area(self):\nreturn self.width * self.height", "def area(self):\n    return abs(self.width * self.height)")
        lines = tool._sandbox_env.read_file("shapes.py").splitlines()
        assert lines[1:3] == ["    def area(self):", "        return abs(self.width * self.height)"]

    def test_part_of_a_line_is_matched_exactly(self):
        tool = make_tool()
        edit(tool, "2 * (width + height)", "(width + height) * 2")
        assert "    return (width + height) * 2" in tool._sandbox_env.read_file("shapes.py").splitlines()

    def test_an_indentation_free_match_must_also_be_unique(self):
        tool = make_tool("if a:\n    x = 1\nif b:\n        x = 1\n")
        assert "matches 2 places" in edit(tool, "\tx = 1", "x = 2")

    def test_new_text_may_be_empty_to_delete(self):
        tool = make_tool()
        edit(tool, "def perimeter(width, height):\n    return 2 * (width + height)", "")
        content = tool._sandbox_env.read_file("shapes.py")
        assert "perimeter" not in content and content.startswith("def area(width, height):")

    def test_replace_all_of_absent_text_is_refused(self):
        assert "was not found" in edit(make_tool(), "depth", "d", replace_all = True)

    def test_a_missing_file_cannot_be_edited(self):
        assert "does not exist" in edit(make_tool(), "x", "y", path = "nope.py")

    def test_identical_texts_change_nothing(self):
        assert "identical" in edit(make_tool(), "area", "area")

    def test_an_edit_that_breaks_python_is_flagged(self):
        output = edit(make_tool(), "def area(width, height):", "def area(width, height:")
        assert "not valid Python" in output

    def test_escaping_the_sandbox_is_refused(self):
        with pytest.raises(ValueError):
            edit(make_tool(), "x", "y", path = "../outside.py")
