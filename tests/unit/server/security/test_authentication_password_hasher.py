import pytest

from app.server.security.authentication.authentication_password_hasher import AuthenticationPasswordHasher

PASSWORD = "correct-horse-battery"


def make_hasher(cost = 16):
    return AuthenticationPasswordHasher(cost = cost, block_size = 1)


class TestAuthenticationPasswordHasher:
    def test_the_right_password_verifies(self):
        hasher = make_hasher()
        assert hasher.verify(PASSWORD, hasher.hash(PASSWORD))

    def test_a_wrong_password_does_not(self):
        hasher = make_hasher()
        assert not hasher.verify("wrong-horse-battery", hasher.hash(PASSWORD))

    def test_the_same_password_hashes_differently_every_time(self):
        hasher = make_hasher()
        assert hasher.hash(PASSWORD) != hasher.hash(PASSWORD)

    def test_the_hash_names_its_algorithm_and_parameters(self):
        assert make_hasher().hash(PASSWORD).startswith("scrypt$16$1$1$")

    def test_a_hash_made_at_an_older_cost_still_verifies(self):
        assert make_hasher(cost = 32).verify(PASSWORD, make_hasher(cost = 16).hash(PASSWORD))

    def test_no_stored_hash_verifies_false(self):
        assert not make_hasher().verify(PASSWORD, None)

    def test_malformed_hashes_verify_false(self):
        hasher = make_hasher()
        for current_hash in ["", "scrypt", "scrypt$16$1$1$salt", "scrypt$x$1$1$AA==$AA==", "scrypt$16$1$1$!!$AA=="]:
            assert not hasher.verify(PASSWORD, current_hash)

    def test_another_algorithm_verifies_false(self):
        hasher = make_hasher()
        assert not hasher.verify(PASSWORD, hasher.hash(PASSWORD).replace("scrypt", "bcrypt", 1))

    def test_absurd_parameters_from_a_tampered_hash_are_refused(self):
        hasher = make_hasher()
        parts = hasher.hash(PASSWORD).split("$")
        parts[1] = str(2 ** 30)
        assert not hasher.verify(PASSWORD, "$".join(parts))

    def test_a_password_shorter_than_twelve_characters_is_refused(self):
        with pytest.raises(ValueError):
            make_hasher().hash("eleven-char")

    def test_a_password_longer_than_the_limit_is_refused(self):
        with pytest.raises(ValueError):
            make_hasher().hash("x" * 1025)
