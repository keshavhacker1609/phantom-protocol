"""
Attack Correlation Engine
Finds semantically similar past attacks using pgvector cosine similarity.
Enables pre-emptive profiling and pattern recognition across sessions.
"""
from __future__ import annotations

import hashlib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from models.embedding import AttackEmbedding
from models.attack import AttackDetectionResult
from utils.logger import get_logger

logger = get_logger(__name__)

SIMILARITY_THRESHOLD = 0.82
MAX_CORRELATIONS = 5


class AttackCorrelator:
    def __init__(self):
        self._pgvector_available = False

    async def store_embedding(
        self,
        db: AsyncSession,
        session_id: str,
        detection: AttackDetectionResult,
        embedding: list[float],
        text_hash: str,
    ) -> bool:
        try:
            record = AttackEmbedding(
                session_id=session_id,
                attack_type=detection.attack_type.value,
                severity=detection.severity.value,
                text_hash=text_hash,
            )
            db.add(record)
            await db.flush()

            if self._pgvector_available:
                vec_str = "[" + ",".join(f"{v:.6f}" for v in embedding) + "]"
                await db.execute(
                    text(
                        "UPDATE attack_embeddings SET embedding = :vec::vector "
                        "WHERE id = :id"
                    ),
                    {"vec": vec_str, "id": str(record.id)},
                )
            return True
        except Exception as e:
            logger.warning(f"Failed to store attack embedding: {e}")
            return False

    async def find_similar_attacks(
        self,
        db: AsyncSession,
        embedding: list[float],
        attack_type: str,
        limit: int = MAX_CORRELATIONS,
    ) -> list[dict]:
        if not self._pgvector_available:
            return []

        try:
            vec_str = "[" + ",".join(f"{v:.6f}" for v in embedding) + "]"
            result = await db.execute(
                text("""
                    SELECT session_id, attack_type, severity,
                           1 - (embedding <=> :vec::vector) AS similarity,
                           created_at
                    FROM attack_embeddings
                    WHERE embedding IS NOT NULL
                      AND attack_type = :atype
                    ORDER BY embedding <=> :vec::vector
                    LIMIT :limit
                """),
                {"vec": vec_str, "atype": attack_type, "limit": limit},
            )
            rows = result.fetchall()
            correlations = []
            for row in rows:
                sim = float(row.similarity)
                if sim >= SIMILARITY_THRESHOLD:
                    correlations.append({
                        "session_id": row.session_id,
                        "attack_type": row.attack_type,
                        "severity": row.severity,
                        "similarity": round(sim, 4),
                        "seen_at": row.created_at.isoformat() if row.created_at else None,
                    })
            return correlations
        except Exception as e:
            logger.warning(f"Similarity search failed: {e}")
            return []

    async def check_pgvector(self, db: AsyncSession) -> bool:
        try:
            await db.execute(text("SELECT '[1,2,3]'::vector"))
            self._pgvector_available = True
            logger.info("pgvector: available — semantic correlation ACTIVE")
        except Exception:
            self._pgvector_available = False
            logger.info("pgvector: not available — semantic correlation disabled")
        return self._pgvector_available

    @property
    def is_available(self) -> bool:
        return self._pgvector_available


_correlator_instance: AttackCorrelator | None = None


def get_correlator() -> AttackCorrelator:
    global _correlator_instance
    if _correlator_instance is None:
        _correlator_instance = AttackCorrelator()
    return _correlator_instance
