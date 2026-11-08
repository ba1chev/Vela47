import pathlib
import tempfile

from app.intelligence.messages import MessageAI
from app.intelligence.tools import ToolReadFile
from app.intelligence.tools import ToolWriteFile
from app.intelligence.messages import MessageTool
from app.intelligence.agents import PromptManager
from app.intelligence.messages import MessageHuman
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.messages import MessageToolCall
from app.intelligence.agents import OperationSubagent
from app.intelligence.agents import SUBAGENT_ACT_PROMPT
from app.intelligence.agents import SUBAGENT_REPORT_PROMPT
from app.intelligence.middleware import MiddlewareSlidingWindow
from tests.fixtures.model.scripted_tool_model import ScriptedToolModel


def call(name, args, id):
    return MessageAI(content = "", tool_calls = [MessageToolCall(name = name, args = args, id = id)])


def make_subagent(replies, max_iterations = 6):
    env = SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run")
    model = ScriptedToolModel(replies)
    subagent = OperationSubagent(
        model = model,
        prompt_manager = PromptManager(),
        max_context_window_size = 24,
        tools = [ToolWriteFile(env), ToolReadFile(env)],
        context_window_middleware = MiddlewareSlidingWindow(step = 2),
        max_iterations = max_iterations
    )
    return subagent, model, env


class TestOperationSubagent:
    def test_every_tool_in_the_toolset_is_offered_to_the_model(self):
        subagent, model, _ = make_subagent([MessageAI(content = "nothing to do")])
        subagent.execute(MessageHuman(content = "task"))
        offered = [current["function"]["name"] for current in model.calls[0][1]]
        assert offered == ["write_file", "read_file"]

    def test_one_task_can_use_several_tools_in_turn(self):
        subagent, model, env = make_subagent([
            call("write_file", {"path": "a.py", "content": "x = 1\n"}, "c1"),
            call("read_file", {"path": "a.py"}, "c2"),
            MessageAI(content = "a.py holds x = 1.")
        ])
        response = subagent.execute(MessageHuman(content = "write and check a.py"))
        assert response.content == "a.py holds x = 1." and env.read_file("a.py") == "x = 1\n"
        assert len(model.calls) == 3

    def test_the_history_keeps_which_tool_was_called_and_which_answered(self):
        subagent, model, _ = make_subagent([
            call("write_file", {"path": "a.py", "content": "x = 1\n"}, "c1"),
            MessageAI(content = "done")
        ])
        subagent.execute(MessageHuman(content = "write a.py"))
        history = model.calls[1][0]
        assistant = [current for current in history if isinstance(current, MessageAI)][0]
        result = [current for current in history if isinstance(current, MessageTool)][0]
        assert assistant.tool_calls[0].name == "write_file" and assistant.tool_calls[0].args["path"] == "a.py"
        assert result.name == "write_file" and result.tool_call_id == "c1" and result.content.startswith("Created a.py")

    def test_reaching_the_cap_ends_with_a_turn_without_tools(self):
        subagent, model, _ = make_subagent(
            [call("read_file", {"path": "a.py"}, f"c{index}") for index in range(2)]
            + [MessageAI(content = "a.py does not exist yet.")],
            max_iterations = 2
        )
        response = subagent.execute(MessageHuman(content = "read a.py"))
        assert response.content == "a.py does not exist yet."
        assert len(model.calls) == 3 and model.calls[-1][1] is None

    def test_the_task_stays_in_view_for_the_whole_loop(self):
        subagent, model, _ = make_subagent(
            [call("read_file", {"path": "a.py"}, f"c{index}") for index in range(6)]
        )
        subagent.execute(MessageHuman(content = "the task"))
        assert all(
            any(isinstance(current, MessageHuman) and current.content == "the task" for current in current_call[0])
            for current_call in model.calls
        )

    def test_an_announcement_before_any_tool_is_sent_back_to_act(self):
        subagent, model, _ = make_subagent([
            MessageAI(content = "I will first read a.py."),
            call("read_file", {"path": "a.py"}, "c1"),
            MessageAI(content = "a.py does not exist yet.")
        ])
        response = subagent.execute(MessageHuman(content = "read a.py"))
        assert response.content == "a.py does not exist yet." and len(model.calls) == 3
        assert model.calls[1][0][-1].content == SUBAGENT_ACT_PROMPT

    def test_a_second_reply_without_a_tool_is_accepted(self):
        subagent, model, _ = make_subagent([MessageAI(content = "Nothing to do."), MessageAI(content = "There is nothing to do.")])
        assert subagent.execute(MessageHuman(content = "task")).content == "There is nothing to do."
        assert len(model.calls) == 2

    def test_a_reply_without_a_tool_after_using_one_is_the_answer(self):
        subagent, model, _ = make_subagent([call("read_file", {"path": "a.py"}, "c1"), MessageAI(content = "a.py is missing.")])
        assert subagent.execute(MessageHuman(content = "read a.py")).content == "a.py is missing."
        assert len(model.calls) == 2

    def test_the_last_turn_is_told_that_no_tools_are_left(self):
        subagent, model, _ = make_subagent([call("read_file", {"path": "a.py"}, "c1"), MessageAI(content = "a.py is missing.")], max_iterations = 1)
        subagent.execute(MessageHuman(content = "read a.py"))
        assert model.calls[-1][0][-1].content == SUBAGENT_REPORT_PROMPT and model.calls[-1][1] is None

    def test_a_tool_call_written_as_text_is_replaced_by_the_last_real_result(self):
        written = MessageAI(content = '<tool_call>\n{"name": "read_file", "arguments": {"path": "a.py"}}\n</tool_call>')
        subagent, _, _ = make_subagent([call("read_file", {"path": "a.py"}, "c1"), written], max_iterations = 1)
        report = subagent.execute(MessageHuman(content = "read a.py")).content
        assert report.startswith("This step ran out of turns") and "read_file" in report and "does not exist" in report
        assert "<tool_call>" not in report

    def test_text_around_a_tool_call_written_as_text_is_kept(self):
        written = MessageAI(content = 'a.py is missing.\n<tool_call>\n{"name": "read_file"}\n</tool_call>')
        subagent, _, _ = make_subagent([call("read_file", {"path": "a.py"}, "c1"), written])
        assert subagent.execute(MessageHuman(content = "read a.py")).content == "a.py is missing."
