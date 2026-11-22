import asyncio
from starlette.datastructures import State

from db import DatabaseSqlite
from app.server.routes import stream_chat
from app.server.routes import KEEPALIVE_FRAME
from app.intelligence.model import ModelConfig
from app.server.chat_sessions import ChatSession
from app.intelligence.agents import PromptManager
from app.intelligence.model import ModelFoundation
from app.server.chat_sessions import ChatSessionStoreSql
from tests.fixtures.agents.slow_echo_agent import SlowEchoAgent
from tests.fixtures.agents.tracing_echo_agent import TracingEchoAgent


def make_state():
    database = DatabaseSqlite()
    database.start()
    state = State()
    state.chat_session_store = ChatSessionStoreSql(database)
    return state


def make_agent(delay_seconds):
    return SlowEchoAgent(
        delay_seconds,
        model = ModelFoundation(ModelConfig(model_name = "qwen3:1.7b")),
        prompt_manager = PromptManager(),
        max_context_window_size = 10
    )


def stream(delay_seconds, keepalive_seconds):
    async def collect():
        frames = stream_chat(
            make_state(), "hi", ChatSession(owner_id = "a" * 32, title = "hi"), True,
            lambda tracing_service: make_agent(delay_seconds), "deep", keepalive_seconds = keepalive_seconds
        )
        return [current_frame async for current_frame in frames]
    return asyncio.run(collect())


def stored_trace(tool_result):
    state = make_state()
    chat_session = ChatSession(owner_id = "a" * 32, title = "hi")

    async def collect():
        frames = stream_chat(
            state, "hi", chat_session, True,
            lambda tracing_service: TracingEchoAgent(
                tracing_service,
                tool_result,
                model = ModelFoundation(ModelConfig(model_name = "qwen3:1.7b")),
                prompt_manager = PromptManager(),
                max_context_window_size = 10
            ),
            "deep"
        )
        return [current_frame async for current_frame in frames]

    asyncio.run(collect())
    return state.chat_session_store.get_session(chat_session.id).messages[-1].response_metadata["trace"]


class TestChatStream:
    def test_a_silent_agent_keeps_the_stream_alive_with_comments(self):
        frames = stream(delay_seconds = 0.4, keepalive_seconds = 0.1)
        assert frames.count(KEEPALIVE_FRAME) >= 2
        assert frames[0].startswith("event: session") and frames[-1].startswith("event: answer")

    def test_a_keep_alive_is_a_comment_the_browser_ignores(self):
        assert KEEPALIVE_FRAME.startswith(":") and KEEPALIVE_FRAME.endswith("\n\n")

    def test_an_agent_that_answers_quickly_gets_no_keep_alive(self):
        frames = stream(delay_seconds = 0, keepalive_seconds = 10)
        assert KEEPALIVE_FRAME not in frames
        assert frames[-1].startswith("event: answer")

    def test_the_stored_answer_keeps_the_steps_the_trace_panel_draws(self):
        trace = stored_trace("short")
        assert [current["type"] for current in trace] == [
            "pipeline_started", "model_invoked", "tool_executed", "pipeline_finished"
        ]
        assert trace[1]["payload"] == {"total_tokens": 42} and trace[-1]["duration_ms"] == 12.5

    def test_a_long_text_in_the_stored_trace_is_cut_short(self):
        result = stored_trace("x" * 5000)[2]["payload"]["result"]
        assert len(result) == 300 and result.endswith("…")
