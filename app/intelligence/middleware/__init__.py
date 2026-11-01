# Cross-cutting concerns applied to a component before it is used.

from app.intelligence.middleware.middleware_base import MiddlewareBase
from app.intelligence.middleware.context_window_middleware.middleware_summarization import MiddlewareSummarization
from app.intelligence.middleware.context_window_middleware.middleware_sliding_window import MiddlewareSlidingWindow

__all__ = [
    "MiddlewareBase",
    "MiddlewareSlidingWindow",
    "MiddlewareSummarization"
]
