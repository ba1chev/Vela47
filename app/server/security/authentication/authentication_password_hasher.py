import base64
import hashlib
import secrets
from typing import Optional
from hmac import compare_digest


class AuthenticationPasswordHasher:
    """Salted scrypt hashes from the standard library, at OWASP's minimum cost (N=2^17,
    r=8, p=1); the cost is a constructor argument so tests run cheaply. Each hash names
    its own parameters, so raising the cost never locks out existing accounts, and
    parameters read back are bounded so a tampered record cannot make a sign-in allocate
    gigabytes.

    verify() with no stored hash still spends one full hash on a dummy, so an unknown
    name takes as long as a wrong password and the clock does not reveal which names
    exist."""

    ALGORITHM = "scrypt"
    SEPARATOR = "$"
    SALT_BYTES = 16
    KEY_BYTES = 32
    MIN_PASSWORD_CHARS = 12
    MAX_PASSWORD_CHARS = 1024
    MAX_COST = 2 ** 20
    MAX_BLOCK_SIZE = 32
    MAX_PARALLELISM = 16

    def __init__(self, cost: int = 2 ** 17, block_size: int = 8, parallelism: int = 1) -> None:
        self._cost: int = cost
        self._block_size: int = block_size
        self._parallelism: int = parallelism
        self._dummy_hash: str = self._encode(secrets.token_urlsafe(32))

    def _derive(self, password: str, salt: bytes, cost: int,
        block_size: int, parallelism: int) -> bytes:
        return hashlib.scrypt(
            password.encode("utf-8"),
            salt = salt,
            n = cost,
            r = block_size,
            p = parallelism,
            maxmem = 256 * cost * block_size + 1024 * 1024,
            dklen = self.KEY_BYTES
        )

    def _encode(self, password: str) -> str:
        salt = secrets.token_bytes(self.SALT_BYTES)
        key = self._derive(password, salt, self._cost, self._block_size, self._parallelism)
        return self.SEPARATOR.join([
            self.ALGORITHM,
            str(self._cost),
            str(self._block_size),
            str(self._parallelism),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(key).decode("ascii")
        ])

    def _check(self, password: str, encoded: str) -> bool:
        try:
            algorithm, cost, block_size, parallelism, salt, key = encoded.split(self.SEPARATOR)
            cost, block_size, parallelism = int(cost), int(block_size), int(parallelism)
            salt, key = base64.b64decode(salt, validate = True), base64.b64decode(key, validate = True)
        except ValueError:
            return False

        if algorithm != self.ALGORITHM:
            return False
        if not (1 < cost <= self.MAX_COST and 0 < block_size <= self.MAX_BLOCK_SIZE
            and 0 < parallelism <= self.MAX_PARALLELISM):
            return False

        try:
            candidate = self._derive(password, salt, cost, block_size, parallelism)
        except ValueError:
            return False
        return compare_digest(candidate, key)

    def hash(self, password: str) -> str:
        if not self.MIN_PASSWORD_CHARS <= len(password) <= self.MAX_PASSWORD_CHARS:
            raise ValueError(
                f"A password must be between {self.MIN_PASSWORD_CHARS} and "
                f"{self.MAX_PASSWORD_CHARS} characters long."
            )
        return self._encode(password)

    def verify(self, password: str, encoded: Optional[str]) -> bool:
        if encoded is None:
            self._check(password, self._dummy_hash)
            return False
        return self._check(password, encoded)
