"""The trace of the upload that indexed each document, kept on its row.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-27
"""
from alembic import op
import sqlalchemy as sa

from db import JSON_DOCUMENT

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {current["name"] for current in sa.inspect(op.get_bind()).get_columns("knowledge_documents")}
    if "trace" in columns:
        return
    op.add_column(
        "knowledge_documents",
        sa.Column(
            "trace", JSON_DOCUMENT, nullable = True,
            comment = "The trace of the upload that indexed the document, as a JSON list of events. "
                "Loaded only when asked for, so listing documents never reads it."
        )
    )


def downgrade() -> None:
    op.drop_column("knowledge_documents", "trace")
