import json
import httpx
import pytest

from app.intelligence.web import WebAccessError
from app.intelligence.web import WebSearchTavily

RESULTS = {
    "query": "rotate rds secret",
    "results": [
        {"title": "Rotate AWS Secrets Manager secrets", "url": "https://docs.aws.amazon.com/rotating-secrets.html", "content": "Rotation   updates\nthe secret.", "score": 0.9},
        {"title": "Duplicate", "url": "https://docs.aws.amazon.com/rotating-secrets.html", "content": "Same page again.", "score": 0.5},
        {"title": "", "url": "https://example.org/untitled", "content": "", "score": 0.4},
        {"title": "Not a web page", "url": "ftp://example.org/file", "content": "x", "score": 0.3}
    ],
    "response_time": 0.4
}


def make_search(status = 200, body = None, error = None):
    requests = []

    def handler(request):
        requests.append(request)
        if error is not None:
            raise error
        return httpx.Response(status, json = RESULTS if body is None else body)

    return WebSearchTavily("tvly-test-key", transport = httpx.MockTransport(handler)), requests


class TestWebSearchTavily:
    def test_a_search_is_one_basic_post_with_the_key_as_a_bearer_token(self):
        search, requests = make_search()
        search.search("rotate rds secret", max_results = 5)
        request = requests[0]
        body = json.loads(request.content)
        assert request.method == "POST" and str(request.url) == WebSearchTavily.SEARCH_URL
        assert request.headers["authorization"] == "Bearer tvly-test-key"
        assert body["query"] == "rotate rds secret" and body["max_results"] == 5 and body["search_depth"] == "basic"
        assert body["include_answer"] is False and body["include_raw_content"] is False

    def test_results_become_titled_linked_results_with_one_line_snippets(self):
        results = make_search()[0].search("rotate rds secret")
        assert results[0].title == "Rotate AWS Secrets Manager secrets"
        assert results[0].url == "https://docs.aws.amazon.com/rotating-secrets.html"
        assert results[0].snippet == "Rotation updates the secret."

    def test_a_page_listed_twice_is_kept_once_and_only_web_addresses_are_kept(self):
        results = make_search()[0].search("rotate rds secret")
        assert [current.url for current in results] == [
            "https://docs.aws.amazon.com/rotating-secrets.html", "https://example.org/untitled"
        ]

    def test_a_result_without_a_title_is_named_by_its_address(self):
        assert make_search()[0].search("q")[1].title == "https://example.org/untitled"

    def test_the_count_asked_for_stays_within_what_the_api_allows(self):
        search, requests = make_search()
        search.search("q", max_results = 50)
        search.search("q", max_results = 0)
        assert [json.loads(current.content)["max_results"] for current in requests] == [20, 1]

    def test_no_results_is_an_empty_list(self):
        assert make_search(body = {"query": "q", "results": []})[0].search("q") == []

    def test_a_refused_key_is_an_error_that_says_to_use_the_pages_already_found(self):
        with pytest.raises(WebAccessError, match = "refused this server's key.*fetch_url"):
            make_search(status = 401)[0].search("q")

    def test_a_spent_quota_is_an_error_not_an_empty_search(self):
        for current_status in (429, 432, 433):
            with pytest.raises(WebAccessError, match = "used up its searches"):
                make_search(status = current_status)[0].search("q")

    def test_another_failure_status_is_reported_with_its_code(self):
        with pytest.raises(WebAccessError, match = "status 500"):
            make_search(status = 500)[0].search("q")

    def test_an_unreachable_api_is_an_error(self):
        with pytest.raises(WebAccessError, match = "could not be reached"):
            make_search(error = httpx.ConnectError("refused"))[0].search("q")
