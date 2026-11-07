import httpx


class FakeWebServer:
    """Answers HTTP requests through httpx.MockTransport from a table of routes, keyed by
    the URL the client meant — scheme, Host header and path — rather than the address it
    connected to, since the fetcher connects to a pinned IP. Unknown routes answer 404.
    Every request is recorded, so a test can check where it went and what it carried.

    Routes are callables taking the request, so a response is built fresh each time and
    can be read more than once; page() and redirect() make the common ones."""

    def __init__(self, routes = None) -> None:
        self._routes = dict(routes or {})
        self.requests = []
        self.transport = httpx.MockTransport(self._handle)

    @staticmethod
    def page(content, content_type = "text/html; charset=utf-8", status = 200):
        body = content.encode("utf-8") if isinstance(content, str) else content
        return lambda request: httpx.Response(status, headers = {"content-type": content_type}, content = body)

    @staticmethod
    def redirect(location, status = 302):
        return lambda request: httpx.Response(status, headers = {"location": location})

    def _handle(self, request):
        self.requests.append(request)
        key = f"{request.url.scheme}://{request.headers['host']}{request.url.raw_path.decode('ascii')}"
        route = self._routes.get(key)
        return route(request) if route is not None else httpx.Response(404)
