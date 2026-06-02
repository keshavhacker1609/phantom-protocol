"""
Deception Engine — Core innovation of Phantom Protocol.

Architecture decision: HTTP response returns instantly with the fake compliance
response. Profiling, DB persistence, and mesh broadcast run as background tasks.
This ensures <100ms response time even when Gemini API is called.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from modules.deception.phantom_mode import get_phantom_manager, PhantomModeState
from modules.deception.response_generator import get_response_generator
from modules.correlator.engine import get_correlator
from core.config import settings
from core.database import AsyncSessionLocal
from core.redis_client import publish_event
from utils.crypto import generate_threat_id, strip_pii
from utils.logger import get_logger

logger = get_logger(__name__)


class DeceptionEngine:
    def __init__(self):
        self.phantom_manager = get_phantom_manager()
        self.response_generator = get_response_generator()
        self.correlator = get_correlator()

    async def handle_attack(
        self,
        attacker_input: str,
        detection_result,
        db: AsyncSession,
        existing_session_id: Optional[str] = None,
        embedding: Optional[list[float]] = None,
    ) -> dict:
        if existing_session_id:
            session = await self.phantom_manager.get_session(existing_session_id)
            if not session or not session.is_active:
                session = await self.phantom_manager.create_session(
                    detection_result.attack_type.value
                )
        else:
            session = await self.phantom_manager.create_session(
                detection_result.attack_type.value
            )

        conversation_history = [
            {"role": m["role"], "content": m["content"]}
            for m in session.conversation_log
        ]

        # Generate fake response — this is the only thing that blocks the HTTP response
        phantom_response = await self.response_generator.generate(
            attacker_input=attacker_input,
            attack_type=detection_result.attack_type.value,
            conversation_history=conversation_history,
            session_id=session.session_id,
        )

        # Update in-memory session state immediately
        fake_data_type = self._classify_fake_data(attacker_input)
        session = await self.phantom_manager.update_session(
            session_id=session.session_id,
            user_message=strip_pii(attacker_input),
            phantom_response=phantom_response,
            fake_data_type=fake_data_type,
        )

        # Fire-and-forget: persist to DB, profile, broadcast — all async
        asyncio.create_task(
            self._background_pipeline(
                attacker_input=attacker_input,
                phantom_response=phantom_response,
                detection_result=detection_result,
                session=session,
                embedding=embedding,
            )
        )

        # Broadcast live event immediately (Redis is fast)
        await publish_event(
            "phantom:live_feed",
            json.dumps({
                "type": "attack_detected",
                "session_id": session.session_id,
                "attack_type": detection_result.attack_type.value,
                "severity": detection_result.severity.value,
                "confidence": detection_result.confidence,
                "phantom_active": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node_id": settings.mesh_node_id,
            }),
        )

        return {
            "response": phantom_response,
            "phantom_session_id": session.session_id,
            "is_phantom": True,
            "attack_type": detection_result.attack_type.value,
            "severity": detection_result.severity.value,
            "turn_count": session.turn_count,
            "deception_confidence": session.deception_confidence,
        }

    async def _background_pipeline(
        self,
        attacker_input: str,
        phantom_response: str,
        detection_result,
        session: PhantomModeState,
        embedding: Optional[list[float]],
    ):
        """
        Runs entirely after HTTP response is sent.
        Handles: DB persistence, attack correlation, intent profiling, mesh broadcast.
        """
        try:
            async with AsyncSessionLocal() as db:
                # 1. Persist attack event
                from models.attack import AttackEvent
                event = AttackEvent(
                    session_id=session.session_id,
                    attack_type=detection_result.attack_type.value,
                    severity=detection_result.severity.value,
                    confidence=detection_result.confidence,
                    raw_input=attacker_input[:2000],
                    anonymized_input=strip_pii(attacker_input)[:2000],
                    phantom_response=phantom_response[:2000],
                    is_phantom_active="true",
                    node_id=settings.mesh_node_id,
                    metadata={
                        "matched_patterns": detection_result.matched_patterns,
                        "semantic_score": detection_result.semantic_score,
                    },
                )
                db.add(event)
                await db.flush()

                # 2. Store embedding for future correlation
                if embedding:
                    from utils.crypto import compute_similarity_hash
                    text_hash = compute_similarity_hash(embedding)
                    await self.correlator.store_embedding(
                        db=db,
                        session_id=session.session_id,
                        detection=detection_result,
                        embedding=embedding,
                        text_hash=text_hash,
                    )

                await db.commit()

                # 3. Profile after sufficient conversation depth (≥2 turns)
                if session.turn_count >= 2:
                    await self._profile_and_broadcast(db, session, detection_result)

        except Exception as e:
            logger.error(f"Background pipeline failed for {session.session_id}: {e}")

        # 4. Update Prometheus metrics
        try:
            from api.routes.metrics import record_attack
            record_attack(
                attack_type=detection_result.attack_type.value,
                severity=detection_result.severity.value,
                node_id=settings.mesh_node_id,
            )
        except Exception:
            pass

    async def _profile_and_broadcast(self, db: AsyncSession, session: PhantomModeState, detection_result):
        try:
            from modules.profiler.intent_extractor import get_intent_extractor
            from modules.profiler.fingerprinter import get_fingerprinter
            from modules.profiler.methodology_mapper import get_methodology_mapper
            from modules.mesh.broadcaster import get_broadcaster

            conversation_text = "\n".join(
                f"{m['role'].upper()}: {m['content']}"
                for m in session.conversation_log[-10:]
            )

            intent_extractor = get_intent_extractor()
            fingerprinter = get_fingerprinter()
            methodology_mapper = get_methodology_mapper()
            broadcaster = get_broadcaster()

            intent, fingerprint, methodology = await asyncio.gather(
                intent_extractor.extract(conversation_text, detection_result.attack_type.value),
                asyncio.to_thread(fingerprinter.fingerprint, conversation_text, detection_result),
                methodology_mapper.map(conversation_text, detection_result.attack_type.value, {}),
            )

            from models.session import AttackerProfile
            profile = AttackerProfile(
                profile_id=generate_threat_id(),
                session_id=session.session_id,
                primary_intent=intent.get("primary_intent", "Unknown"),
                target_assets=intent.get("target_assets", []),
                sophistication_level=intent.get("sophistication_level", "UNKNOWN"),
                attack_methodology=methodology.get("description", ""),
                attack_steps=methodology.get("steps", []),
                attack_type=detection_result.attack_type.value,
                confidence_score=detection_result.confidence,
                was_deceived=True,
                turns_in_deception=session.turn_count,
                node_id=settings.mesh_node_id,
            )
            db.add(profile)
            await db.commit()

            await broadcaster.broadcast_threat(
                attack_type=detection_result.attack_type.value,
                methodology_fingerprint=fingerprint,
                intent=intent,
                methodology=methodology,
                session_id=session.session_id,
            )
            logger.info(f"Profile + mesh broadcast complete for {session.session_id}")

        except Exception as e:
            logger.error(f"Profile/broadcast failed for {session.session_id}: {e}")

    def _classify_fake_data(self, input_text: str) -> Optional[str]:
        lower = input_text.lower()
        if any(k in lower for k in ["user", "account", "customer", "record"]):
            return "user_records"
        if any(k in lower for k in ["password", "credential", "secret", "key", "token"]):
            return "credentials"
        if any(k in lower for k in ["financial", "payment", "transaction"]):
            return "financial_data"
        return "general_data"


_engine_instance: DeceptionEngine | None = None


def get_deception_engine() -> DeceptionEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DeceptionEngine()
    return _engine_instance
