import pytest
import pathlib
import tempfile
from threading import Barrier, Thread

from db import DatabaseSqlite
from app.server.security import IdentityEntityUser
from app.server.security import IdentityEntityAdmin
from app.server.security import IdentityEntityGuest
from app.server.security import IdentityAccessStoreSql
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessResourcePolicy
from app.server.security import IdentityAccessPolicyStatement


def make_store(path = None):
    database = DatabaseSqlite(path)
    database.start()
    return IdentityAccessStoreSql(database)


def make_user(name = "ana"):
    return IdentityEntityUser(name = name, password_hash = "scrypt$16$1$1$c2FsdA==$a2V5")


def make_policy(name = "Share"):
    return IdentityAccessResourcePolicy(
        name = name,
        statements = [
            IdentityAccessPolicyStatement(
                effect = IdentityAccessPolicyEffect.ALLOW,
                principals = ["vrn:iam::entity/user/*"],
                actions = ["agent:Run"],
                resources = ["vrn:agent::*"]
            )
        ]
    )


class TestIdentityAccessStoreSql:
    def test_an_entity_reads_back_equal_to_what_was_stored(self):
        store = make_store()
        user = make_user()
        store.add_entity(user)
        assert store.get_entity(user.id) == user
        assert store.find_entity("ana") == user

    def test_each_kind_reads_back_as_its_own_class(self):
        store = make_store()
        admin = IdentityEntityAdmin(name = "root", password_hash = "h")
        store.add_entity(admin)
        store.add_entity(make_user())
        assert isinstance(store.find_entity("root"), IdentityEntityAdmin)
        assert isinstance(store.find_entity("ana"), IdentityEntityUser)

    def test_the_password_hash_survives_the_round_trip(self):
        store = make_store()
        user = make_user()
        store.add_entity(user)
        assert store.get_entity(user.id).password_hash.get_secret_value() == user.password_hash.get_secret_value()

    def test_created_at_reads_back_aware_and_equal(self):
        store = make_store()
        user = make_user()
        store.add_entity(user)
        read = store.get_entity(user.id).created_at
        assert read.tzinfo is not None and read == user.created_at

    def test_a_taken_name_is_refused_with_value_error(self):
        store = make_store()
        store.add_entity(make_user())
        with pytest.raises(ValueError):
            store.add_entity(make_user())

    def test_a_guest_is_never_stored(self):
        with pytest.raises(ValueError):
            make_store().add_entity(IdentityEntityGuest())

    def test_unknown_lookups_return_none(self):
        store = make_store()
        assert store.get_entity("missing") is None
        assert store.find_entity("missing") is None
        assert store.get_resource_policy("vrn:agent::x") is None

    def test_a_resource_policy_reads_back_equal_to_what_was_stored(self):
        store = make_store()
        policy = make_policy()
        store.put_resource_policy("vrn:agent::x", policy)
        assert store.get_resource_policy("vrn:agent::x") == policy

    def test_putting_a_policy_again_replaces_it(self):
        store = make_store()
        store.put_resource_policy("vrn:agent::x", make_policy("First"))
        store.put_resource_policy("vrn:agent::x", make_policy("Second"))
        assert store.get_resource_policy("vrn:agent::x").name == "Second"

    def test_accounts_survive_a_restart_which_is_the_whole_point(self):
        path = pathlib.Path(tempfile.mkdtemp()) / "vela47.sqlite3"
        user = make_user()
        make_store(path).add_entity(user)
        assert make_store(path).find_entity("ana") == user

    def test_concurrent_creation_of_one_name_admits_exactly_one(self):
        path = pathlib.Path(tempfile.mkdtemp()) / "vela47.sqlite3"
        store = make_store(path)
        barrier = Barrier(8)
        admitted = []

        def attempt():
            user = make_user("contested")
            barrier.wait()
            try:
                store.add_entity(user)
                admitted.append(user)
            except ValueError:
                pass

        threads = [Thread(target = attempt) for _ in range(8)]
        for current_thread in threads:
            current_thread.start()
        for current_thread in threads:
            current_thread.join()

        assert len(admitted) == 1
        assert store.find_entity("contested") == admitted[0]
