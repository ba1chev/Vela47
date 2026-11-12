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
