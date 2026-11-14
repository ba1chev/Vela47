import pytest

from app.intelligence.tools import ToolMessageWorker
from app.intelligence.tools import ToolMessageWorkerInput


def make_tool(max_messages = 2, sent = None):
    sent = sent if sent is not None else []
    def send(message):
        sent.append(message)
        return f"fixed: {message}"
    return ToolMessageWorker(send, "CODE", max_messages), sent


class TestToolMessageWorker:
    def test_name_is_stable(self):
        assert make_tool()[0].name == "message_worker"

    def test_the_description_names_the_other_worker(self):
        assert "CODE worker" in make_tool()[0].description

    def test_the_message_is_sent_and_the_answer_returned(self):
        tool, sent = make_tool()
        output = tool.execute(ToolMessageWorkerInput(message = "to_fahrenheit(-40) returns 0"))
        assert sent == ["to_fahrenheit(-40) returns 0"]
        assert output.startswith("The CODE worker answered:\nfixed: to_fahrenheit(-40) returns 0")

    def test_the_answer_asks_for_the_fix_to_be_checked(self):
        output = make_tool()[0].execute(ToolMessageWorkerInput(message = "bug"))
        assert output.endswith("Check what it says it changed with your own tools before you rely on it.")

    def test_it_counts_what_it_delivered(self):
        tool, _ = make_tool()
        tool.execute(ToolMessageWorkerInput(message = "one"))
        tool.execute(ToolMessageWorkerInput(message = "two"))
        assert tool.delivered == 2

    def test_messages_over_the_cap_are_not_sent(self):
        tool, sent = make_tool(max_messages = 1)
        tool.execute(ToolMessageWorkerInput(message = "one"))
        output = tool.execute(ToolMessageWorkerInput(message = "two"))
        assert sent == ["one"] and tool.delivered == 1
        assert "the most one step may send" in output

    def test_a_failed_delivery_raises_and_is_not_counted(self):
        def send(message):
            raise RuntimeError("the network is gone")
        tool = ToolMessageWorker(send, "CODE")
        with pytest.raises(RuntimeError, match = "the network is gone"):
            tool.execute(ToolMessageWorkerInput(message = "bug"))
        assert tool.delivered == 0

    def test_an_empty_message_is_refused(self):
        with pytest.raises(ValueError):
            ToolMessageWorkerInput(message = "")
