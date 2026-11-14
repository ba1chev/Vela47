class FakeClock:
    """A clock that only moves when something sleeps on it, so pacing can be tested
    without waiting: every sleep is recorded and advances the time by its length."""

    def __init__(self, now = 1000.0) -> None:
        self.now = now
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds
