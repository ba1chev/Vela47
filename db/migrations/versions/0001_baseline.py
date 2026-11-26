"""The schema as create_all built it before migrations existed: identities, resource
policies, conversations, documents and their chunks.

Revision ID: 0001
Revises:
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa

from db import UtcDateTime
from db import JSON_DOCUMENT
from db import Float32Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "identity_entities",
        sa.Column("id", sa.String(32), primary_key = True, comment = "Random hex id of the entity — the stable part of its VRN, never reused."),
        sa.Column("type", sa.String(16), nullable = False, comment = "Kind of entity: 'admin' or 'user'. Decides which model class the row is read into."),
        sa.Column("name", sa.String(32), nullable = False, unique = True, comment = "Lower-case sign-in name, unique across all entities."),
        sa.Column("password_hash", sa.String(255), nullable = False, comment = "Self-describing scrypt hash of the password, never the password itself."),
        sa.Column("created_at", UtcDateTime(), nullable = False, comment = "When the entity was created, in UTC.")
    )
    op.create_table(
        "identity_access_resource_policies",
        sa.Column("resource", sa.String(512), primary_key = True, comment = "VRN of the resource the policy is attached to."),
        sa.Column("document", JSON_DOCUMENT, nullable = False, comment = "The policy as IdentityAccessResourcePolicy.model_dump(mode='json') produces it.")
    )
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(32), primary_key = True, comment = "Random hex id of the conversation."),
        sa.Column("owner_id", sa.String(32), nullable = False, comment = "Id of the entity the conversation belongs to — a stored admin or user, or a guest."),
        sa.Column("title", sa.String(200), nullable = False, comment = "Human-readable title shown in the list of conversations."),
        sa.Column("messages", JSON_DOCUMENT, nullable = False, comment = "The ordered turns, each as model_dump(mode='json') of its message, without artifacts."),
        sa.Column("created_at", UtcDateTime(), nullable = False, comment = "When the conversation was started, in UTC."),
        sa.Column("updated_at", UtcDateTime(), nullable = False, comment = "When a message was last appended, in UTC. Orders the list of conversations.")
    )
    op.create_index("ix_chat_sessions_owner_id_updated_at", "chat_sessions", ["owner_id", "updated_at"])
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(32), primary_key = True, comment = "Random hex id of the document."),
        sa.Column("owner_id", sa.String(32), nullable = False, comment = "Id of the entity the document belongs to — a stored admin or user, or a guest."),
        sa.Column("title", sa.String(200), nullable = False, comment = "Name the document is shown and cited under, normally its file name."),
        sa.Column("size_bytes", sa.Integer(), nullable = False, comment = "Size of the uploaded text in UTF-8 bytes. Summed per owner to enforce the storage limit."),
        sa.Column("chunk_count", sa.Integer(), nullable = False, comment = "How many chunks the document was cut into."),
        sa.Column("created_at", UtcDateTime(), nullable = False, comment = "When the document was uploaded, in UTC.")
    )
    op.create_index("ix_knowledge_documents_owner_id", "knowledge_documents", ["owner_id"])
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(48), primary_key = True, comment = "'<document id>-<position>' — the id the RAG agent cites the passage by."),
        sa.Column(
            "document_id", sa.String(32), sa.ForeignKey("knowledge_documents.id", ondelete = "CASCADE"),
            nullable = False, comment = "The document this chunk was cut from."
        ),
        sa.Column("owner_id", sa.String(32), nullable = False, comment = "Owner of the document, repeated so one owner's chunks load without a join."),
        sa.Column("chunk_index", sa.Integer(), nullable = False, comment = "Position of the chunk within its document, from 0."),
        sa.Column("content", sa.Text(), nullable = False, comment = "The passage, verbatim as it appears in the document."),
        sa.Column("vector", Float32Vector(), nullable = False, comment = "Embedding of the passage as packed float32 values."),
        sa.Column("span_start", sa.Integer(), nullable = True, comment = "Offset in the document's text where the passage begins, if it is a verbatim slice."),
        sa.Column("span_end", sa.Integer(), nullable = True, comment = "Offset in the document's text just past the passage's last character."),
        sa.Column("section", sa.Text(), nullable = True, comment = "Headings above the passage, outermost first, joined by ' › '."),
        sa.Column("topic", sa.String(100), nullable = True, comment = "The topic register's topic closest to the passage's embedding."),
        sa.Column("topic_score", sa.Float(), nullable = True, comment = "Cosine similarity between the passage's embedding and its topic."),
        sa.Column("keywords", JSON_DOCUMENT, nullable = False, comment = "Words that set the passage apart from the rest of its document, as a JSON list.")
    )
    op.create_index("ix_knowledge_chunks_owner_id", "knowledge_chunks", ["owner_id"])


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("chat_sessions")
    op.drop_table("identity_access_resource_policies")
    op.drop_table("identity_entities")
