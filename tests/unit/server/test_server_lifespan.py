import pytest

from app.server.config import Config
from app.server.security import IdentityEntityType
from app.server.security import IdentityAccessService
from app.server.server_lifespan import _bootstrap_admin
from app.server.security import IdentityAccessStoreInMemory
from app.server.security import AuthenticationPasswordHasher
from tests.fixtures.security.racing_identity_access_store import RacingIdentityAccessStore

PASSWORD = "a-long-enough-password"


def make_service(store = None):
    return IdentityAccessService(
        store or IdentityAccessStoreInMemory(), AuthenticationPasswordHasher(cost = 16, block_size = 1)
    )


def make_config(password = PASSWORD):
    return Config(admin_username = "root", admin_password = password)


class TestServerLifespan:
    def test_the_configured_admin_is_created_on_the_first_start(self):
        service = make_service()
        _bootstrap_admin(service, make_config())
        assert service.find_entity("root").type is IdentityEntityType.ADMIN

    def test_an_existing_admin_is_left_as_it_is(self):
        service = make_service()
        existing = service.create_entity(IdentityEntityType.ADMIN, "root", PASSWORD)
        _bootstrap_admin(service, make_config("another-long-password"))
        assert service.find_entity("root").id == existing.id

    def test_without_admin_credentials_nobody_is_created(self):
        service = make_service()
        _bootstrap_admin(service, Config())
        assert service.find_entity("root") is None

    def test_an_admin_created_by_another_server_meanwhile_does_not_stop_the_start(self):
        service = make_service(RacingIdentityAccessStore())
        _bootstrap_admin(service, make_config())
        assert service.find_entity("root") is not None

    def test_an_admin_that_cannot_be_created_still_stops_the_start(self):
        service = make_service()
        with pytest.raises(ValueError):
            _bootstrap_admin(service, make_config("short"))
        assert service.find_entity("root") is None
