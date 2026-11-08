import re

from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageBase
from app.intelligence.agents import OperationSubagentProbeBase


class OperationSubagentProbeSources(OperationSubagentProbeBase):
    """Reports which sources a research step really read, from the tool calls it made
    rather than the citations it wrote: the pages fetch_url returned and the documents
    search_documents found.

    A small model cites a URL it only saw in a search snippet as readily as one it read,
    so a step that searched the web but opened nothing is reported as having seen only
    snippets. Every call is matched to its result by id, and only successful results
    count — a page that failed to load was not read."""

    MAX_LISTED = 8
    DOCUMENT_TITLE = re.compile(r"^\[\d+\] (.+?)(?:, part \d+)?$", re.MULTILINE)

    def after(self, messages: list[MessageBase]) -> list[str]:
        calls = {
            current_call.id: current_call
            for current_message in messages if isinstance(current_message, MessageAI)
            for current_call in current_message.tool_calls
        }
        pages: list[str] = []
        documents: list[str] = []
        searched_web = False

        for current_message in messages:
            if not isinstance(current_message, MessageTool) or current_message.status != "success":
                continue
            call = calls.get(current_message.tool_call_id)
            content = current_message.content if isinstance(current_message.content, str) else str(current_message.content)
            if current_message.name == "fetch_url" and call is not None and call.args.get("url"):
                pages.append(str(call.args["url"]).strip())
            elif current_message.name == "search_documents":
                documents.extend(self.DOCUMENT_TITLE.findall(content))
            elif current_message.name == "web_search":
                searched_web = True

        pages, documents = list(dict.fromkeys(pages)), list(dict.fromkeys(documents))
        facts = []
        if pages:
            facts.append(f"Pages read: {', '.join(pages[:self.MAX_LISTED])}.")
        elif searched_web:
            facts.append("No page was read — only web search results and their snippets were seen.")
        if documents:
            facts.append(f"Documents found: {', '.join(documents[:self.MAX_LISTED])}.")
        return facts or ["No source was searched or read in this step."]
