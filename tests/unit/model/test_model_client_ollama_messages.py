from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageHuman
from app.intelligence.messages import MessageSystem
from app.intelligence.model import ModelClientOllama
from app.intelligence.messages import MessageToolCall


def format_messages(messages):
    return ModelClientOllama()._format_messages(messages)


class TestModelClientOllamaMessages:
    def test_plain_messages_carry_role_and_content_only(self):
        assert format_messages([MessageSystem(content = "rules"), MessageHuman(content = "hi")]) == [
            {"role": "system", "content": "rules"},
            {"role": "user", "content": "hi"}
        ]

    def test_an_assistant_turn_keeps_the_tool_calls_it_made(self):
        call = MessageToolCall(name = "read_file", args = {"path": "a.py"}, id = "c1")
        formatted = format_messages([MessageAI(content = "", tool_calls = [call])])[0]
        assert formatted == {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": "a.py"}}}]
        }

    def test_a_tool_result_names_the_tool_that_produced_it(self):
        formatted = format_messages([MessageTool(content = "1  x", tool_call_id = "c1", name = "read_file")])[0]
        assert formatted == {"role": "tool", "content": "1  x", "tool_name": "read_file"}

    def test_a_tool_result_without_a_name_is_sent_without_one(self):
        assert "tool_name" not in format_messages([MessageTool(content = "x", tool_call_id = "c1")])[0]
