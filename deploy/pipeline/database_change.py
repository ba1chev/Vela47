from enum import Enum


class DatabaseChange(str, Enum):
    """Enumerates what a release does to the schema. EXPAND adds tables, nullable columns
    or indexes that the previous release ignores, which matters because during a
    deployment both releases run against the same database. CONTRACT drops or renames
    what the previous release still reads, so it ships alone, one release after the code
    stopped using it (see docs/change_management.md)."""

    NONE = "none"
    EXPAND = "expand"
    CONTRACT = "contract"
