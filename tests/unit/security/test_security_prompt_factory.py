import pytest

from app.intelligence.security import SecurityPromptType
from app.intelligence.security import SecurityPromptFactory
from app.intelligence.security import SECURITY_PROMPT_REGISTRY


class TestSecurityPromptFactory:
    def test_every_threat_is_registered(self):
        assert set(SECURITY_PROMPT_REGISTRY) == set(SecurityPromptType)

    @pytest.mark.parametrize("threat", list(SecurityPromptType))
    def test_the_detector_of_a_threat_is_built(self, threat):
        assert SecurityPromptFactory().create(threat).prompt_type is threat

    def test_an_unknown_threat_is_refused(self):
        with pytest.raises(ValueError, match = "No prompt detector class registered"):
            SecurityPromptFactory().create("carrier pigeon")
