from typing import Optional

from app.server.security.security_context import SecurityContext
from app.server.security.security_service_base import SecurityServiceBase
from app.server.security.security_service_type import SecurityServiceType
from app.server.security.authentication.authentication_error import AuthenticationError
from app.server.security.identity_access.identity_access_service import IdentityAccessService
from app.server.security.authentication.authentication_token_codec import AuthenticationTokenCodec
from app.server.security.identity_access.identity_access_role_session import IdentityAccessRoleSession
from app.server.security.authentication.authentication_password_hasher import AuthenticationPasswordHasher
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType


class AuthenticationService(SecurityServiceBase):
    """Establishes who is asking — the first stage of the pipeline, and the only part of
    the server that ever handles a credential. It has two jobs, which meet at the role
    session.

    Signing in turns credentials into a session. A password is checked against the
    entity's stored hash and the requested role is then assumed through that role's
    trust policy; a guest has no credential and is minted on the spot. Verifying runs on
    every request and turns a token back into its session, checking again that the
    entity behind it still exists — so removing an account ends its access immediately
    instead of when its tokens happen to expire.

    A failed sign-in says the same thing whether the name is unknown or the password is
    wrong, and takes the same time either way, so neither the message nor the clock
    reveals which accounts exist."""

    def __init__(self, identity_access_service: IdentityAccessService,
        token_codec: AuthenticationTokenCodec,
        password_hasher: AuthenticationPasswordHasher) -> None:
        self._identity_access_service: IdentityAccessService = identity_access_service
        self._token_codec: AuthenticationTokenCodec = token_codec
        self._password_hasher: AuthenticationPasswordHasher = password_hasher

    @property
    def security_type(self) -> SecurityServiceType:
        return SecurityServiceType.AUTHENTICATION

    def sign_in(self, name: str, password: str,
        role_type: Optional[IdentityAccessRoleType] = None) -> IdentityAccessRoleSession:
        entity = self._identity_access_service.find_entity(name)
        stored_hash = (
            entity.password_hash.get_secret_value()
            if entity is not None and entity.password_hash is not None
            else None
        )

        if not self._password_hasher.verify(password, stored_hash):
            raise AuthenticationError("The name or password is incorrect.")

        return self._identity_access_service.assume_role(entity, role_type)

    def sign_in_guest(self) -> IdentityAccessRoleSession:
        return self._identity_access_service.assume_role(
            self._identity_access_service.create_guest()
        )

    def issue_token(self, session: IdentityAccessRoleSession) -> str:
        return self._token_codec.encode(session)

    def verify(self, token: Optional[str]) -> IdentityAccessRoleSession:
        if not token:
            raise AuthenticationError("No session was presented — sign in first.")

        session = self._token_codec.decode(token)
        if self._identity_access_service.resolve_entity(session) is None:
            raise AuthenticationError("The identity this session belongs to no longer exists.")
        return session

    def execute(self, context: SecurityContext) -> None:
        context.session = self.verify(context.token)
