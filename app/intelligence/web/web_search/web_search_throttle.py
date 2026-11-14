import time
import threading
from typing import Callable


class WebSearchThrottle:
    """Paces the searches one process sends to a search engine. Every search leaves from
    the same address, so a model that asks for three at once must not send them at
    once: wait_turn() spaces requests min_interval_seconds apart, and back_off() pushes
    the next one further out after the engine refused one.

    cool_down() pauses searching altogether; until it ends, blocked_for() says how long
    is left and the search answers at once instead of asking the engine again, so a run
    spends no turns on requests that would only be refused."""

    def __init__(self, min_interval_seconds: float = 2.0, cool_down_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep) -> None:
        self._min_interval_seconds: float = min_interval_seconds
        self._cool_down_seconds: float = cool_down_seconds
        self._clock: Callable[[], float] = clock
        self._sleep: Callable[[float], None] = sleep
        self._lock: threading.Lock = threading.Lock()
        self._next_at: float = 0.0
        self._blocked_until: float = 0.0

    def wait_turn(self) -> None:
        with self._lock:
            wait = self._next_at - self._clock()
            if wait > 0:
                self._sleep(wait)
            self._next_at = self._clock() + self._min_interval_seconds

    def back_off(self, seconds: float) -> None:
        with self._lock:
            self._next_at = max(self._next_at, self._clock() + seconds)

    def cool_down(self) -> None:
        with self._lock:
            self._blocked_until = self._clock() + self._cool_down_seconds

    def blocked_for(self) -> float:
        return max(0.0, self._blocked_until - self._clock())
