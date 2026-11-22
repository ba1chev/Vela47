from typing import Any
from starlette.responses import Response
from fastapi.staticfiles import StaticFiles


class StaticFilesRevalidated(StaticFiles):
    """Serves the frontend's files with Cache-Control: no-cache. Without it a browser
    guesses how long a file stays fresh from its Last-Modified date and keeps using an
    old stylesheet or script after a deploy. With it every load asks again, and an
    unchanged file costs a 304 against its ETag, not a download."""

    def file_response(self, *args: Any, **kwargs: Any) -> Response:
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response
