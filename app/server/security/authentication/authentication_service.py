from typing import Optional

from app.server.security import SecurityContext
from app.server.security import SecurityServiceBase
from app.server.security import SecurityServiceType
from app.server.security import AuthenticationError
from app.server.security import IdentityAccessService
from app.server.security import IdentityAccessRoleType
from app.server.security import AuthenticationTokenCodec
from app.server.security import IdentityAccessRoleSession
from app.server.security import AuthenticationPasswordHasher


class AuthenticationService(SecurityServiceBase):
    """Establishes who is asking: the first stage of the pipeline and the only part of
    the server that handles a credential. Signing in checks a password against the
    stored hash, or mints a guest, and assumes the requested role through its trust
    policy. Verifying turns a token back into its session on every request and checks
    that the entity still exists, so removing an account ends its access at once.

    A failed sign-in reads the same and takes as long whether the name is unknown or the
    password is wrong."""

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
