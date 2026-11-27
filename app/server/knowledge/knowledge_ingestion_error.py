class KnowledgeIngestionError(Exception):
    """Why a document could not be added, as the HTTP status that says so and a sentence
    a person can act on. KnowledgeIngestion raises it and knows nothing of HTTP; the
    route turns it into a response, or into the last frame of a streamed upload."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self._status_code: int = status_code
        self._detail: str = detail

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def detail(self) -> str:
        return self._detail
