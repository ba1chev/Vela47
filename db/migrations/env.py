from alembic import context
from sqlalchemy import create_engine

from db import TableBase

connection = context.config.attributes.get("connection")

if connection is None:
    engine = create_engine(context.config.get_main_option("sqlalchemy.url"))
    with engine.begin() as connection:
        context.configure(
            connection = connection,
            target_metadata = TableBase.metadata,
            render_as_batch = connection.dialect.name == "sqlite"
        )
        context.run_migrations()
else:
    context.configure(
        connection = connection,
        target_metadata = TableBase.metadata,
        render_as_batch = connection.dialect.name == "sqlite"
    )
    with context.begin_transaction():
        context.run_migrations()
