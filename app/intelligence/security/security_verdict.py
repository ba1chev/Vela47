from pydantic import BaseModel, Field

from app.intelligence.security import SecurityType


class SecurityVerdict(BaseModel):
    """What one detector found in one text. Every signature that matched is kept with the
    text it matched, so whoever reads the verdict, a person in the trace or a later
    stage, sees why without searching the text again. flagged is only a reading of the
    matches and is never set on its own: a verdict without a match is clean.

    Frozen like the messages it is written about, and plain JSON, since it travels in
    trace events and in the metadata of an answer."""

    model_config = {"frozen": True}

    security_type: SecurityType = Field(
        description = "Family of the threat that was looked for. The verdict of each family "
            "names the threat within it."
    )
    matches: dict[str, str] = Field(
        default_factory = dict,
        description = "Every signature that matched, by name, with the text it matched, cut to a "
            "short excerpt. Empty when nothing matched."
    )

    signatures: list[str] = Field(
        default_factory = list,
        description = "Name of every signature the text was checked against, matched or not, so a "
            "clean verdict still says what it is clean of."
    )
    characters: int = Field(
        default = 0,
        ge = 0,
        description = "Length of the inspected text in characters, before any normalisation."
    )

    @property
    def flagged(self) -> bool:
        return bool(self.matches)
