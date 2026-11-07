import jwt
import json
import base64
import pytest
from datetime import datetime, timedelta, timezone

from app.server.security import IdentityEntityType
from app.server.security import AuthenticationError
from app.server.security import IdentityAccessRoleType
from app.server.security import AuthenticationTokenCodec
from app.server.security import IdentityAccessRoleSession

SECRET = "s" * 32


def make_session(issued_at = None, lifetime = timedelta(hours = 1)):
    issued_at = issued_at or datetime.now(timezone.utc).replace(microsecond = 0)
    return IdentityAccessRoleSession(
        entity_id = "e1",
        entity_type = IdentityEntityType.USER,
        role_type = IdentityAccessRoleType.USER,
        issued_at = issued_at,
        expires_at = issued_at + lifetime
    )


def encode_segment(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def decode_segment(segment):
    return json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))


def make_claims(**overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "sub": "e1", "jti": "j1", "iat": now, "exp": now + timedelta(hours = 1),
        "iss": "vela47", "aud": "vela47", "entity_type": "user", "role": "user"
    }
    claims.update(overrides)
    return claims


class TestAuthenticationTokenCodec:
    def test_a_session_survives_a_round_trip(self):
        codec = AuthenticationTokenCodec(SECRET)
        session = make_session()
        assert codec.decode(codec.encode(session)) == session

    def test_a_secret_shorter_than_32_bytes_is_refused(self):
        with pytest.raises(ValueError):
            AuthenticationTokenCodec("s" * 31)

    def test_a_token_signed_with_another_secret_is_refused(self):
        token = AuthenticationTokenCodec("o" * 32).encode(make_session())
        with pytest.raises(AuthenticationError):
            AuthenticationTokenCodec(SECRET).decode(token)

    def test_promoting_yourself_by_editing_the_payload_is_refused(self):
        header, payload, signature = AuthenticationTokenCodec(SECRET).encode(make_session()).split(".")
        claims = decode_segment(payload)
        claims["role"] = "admin"
        claims["entity_type"] = "admin"
        with pytest.raises(AuthenticationError):
            AuthenticationTokenCodec(SECRET).decode(f"{header}.{encode_segment(claims)}.{signature}")

    def test_an_unsigned_none_algorithm_token_is_refused(self):
        claims = decode_segment(AuthenticationTokenCodec(SECRET).encode(make_session()).split(".")[1])
        forged = f"{encode_segment({'alg': 'none', 'typ': 'JWT'})}.{encode_segment(claims)}."
        with pytest.raises(AuthenticationError):
            AuthenticationTokenCodec(SECRET).decode(forged)

    def test_an_expired_token_is_refused_as_expired(self):
        codec = AuthenticationTokenCodec(SECRET)
        stale = make_session(issued_at = datetime.now(timezone.utc).replace(microsecond = 0) - timedelta(hours = 2))
        with pytest.raises(AuthenticationError, match = "expired"):
            codec.decode(codec.encode(stale))

    def test_a_token_meant_for_another_audience_is_refused(self):
        token = jwt.encode(make_claims(aud = "elsewhere"), SECRET, algorithm = "HS256")
        with pytest.raises(AuthenticationError):
            AuthenticationTokenCodec(SECRET).decode(token)

    def test_a_token_from_another_issuer_is_refused(self):
        token = jwt.encode(make_claims(iss = "elsewhere"), SECRET, algorithm = "HS256")
        with pytest.raises(AuthenticationError):
            AuthenticationTokenCodec(SECRET).decode(token)

    def test_a_token_missing_a_claim_is_refused(self):
        claims = make_claims()
        del claims["role"]
        with pytest.raises(AuthenticationError):
            AuthenticationTokenCodec(SECRET).decode(jwt.encode(claims, SECRET, algorithm = "HS256"))

    def test_a_correctly_signed_token_naming_an_unknown_role_is_refused(self):
        token = jwt.encode(make_claims(role = "superuser"), SECRET, algorithm = "HS256")
        with pytest.raises(AuthenticationError):
            AuthenticationTokenCodec(SECRET).decode(token)

    def test_garbage_is_refused(self):
        with pytest.raises(AuthenticationError):
            AuthenticationTokenCodec(SECRET).decode("not-a-token")
