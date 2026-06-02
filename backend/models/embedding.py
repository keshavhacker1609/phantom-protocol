from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import text
import uuid

from core.database import Base


class AttackEmbedding(Base):
    """Stores attack text embeddings in pgvector for semantic similarity search."""
    __tablename__ = "attack_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), nullable=False, index=True)
    attack_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    text_hash = Column(String(32), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # NOTE: vector column added via raw SQL in init_db() because pgvector
    # availability is optional — the system degrades gracefully without it.


EMBEDDING_DDL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='attack_embeddings' AND column_name='embedding'
    ) THEN
        ALTER TABLE attack_embeddings ADD COLUMN embedding vector(384);
        CREATE INDEX IF NOT EXISTS attack_embeddings_embedding_idx
            ON attack_embeddings USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 50);
    END IF;
END$$;
"""
