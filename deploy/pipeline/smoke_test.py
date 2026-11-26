import json
import time
import urllib.error
import urllib.request
from typing import Callable, Optional

SESSION_COOKIE = "vela47_session"

Fetch = Callable[[str, str, dict[str, str]], tuple[int, dict[str, str], bytes]]


def fetch_over_http(method: str, url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, method = method, headers = headers, data = b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(request, timeout = 15) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


class SmokeTest:
    """Checks that a freshly deployed environment answers like the release it was given:
    the health endpoint reports that release's version, a guest can sign in, and the
    guest's conversations can be listed, which reads the database. It runs while the old
    tasks are still kept for a rollback, so a failure here undoes the deployment.

    The health check is retried for a while, since the load balancer may still be moving
    the last connections; the other checks are not."""

    def __init__(self, base_url: str, expected_version: str, fetch: Fetch = fetch_over_http,
        attempts: int = 10, wait_seconds: float = 6.0) -> None:
        self._base_url: str = base_url.rstrip("/")
        self._expected_version: str = expected_version
        self._fetch: Fetch = fetch
        self._attempts: int = attempts
        self._wait_seconds: float = wait_seconds

    def _health(self) -> Optional[str]:
        problem = "the health endpoint never answered"
        for current_attempt in range(self._attempts):
            if current_attempt:
                time.sleep(self._wait_seconds)
            try:
                status, _, body = self._fetch("GET", f"{self._base_url}/api/health", {})
            except OSError as error:
                problem = f"the health endpoint is unreachable: {error}"
                continue
            if status != 200:
                problem = f"the health endpoint answered {status}"
                continue
            version = json.loads(body).get("version")
            if version == self._expected_version:
                return None
            problem = f"the health endpoint reports version {version}, not {self._expected_version}"
        return problem

    def run(self) -> list[str]:
        problem = self._health()
        if problem is not None:
            return [problem]

        status, headers, _ = self._fetch("POST", f"{self._base_url}/api/auth/guest", {})
        cookie = next(
            (current_value for current_name, current_value in headers.items()
             if current_name.lower() == "set-cookie" and current_value.startswith(f"{SESSION_COOKIE}=")),
            None
        )
        if status != 200 or cookie is None:
            return [f"signing in as a guest answered {status}{'' if cookie else ' without a session cookie'}"]

        status, _, body = self._fetch("GET", f"{self._base_url}/api/sessions", {"Cookie": cookie.split(";")[0]})
        if status != 200 or not isinstance(json.loads(body), list):
            return [f"listing the guest's conversations answered {status}"]
        return []
