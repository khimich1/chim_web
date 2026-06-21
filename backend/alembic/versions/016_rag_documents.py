"""Keyword RAG document metadata in PostgreSQL (Task 96, Phase 17c).

Revision ID: 016_rag_documents
Revises: 015_tutor_user_profile
Create Date: 2026-06-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_rag_documents"
down_revision: Union[str, Sequence[str], None] = "015_tutor_user_profile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(
        sa.text(
            """
            CREATE TABLE rag_documents (
                id SERIAL PRIMARY KEY,
                doc_id VARCHAR(255) NOT NULL UNIQUE,
                source VARCHAR(32) NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb
            )
            """
        )
    )
    op.create_index("ix_rag_documents_source", "rag_documents", ["source"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_index("ix_rag_documents_source", table_name="rag_documents")
    op.drop_table("rag_documents")
