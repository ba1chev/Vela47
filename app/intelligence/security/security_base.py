from abc import ABC, abstractmethod

from app.intelligence.security import SecurityType
from app.intelligence.security import SecurityVerdict


class SecurityBase(ABC):
    """Abstract base for a detector: one threat, looked for in one text at a time.
    inspect() only reads: it never changes, withholds or refuses the text, so a detector
    can watch every input of a model without altering a run, and what to do about a
    verdict stays with whoever asked for it.

    A detector keeps nothing between texts, so one instance serves every run of the
    process."""

    @property
    @abstractmethod
    def security_type(self) -> SecurityType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def inspect(self, text: str) -> SecurityVerdict:
        raise NotImplementedError("Must be implemented")
