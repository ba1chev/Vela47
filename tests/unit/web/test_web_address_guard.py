import httpx
import pytest

from app.intelligence.web import WebAccessError
from app.intelligence.web import WebAddressGuard
from tests.fixtures.web.fake_resolver import FakeResolver


def check(url, table = None):
    return WebAddressGuard(FakeResolver(table)).check(httpx.URL(url))


class TestWebAddressGuard:
    def test_a_public_host_is_allowed_and_its_address_returned(self):
        assert check("https://example.org/page", {"example.org": ["93.184.216.34"]}) == "93.184.216.34"

    def test_the_instance_metadata_address_is_refused(self):
        with pytest.raises(WebAccessError, match = "not a public address"):
            check("http://169.254.169.254/latest/meta-data/iam/")

    def test_a_name_that_resolves_to_a_private_address_is_refused(self):
        with pytest.raises(WebAccessError, match = "10.0.0.5"):
            check("https://intranet.example/", {"intranet.example": ["10.0.0.5"]})

    def test_one_private_address_among_public_ones_is_enough_to_refuse(self):
        with pytest.raises(WebAccessError):
            check("https://mixed.example/", {"mixed.example": ["93.184.216.34", "127.0.0.1"]})

    def test_other_schemes_are_refused(self):
        with pytest.raises(WebAccessError, match = "Only http and https"):
            check("file:///etc/passwd")

    def test_credentials_in_the_url_are_refused(self):
        with pytest.raises(WebAccessError, match = "user name or password"):
            check("https://user:secret@example.org/")

    def test_a_name_that_resolves_to_nothing_is_refused(self):
        with pytest.raises(WebAccessError, match = "did not resolve"):
            check("https://empty.example/", {"empty.example": []})

    def test_private_and_reserved_ranges_are_not_public(self):
        guard = WebAddressGuard(FakeResolver())
        assert not any(guard.is_public(current) for current in (
            "127.0.0.1", "10.1.2.3", "172.16.0.1", "192.168.1.1", "169.254.169.254", "100.64.0.1",
            "0.0.0.0", "224.0.0.1", "::1", "fe80::1%en0", "fd00::1", "not-an-address"
        ))

    def test_private_addresses_hidden_inside_ipv6_are_not_public(self):
        guard = WebAddressGuard(FakeResolver())
        assert not any(guard.is_public(current) for current in (
            "::ffff:169.254.169.254", "2002:a9fe:a9fe::1", "64:ff9b::a9fe:a9fe"
        ))

    def test_public_addresses_are_public(self):
        guard = WebAddressGuard(FakeResolver())
        assert all(guard.is_public(current) for current in ("93.184.216.34", "8.8.8.8", "2606:4700::1111"))
