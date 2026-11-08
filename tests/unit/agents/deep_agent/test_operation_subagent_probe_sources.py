import pathlib
import tempfile

from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageTool
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.messages import MessageToolCall
from app.intelligence.agents import OperationSubagentProbeSources


def call(name, args, id):
    return MessageAI(content = "", tool_calls = [MessageToolCall(name = name, args = args, id = id)])


def result(name, id, content, status = "success"):
    return MessageTool(tool_call_id = id, name = name, content = content, status = status)


def check(messages):
    return OperationSubagentProbeSources(SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run")).after(messages)


class TestOperationSubagentProbeSources:
    def test_pages_read_are_listed_once_and_failed_ones_left_out(self):
        assert check([
            call("fetch_url", {"url": "https://a.org/x"}, "1"), result("fetch_url", "1", "A — https://a.org/x"),
            call("fetch_url", {"url": "https://a.org/x"}, "2"), result("fetch_url", "2", "A — https://a.org/x"),
            call("fetch_url", {"url": "https://b.org"}, "3"), result("fetch_url", "3", "refused", "error")
        ]) == ["Pages read: https://a.org/x."]

    def test_a_web_search_without_a_page_read_is_called_snippets_only(self):
        assert check([call("web_search", {"query": "x"}, "1"), result("web_search", "1", "3 result(s)")]) == [
            "No page was read — only web search results and their snippets were seen."
        ]

    def test_documents_found_are_listed_by_title(self):
        found = "2 passage(s) for 'leave':\n\n[1] Employee Handbook, part 2\n25 days.\n\n[2] Runbook\nBackups."
        assert check([call("search_documents", {"query": "leave"}, "1"), result("search_documents", "1", found)]) == [
            "Documents found: Employee Handbook, Runbook."
        ]

    def test_a_step_that_used_no_source_says_so(self):
        assert check([call("search_files", {"query": "x"}, "1"), result("search_files", "1", "No match")]) == [
            "No source was searched or read in this step."
        ]
