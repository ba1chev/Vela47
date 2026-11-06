import pytest
from threading import Barrier, Thread

from app.server.security.identity_access.identity_entities.identity_entity_user import IdentityEntityUser
from app.server.security.identity_access.identity_access_policies.identity_access_policy_effect import IdentityAccessPolicyEffect
from app.server.security.identity_access.identity_access_store.identity_access_store_in_memory import IdentityAccessStoreInMemory
from app.server.security.identity_access.identity_access_policies.identity_access_policy_statement import IdentityAccessPolicyStatement
from app.server.security.identity_access.identity_access_policies.identity_access_resource_policy.identity_access_resource_policy import IdentityAccessResourcePolicy


def make_user(name = "ana"):
    return IdentityEntityUser(name = name, password_hash = "h")


def make_policy(name = "Share"):
    return IdentityAccessResourcePolicy(
        name = name,
        statements = [
            IdentityAccessPolicyStatement(
                effect = IdentityAccessPolicyEffect.ALLOW,
                principals = ["*"],
                actions = ["agent:Run"],
                resources = ["*"]
            )
        ]
    )


class TestIdentityAccessStoreInMemory:
    def test_an_added_entity_can_be_got_by_id_and_found_by_name(self):
        store = IdentityAccessStoreInMemory()
        user = make_user()
        store.add_entity(user)
        assert store.get_entity(user.id) is user
        assert store.find_entity("ana") is user

    def test_a_taken_name_is_refused(self):
        store = IdentityAccessStoreInMemory()
        store.add_entity(make_user())
        with pytest.raises(ValueError):
            store.add_entity(make_user())

    def test_unknown_lookups_return_none(self):
        store = IdentityAccessStoreInMemory()
        assert store.get_entity("missing") is None
        assert store.find_entity("missing") is None
        assert store.get_resource_policy("vrn:agent::x") is None

    def test_a_resource_policy_is_found_by_its_exact_resource_only(self):
        store = IdentityAccessStoreInMemory()
        policy = make_policy()
        store.put_resource_policy("vrn:session:1:session/a", policy)
        assert store.get_resource_policy("vrn:session:1:session/a") is policy
        assert store.get_resource_policy("vrn:session:1:session/ab") is None

    def test_putting_a_policy_again_replaces_it(self):
        store = IdentityAccessStoreInMemory()
        store.put_resource_policy("vrn:x:", make_policy("First"))
        store.put_resource_policy("vrn:x:", make_policy("Second"))
        assert store.get_resource_policy("vrn:x:").name == "Second"

    def test_len_counts_entities(self):
        store = IdentityAccessStoreInMemory()
        store.add_entity(make_user("ana"))
        store.add_entity(make_user("bob"))
        assert len(store) == 2

    def test_concurrent_creation_of_one_name_admits_exactly_one(self):
        store = IdentityAccessStoreInMemory()
        barrier = Barrier(16)
        admitted = []

        def attempt():
            user = make_user("contested")
            barrier.wait()
            try:
                store.add_entity(user)
                admitted.append(user)
            except ValueError:
                pass

        threads = [Thread(target = attempt) for _ in range(16)]
        for current_thread in threads:
            current_thread.start()
        for current_thread in threads:
            current_thread.join()

        assert len(admitted) == 1
        assert len(store) == 1
