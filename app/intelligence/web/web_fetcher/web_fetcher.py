import time
import httpx
from typing import Optional

from app.intelligence.web import WebPage
from app.intelligence.web import WebAccessError
from app.intelligence.web import WebAddressGuard


class WebFetcher:
    """Fetches one URL for an agent or an upload, and nothing it was not allowed to.

    Every hop goes through the WebAddressGuard, redirects included: they are followed by
    hand rather than by the HTTP client, because a public page that redirects to
    http://169.254.169.254/ is the oldest way around a check made only on the first URL.
    Each request is sent to the address the guard approved, with the original name in
    the Host header and as the TLS server name, so certificates are still verified
    against the name while the connection cannot be rebound to a different address.
    Proxy settings from the environment are ignored for the same reason.

    The response is read as a stream and cut at max_bytes, and the whole fetch has a
    deadline as well as per-read timeouts — a server trickling one byte a second would
    otherwise pass every read timeout and hold a subagent forever. Decompression happens
    before the cut, so a compressed response cannot expand past the limit either.

    Any failure leaves as WebAccessError with a sentence a model can act on. The
    transport is injectable, which is how tests answer requests without a network."""

    USER_AGENT = "Mozilla/5.0 (compatible; Vela47/1.0; +research agent)"
    REDIRECT_STATUSES = {301, 302, 303, 307, 308}

    def __init__(self, address_guard: Optional[WebAddressGuard] = None,
        transport: Optional[httpx.BaseTransport] = None, max_bytes: int = 3 * 1024 * 1024,
        timeout_seconds: float = 10.0, deadline_seconds: float = 30.0,
        max_redirects: int = 5) -> None:
        self._address_guard: WebAddressGuard = (
            address_guard if address_guard is not None else WebAddressGuard()
        )
        self._transport: Optional[httpx.BaseTransport] = transport
        self._max_bytes: int = max_bytes
        self._timeout_seconds: float = timeout_seconds
        self._deadline_seconds: float = deadline_seconds
        self._max_redirects: int = max_redirects

    def _parse(self, url: str) -> httpx.URL:
        try:
            parsed = httpx.URL(url.strip())
        except (httpx.InvalidURL, TypeError) as error:
            raise WebAccessError(f"'{url}' is not a valid URL: {error}") from None
        if not parsed.scheme:
            raise WebAccessError(f"'{url}' is not a full URL — it needs to start with https://.")
        return parsed

    def _send(self, client: httpx.Client, method: str, url: httpx.URL,
        form: Optional[dict[str, str]]) -> httpx.Response:
        address = self._address_guard.check(url)
        extensions = {"sni_hostname": url.raw_host.decode("ascii")} if url.scheme == "https" else {}
        request = client.build_request(
            method,
            url.copy_with(host = address),
            headers = {
                "Host": url.netloc.decode("ascii"),
                "User-Agent": self.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/pdf,text/plain;q=0.9,*/*;q=0.5"
            },
            data = form,
            extensions = extensions
        )
        return client.send(request, stream = True)

    def _read(self, response: httpx.Response, limit: int, deadline: float) -> tuple[bytes, bool]:
        chunks: list[bytes] = []
        size = 0
        for current_chunk in response.iter_bytes():
            if time.monotonic() > deadline:
                raise WebAccessError(f"Reading the response took longer than {self._deadline_seconds:.0f}s.")
            if size + len(current_chunk) > limit:
                chunks.append(current_chunk[:limit - size])
                return b"".join(chunks), True
            chunks.append(current_chunk)
            size += len(current_chunk)
        return b"".join(chunks), False

    def fetch(self, url: str, form: Optional[dict[str, str]] = None,
        max_bytes: Optional[int] = None) -> WebPage:
        current_url = self._parse(url)
        method = "POST" if form is not None else "GET"
        deadline = time.monotonic() + self._deadline_seconds

        try:
            with httpx.Client(transport = self._transport, timeout = self._timeout_seconds,
                trust_env = False, follow_redirects = False) as client:
                for _ in range(self._max_redirects + 1):
                    response = self._send(client, method, current_url, form)
                    try:
                        location = response.headers.get("location")
                        if response.status_code in self.REDIRECT_STATUSES and location:
                            current_url = current_url.join(location)
                            if response.status_code in (301, 302, 303):
                                method, form = "GET", None
                            continue
                        if response.status_code >= 400:
                            raise WebAccessError(f"{current_url} answered HTTP {response.status_code}.")

                        content, truncated = self._read(response, max_bytes or self._max_bytes, deadline)
                        return WebPage(
                            url = str(current_url),
                            status_code = response.status_code,
                            content_type = response.headers.get("content-type", "").split(";")[0].strip().lower(),
                            encoding = response.charset_encoding,
                            content = content,
                            truncated = truncated
                        )
                    finally:
                        response.close()
        except httpx.HTTPError as error:
            raise WebAccessError(
                f"{current_url} could not be fetched: {type(error).__name__}: {error or 'no detail'}"
            ) from None

        raise WebAccessError(f"{url} redirected more than {self._max_redirects} times.")
