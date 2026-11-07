from typing import Optional
from sqlalchemy.engine import Dialect
from datetime import datetime, timezone
from sqlalchemy import DateTime, TypeDecorator


class UtcDateTime(TypeDecorator):
    """A timestamp column that always stores UTC and always hands back an aware datetime.
    PostgreSQL keeps the time zone and SQLite does not: read back from SQLite, a plain
    DateTime comes out naive, and comparing it with an aware one raises. Converting here
    means no code above the tables ever finds out which backend it ran on.

    A naive datetime is refused on the way in rather than assumed to be UTC. Every
    timestamp in the server is created aware, so a naive one is a bug worth surfacing."""

    impl = DateTime(timezone = True)
    cache_ok = True

    def process_bind_param(self, value: Optional[datetime], dialect: Dialect) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Refusing to store a naive datetime — timestamps must carry a time zone.")
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: Optional[datetime], dialect: Dialect) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo = timezone.utc)
        return value.astimezone(timezone.utc)
