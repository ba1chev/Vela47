import jwt
from datetime import datetime, timezone

from app.server.security import AuthenticationError
from app.server.security import IdentityAccessRoleSession


class AuthenticationTokenCodec:
    """Turns a role session into a signed JWT and back. The token is the session, since
    the server keeps no session table, so the signature is all that stands between a
    client and a token claiming to be an admin.

    Decoding is strict: the algorithm is pinned to HS256, issuer and audience must be
    ours, and every claim must be present; any failure is an AuthenticationError, never
    a partially trusted session. The secret must be at least 32 bytes, the length of the
    HMAC-SHA256 output."""

    ALGORITHM = "HS256"
    ISSUER = "vela47"
    AUDIENCE = "vela47"
    MIN_SECRET_BYTES = 32
    REQUIRED_CLAIMS = ["sub", "jti", "iat", "exp", "iss", "aud", "entity_type", "role"]

    def __init__(self, secret: str) -> None:
        if len(secret.encode("utf-8")) < self.MIN_SECRET_BYTES:
            raise ValueError(
                f"The token secret must be at least {self.MIN_SECRET_BYTES} bytes long."
            )
        self._secret: str = secret

    def encode(self, session: IdentityAccessRoleSession) -> str:
        return jwt.encode(
            {
                "sub": session.entity_id,
                "jti": session.id,
                "iat": session.issued_at,
                "exp": session.expires_at,
                "iss": self.ISSUER,
                "aud": self.AUDIENCE,
                "entity_type": session.entity_type.value,
                "role": session.role_type.value
            },
            self._secret,
            algorithm = self.ALGORITHM
        )

    def decode(self, token: str) -> IdentityAccessRoleSession:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms = [self.ALGORITHM],
                audience = self.AUDIENCE,
                issuer = self.ISSUER,
                options = {"require": self.REQUIRED_CLAIMS}
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("The session has expired — sign in again.") from None
        except jwt.InvalidTokenError:
            raise AuthenticationError("The session token is invalid.") from None

        try:
            return IdentityAccessRoleSession(
                id = claims["jti"],
                entity_id = claims["sub"],
                entity_type = claims["entity_type"],
                role_type = claims["role"],
                issued_at = datetime.fromtimestamp(claims["iat"], timezone.utc),
                expires_at = datetime.fromtimestamp(claims["exp"], timezone.utc)
            )
        except (TypeError, ValueError, OverflowError, OSError):
            raise AuthenticationError("The session token is invalid.") from None
