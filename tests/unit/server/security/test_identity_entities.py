import pytest
from pydantic import ValidationError

from app.server.security import IdentityEntityBase
from app.server.security import IdentityEntityType
from app.server.security import IdentityEntityUser
from app.server.security import IdentityEntityAdmin
from app.server.security import IdentityEntityGuest
from app.server.security import IdentityEntityFactory
from app.server.security import IdentityAccessRoleType
from app.server.security import IDENTITY_ENTITY_REGISTRY


def make_user(name = "ana"):
    return IdentityEntityUser(name = name, password_hash = "scrypt$hash")


class TestIdentityEntities:
    def test_names_are_normalised_to_lower_case(self):
        assert make_user("  Ana.Maria ").name == "ana.maria"

    def test_a_name_with_a_space_inside_is_refused(self):
        with pytest.raises(ValidationError):
            make_user("ana maria")

    def test_a_name_shorter_than_three_characters_is_refused(self):
        with pytest.raises(ValidationError):
            make_user("ab")

    def test_a_name_may_not_start_with_punctuation(self):
        with pytest.raises(ValidationError):
            make_user(".ana")

    def test_users_and_admins_require_a_password_hash(self):
        with pytest.raises(ValidationError):
            IdentityEntityUser(name = "ana")
        with pytest.raises(ValidationError):
            IdentityEntityAdmin(name = "root")

    def test_a_guest_cannot_hold_a_password_hash(self):
        with pytest.raises(ValidationError):
            IdentityEntityGuest(password_hash = "scrypt$hash")

    def test_the_password_hash_never_shows_in_repr_or_a_dump(self):
        user = make_user()
        assert "scrypt$hash" not in repr(user)
        assert "scrypt$hash" not in str(user.model_dump())
        assert user.password_hash.get_secret_value() == "scrypt$hash"

    def test_each_kind_defaults_to_its_own_role(self):
        assert IdentityEntityAdmin(name = "root", password_hash = "h").default_role is IdentityAccessRoleType.ADMIN
        assert make_user().default_role is IdentityAccessRoleType.USER
        assert IdentityEntityGuest().default_role is IdentityAccessRoleType.GUEST

    def test_the_vrn_carries_the_kind_and_the_id(self):
        user = make_user()
        assert user.vrn == f"vrn:iam::entity/user/{user.id}"

    def test_every_entity_gets_its_own_id(self):
        assert make_user().id != make_user().id

    def test_entities_are_frozen(self):
        with pytest.raises(ValidationError):
            make_user().name = "someone-else"

    def test_the_base_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            IdentityEntityBase(type = IdentityEntityType.USER, name = "ana")


class TestIdentityEntityFactory:
    def test_every_entity_type_is_registered(self):
        assert set(IDENTITY_ENTITY_REGISTRY) == set(IdentityEntityType)

    def test_it_builds_each_kind(self):
        factory = IdentityEntityFactory()
        assert factory.create(IdentityEntityType.ADMIN, name = "root", password_hash = "h").type is IdentityEntityType.ADMIN
        assert factory.create(IdentityEntityType.USER, name = "ana", password_hash = "h").type is IdentityEntityType.USER
        assert factory.create(IdentityEntityType.GUEST).type is IdentityEntityType.GUEST

    def test_it_forwards_keyword_arguments(self):
        assert IdentityEntityFactory().create(IdentityEntityType.GUEST, id = "abc").id == "abc"

    def test_an_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            IdentityEntityFactory().create("robot")
