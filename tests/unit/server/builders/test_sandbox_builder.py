import re

from app.server.builders import SANDBOX_COMPOSE_FILES
from app.server.config_environment import ConfigEnvironment


class TestSandboxBuilder:
    def test_every_environment_has_a_compose_project_of_its_own(self):
        assert set(SANDBOX_COMPOSE_FILES) == set(ConfigEnvironment)
        assert SANDBOX_COMPOSE_FILES[ConfigEnvironment.DEV] != SANDBOX_COMPOSE_FILES[ConfigEnvironment.PROD]
        assert all(current_file.is_file() for current_file in SANDBOX_COMPOSE_FILES.values())

    def test_every_bundled_image_has_pytest_for_the_test_subagent(self):
        for current_file in SANDBOX_COMPOSE_FILES.values():
            assert "pytest" in (current_file.parent / "Dockerfile").read_text()

    def test_every_bundled_network_reaches_nothing(self):
        for current_file in SANDBOX_COMPOSE_FILES.values():
            compose = current_file.read_text()
            assert "internal: true" in compose
            assert "gateway_mode_ipv4: isolated" in compose
            assert 'enable_icc: "false"' in compose

    def test_every_bundled_slot_has_a_name_and_an_address_of_its_own(self):
        for current_file in SANDBOX_COMPOSE_FILES.values():
            compose = current_file.read_text()
            names = re.findall(r"container_name: (\S+)", compose)
            addresses = re.findall(r"ipv4_address: (\S+)", compose)
            assert len(names) == len(set(names)) == len(addresses) == len(set(addresses)) == 10
