import pytest
from datetime import timedelta

from app.server.security import AuthorizationError
from app.server.security import IdentityEntityType
from app.server.security import IdentityAccessService
from app.server.security import IdentityAccessRoleType
from app.server.security import IdentityAccessRoleSession
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessStoreInMemory
from app.server.security import AuthenticationPasswordHasher
from app.server.security import IdentityAccessResourcePolicy
from app.server.security import IdentityAccessPolicyStatement

PASSWORD = "correct-horse-battery"


def make_service():
    hasher = AuthenticationPasswordHasher(cost = 16, block_size = 1)
    return IdentityAccessService(IdentityAccessStoreInMemory(), hasher)


def make_entity(service, entity_type = IdentityEntityType.USER, name = "ana"):
    return service.create_entity(entity_type, name, PASSWORD)


class TestIdentityAccessService:
    def test_a_created_entity_stores_a_hash_not_the_password(self):
        hashed = make_entity(make_service()).password_hash.get_secret_value()
        assert hashed.startswith("scrypt$")
        assert PASSWORD not in hashed

    def test_names_are_found_case_insensitively(self):
        service = make_service()
        entity = make_entity(service, name = "Ana")
        assert service.find_entity("  ANA ") is entity

    def test_guests_cannot_be_created_as_accounts(self):
        with pytest.raises(ValueError):
            make_entity(make_service(), IdentityEntityType.GUEST)

    def test_a_short_password_is_refused(self):
        with pytest.raises(ValueError):
            make_service().create_entity(IdentityEntityType.USER, "ana", "short")

    def test_a_duplicate_name_is_refused(self):
        service = make_service()
        make_entity(service)
        with pytest.raises(ValueError):
            make_entity(service, IdentityEntityType.ADMIN, "ANA")

    def test_an_entity_assumes_its_default_role(self):
        service = make_service()
        assert service.assume_role(make_entity(service)).role_type is IdentityAccessRoleType.USER

    def test_an_admin_may_assume_the_user_role(self):
        service = make_service()
        admin = make_entity(service, IdentityEntityType.ADMIN, "root")
        assert service.assume_role(admin, IdentityAccessRoleType.USER).role_type is IdentityAccessRoleType.USER

    def test_a_user_may_not_assume_the_admin_role(self):
        service = make_service()
        with pytest.raises(AuthorizationError):
            service.assume_role(make_entity(service), IdentityAccessRoleType.ADMIN)

    def test_a_guest_may_not_assume_the_user_role(self):
        service = make_service()
        with pytest.raises(AuthorizationError):
            service.assume_role(service.create_guest(), IdentityAccessRoleType.USER)

    def test_a_session_lasts_as_long_as_its_role_allows(self):
        service = make_service()
        admin = make_entity(service, IdentityEntityType.ADMIN, "root")
        session = service.assume_role(admin)
        expected = service.get_role(IdentityAccessRoleType.ADMIN).max_session_seconds
        assert session.expires_at - session.issued_at == timedelta(seconds = expected)

    def test_session_times_are_whole_seconds(self):
        service = make_service()
        assert service.assume_role(make_entity(service)).issued_at.microsecond == 0

    def test_a_guest_is_never_stored(self):
        service = make_service()
        guest = service.create_guest()
        assert service.get_entity(guest.id) is None

    def test_a_guest_is_rebuilt_from_its_session(self):
        service = make_service()
        session = service.assume_role(service.create_guest())
        assert service.resolve_entity(session).id == session.entity_id

    def test_a_stored_entity_is_resolved_from_its_session(self):
        service = make_service()
        entity = make_entity(service)
        assert service.resolve_entity(service.assume_role(entity)) is entity

    def test_a_session_claiming_the_wrong_kind_resolves_to_nothing(self):
        service = make_service()
        user = make_entity(service)
        forged = service.assume_role(user).model_copy(update = {"entity_type": IdentityEntityType.ADMIN})
        assert service.resolve_entity(forged) is None

    def test_a_session_for_an_unknown_entity_resolves_to_nothing(self):
        session = IdentityAccessRoleSession(
            entity_id = "gone",
            entity_type = IdentityEntityType.USER,
            role_type = IdentityAccessRoleType.USER,
            issued_at = "2026-01-01T00:00:00Z",
            expires_at = "2026-01-01T01:00:00Z"
        )
        assert make_service().resolve_entity(session) is None

    def test_resource_policies_round_trip(self):
        service = make_service()
        policy = IdentityAccessResourcePolicy(
            name = "Share",
            statements = [
                IdentityAccessPolicyStatement(
                    effect = IdentityAccessPolicyEffect.ALLOW,
                    principals = ["*"],
                    actions = ["agent:Run"],
                    resources = ["*"]
                )
            ]
        )
        service.put_resource_policy("vrn:session:1:session/a", policy)
        assert service.get_resource_policy("vrn:session:1:session/a") is policy

    def test_an_unregistered_role_type_raises_value_error(self):
        with pytest.raises(ValueError):
            make_service().get_role("superuser")
