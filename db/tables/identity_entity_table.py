from datetime import datetime
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db import TableBase
from db import UtcDateTime


class IdentityEntityTable(TableBase):
    """One row per stored identity — admins and users. Guests never get a row: they prove
    nothing and exist only inside their session token, which is what keeps this table
    from growing by one row per page load.

    The unique constraint on name is what makes creating an account atomic. Two requests
    racing to take the same name — on the same server or on two EC2 instances — both
    reach the insert, and the database decides which one wins, not a check made
    beforehand."""

    __tablename__ = "identity_entities"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key = True,
        comment = "Random hex id of the entity — the stable part of its VRN, never reused."
    )
    type: Mapped[str] = mapped_column(
        String(16),
        comment = "Kind of entity: 'admin' or 'user'. Decides which model class the row is read into."
    )
    name: Mapped[str] = mapped_column(
        String(32),
        unique = True,
        comment = "Lower-case sign-in name, unique across all entities."
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        comment = "Self-describing scrypt hash of the password, never the password itself."
    )
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime(),
        comment = "When the entity was created, in UTC."
    )
