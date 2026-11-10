from starlette.datastructures import State

from app.server.security import SecurityPipeline
from app.server.security import AuthorizationService
from app.server.security import AuthenticationService
from app.server.security import IdentityAccessService
from app.server.security import IdentityAccessStoreBase
from app.server.security import AuthenticationTokenCodec
from app.server.security import AuthenticationPasswordHasher


def install_security(state: State, store: IdentityAccessStoreBase,
    password_hasher: AuthenticationPasswordHasher, token_secret: str) -> None:
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
