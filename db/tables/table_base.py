from sqlalchemy.orm import DeclarativeBase


class TableBase(DeclarativeBase):
    """The declarative base every table derives from, and therefore the one metadata
    object that knows the whole schema. A table describes how rows are laid out and
    nothing more — turning a row into the model the rest of the server works with is the
    job of the store that owns the table, which is what keeps SQLAlchemy from leaking
    past the stores.

    Every column carries a comment, the database's counterpart of a Field description.
    It ends up in the schema itself, so whoever inspects the RDS instance directly sees
    what each column means without opening this repository.

    Columns that hold a document use JSON_DOCUMENT, which is JSONB on PostgreSQL and
    plain JSON on SQLite: the stores read and write it the same way on both."""
