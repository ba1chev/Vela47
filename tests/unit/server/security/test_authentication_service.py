import pytest

from app.server.security.security_context import SecurityContext
from app.server.security.security_service_type import SecurityServiceType
from app.server.security.authorization.authorization_error import AuthorizationError
from app.server.security.authentication.authentication_error import AuthenticationError
from app.server.security.identity_access.identity_access_action import IdentityAccessAction
from app.server.security.authentication.authentication_service import AuthenticationService
from app.server.security.identity_access.identity_access_service import IdentityAccessService
from app.server.security.authentication.authentication_token_codec import AuthenticationTokenCodec
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType
from app.server.security.authentication.authentication_password_hasher import AuthenticationPasswordHasher
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType
from app.server.security.identity_access.identity_access_store.identity_access_store_in_memory import IdentityAccessStoreInMemory

SECRET = "s" * 32
PASSWORD = "correct-horse-battery"


def make_services():
    hasher = AuthenticationPasswordHasher(cost = 16, block_size = 1)
    identity_access_service = IdentityAccessService(IdentityAccessStoreInMemory(), hasher)
    authentication_service = AuthenticationService(
        identity_access_service, AuthenticationTokenCodec(SECRET), hasher
    )
    identity_access_service.create_entity(IdentityEntityType.ADMIN, "root", PASSWORD)
    identity_access_service.create_entity(IdentityEntityType.USER, "ana", PASSWORD)
    return identity_access_service, authentication_service


def make_authentication():
    return make_services()[1]


class TestAuthenticationService:
    def test_its_type_is_authentication(self):
        assert make_authentication().security_type is SecurityServiceType.AUTHENTICATION

    def test_sign_in_assumes_the_default_role(self):
        assert make_authentication().sign_in("ana", PASSWORD).role_type is IdentityAccessRoleType.USER

    def test_sign_in_may_ask_for_another_trusted_role(self):
        session = make_authentication().sign_in("root", PASSWORD, IdentityAccessRoleType.USER)
        assert session.role_type is IdentityAccessRoleType.USER
        assert session.entity_type is IdentityEntityType.ADMIN

    def test_sign_in_for_a_role_that_does_not_trust_you_is_refused(self):
        with pytest.raises(AuthorizationError):
            make_authentication().sign_in("ana", PASSWORD, IdentityAccessRoleType.ADMIN)

    def test_names_are_matched_case_insensitively(self):
        assert make_authentication().sign_in("ANA", PASSWORD).role_type is IdentityAccessRoleType.USER

    def test_a_wrong_password_is_refused(self):
        with pytest.raises(AuthenticationError):
            make_authentication().sign_in("ana", "wrong-horse-battery")

    def test_an_unknown_name_fails_with_the_same_message_as_a_wrong_password(self):
        authentication_service = make_authentication()
        with pytest.raises(AuthenticationError) as wrong_password:
            authentication_service.sign_in("ana", "wrong-horse-battery")
        with pytest.raises(AuthenticationError) as unknown_name:
            authentication_service.sign_in("nobody", PASSWORD)
        assert str(wrong_password.value) == str(unknown_name.value)

    def test_a_guest_signs_in_without_credentials(self):
        session = make_authentication().sign_in_guest()
        assert session.entity_type is IdentityEntityType.GUEST
        assert session.role_type is IdentityAccessRoleType.GUEST

    def test_every_guest_is_someone_new(self):
        authentication_service = make_authentication()
        assert authentication_service.sign_in_guest().entity_id != authentication_service.sign_in_guest().entity_id

    def test_an_issued_token_verifies_back_to_its_session(self):
        authentication_service = make_authentication()
        session = authentication_service.sign_in("ana", PASSWORD)
        assert authentication_service.verify(authentication_service.issue_token(session)) == session

    def test_a_guest_token_verifies_although_guests_are_never_stored(self):
        authentication_service = make_authentication()
        session = authentication_service.sign_in_guest()
        assert authentication_service.verify(authentication_service.issue_token(session)) == session

    def test_verifying_without_a_token_is_refused(self):
        for current_token in [None, ""]:
            with pytest.raises(AuthenticationError):
                make_authentication().verify(current_token)

    def test_a_validly_signed_token_whose_entity_is_gone_is_refused(self):
        issuer = make_authentication()
        token = issuer.issue_token(issuer.sign_in("ana", PASSWORD))
        hasher = AuthenticationPasswordHasher(cost = 16, block_size = 1)
        forgetful = AuthenticationService(
            IdentityAccessService(IdentityAccessStoreInMemory(), hasher),
            AuthenticationTokenCodec(SECRET),
            hasher
        )
        with pytest.raises(AuthenticationError):
            forgetful.verify(token)

    def test_execute_writes_the_verified_session_into_the_context(self):
        authentication_service = make_authentication()
        session = authentication_service.sign_in("ana", PASSWORD)
        context = SecurityContext(
            token = authentication_service.issue_token(session),
            action = IdentityAccessAction.AGENT_RUN,
            resource = "vrn:agent::deep-agent"
        )
        authentication_service.execute(context)
        assert context.session == session

    def test_the_token_never_shows_in_a_context_repr_or_dump(self):
        context = SecurityContext(
            token = "secret-token", action = IdentityAccessAction.AGENT_RUN, resource = "vrn:agent::x"
        )
        assert "secret-token" not in repr(context)
        assert "secret-token" not in str(context.model_dump())
