import pytest

from app.intelligence.security import SecurityType
from app.intelligence.security import SecurityFactory
from app.intelligence.security import SECURITY_REGISTRY
from app.intelligence.security import SecurityPromptType
from app.intelligence.security import SecurityPromptPoisoning


class TestSecurityFactory:
    def test_every_family_is_registered(self):
        assert set(SECURITY_REGISTRY) == set(SecurityType)

    def test_a_detector_is_built_from_its_family_and_its_threat(self):
        detector = SecurityFactory().create(SecurityType.PROMPT, SecurityPromptType.POISONING)
        assert isinstance(detector, SecurityPromptPoisoning)

    def test_an_unknown_family_is_refused(self):
        with pytest.raises(ValueError, match = "No security factory registered"):
            SecurityFactory().create("network", SecurityPromptType.INJECTION)

    def test_a_threat_its_family_does_not_know_is_refused_by_the_family(self):
        with pytest.raises(ValueError, match = "No prompt detector class registered"):
            SecurityFactory().create(SecurityType.PROMPT, "carrier pigeon")
