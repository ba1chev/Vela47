from fastapi.testclient import TestClient

from app.server.server import app


class TestStaticFilesRevalidated:
    def test_a_static_file_must_be_revalidated_before_reuse(self):
        response = TestClient(app).get("/static/css/base.css")
        assert response.status_code == 200 and response.headers["cache-control"] == "no-cache"

    def test_an_unchanged_file_is_answered_with_not_modified(self):
        client = TestClient(app)
        etag = client.get("/static/js/main.js").headers["etag"]
        response = client.get("/static/js/main.js", headers = {"If-None-Match": etag})
        assert response.status_code == 304 and response.headers["cache-control"] == "no-cache"

    def test_the_page_itself_must_be_revalidated_too(self):
        assert TestClient(app).get("/").headers["cache-control"] == "no-cache"
