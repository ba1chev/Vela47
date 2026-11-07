from starlette.datastructures import State

from app.server.security.security_pipeline import SecurityPipeline
from app.server.security.authorization.authorization_service import AuthorizationService
from app.server.security.authentication.authentication_service import AuthenticationService
from app.server.security.identity_access.identity_access_service import IdentityAccessService
from app.server.security.authentication.authentication_token_codec import AuthenticationTokenCodec
from app.server.security.authentication.authentication_password_hasher import AuthenticationPasswordHasher
from app.server.security.identity_access.identity_access_store.identity_access_store_base import IdentityAccessStoreBase


def install_security(state: State, store: IdentityAccessStoreBase,
    password_hasher: AuthenticationPasswordHasher, token_secret: str) -> None:
    """Assembles the security layer and hangs its three entry points on the app state:
    the identity directory, for endpoints that manage identities; the authentication
    service, for the sign-in endpoints; and the pipeline, which every protected endpoint
    runs before doing any work.

    Built once per process, unlike the deep agent, which is built per request. The store
    is passed in — the database-backed one when serving, an in-memory one in tests — and
    so is the hasher, so tests can install the same graph at a cheap cost."""
    identity_access_service = IdentityAccessService(store, password_hasher)
    authentication_service = AuthenticationService(
        identity_access_service,
        AuthenticationTokenCodec(token_secret),
        password_hasher
    )

    state.identity_access_service = identity_access_service
    state.authentication_service = authentication_service
    state.security_pipeline = SecurityPipeline([
        authentication_service,
        AuthorizationService(identity_access_service)
    ])
