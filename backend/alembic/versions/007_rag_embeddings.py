"""pgvector table for hybrid RAG embeddings (Task 41.2).

Revision ID: 007_rag_embeddings
Revises: 006_test_by_type
Create Date: 2026-06-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_rag_embeddings"
down_revision: Union[str, Sequence[str], None] = "006_test_by_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.execute(
        sa.text(
            """
            CREATE TABLE rag_embeddings (
                id SERIAL PRIMARY KEY,
                doc_id VARCHAR(255) NOT NULL UNIQUE,
                source VARCHAR(32) NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                embedding vector(1536) NOT NULL
            )
            """
        )
    )
    op.create_index("ix_rag_embeddings_source", "rag_embeddings", ["source"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_index("ix_rag_embeddings_source", table_name="rag_embeddings")
    op.drop_table("rag_embeddings")
