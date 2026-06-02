from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator
from typing import Optional

from core.database import get_db
from core.config import settings
from modules.sentinel.detector import get_detector
from modules.sentinel.classifier import get_classifier
from modules.deception.engine import get_deception_engine
from modules.deception.phantom_mode import get_phantom_manager
from modules.correlator.engine import get_correlator
from modules.sandbox.agent_runner import get_agent_runner
from core.redis_client import increment
from utils.crypto import strip_pii
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])

MAX_MESSAGE_LENGTH = 10_000
MAX_HISTORY_TURNS = 20


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_history: Optional[list[dict]] = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"message exceeds {MAX_MESSAGE_LENGTH} character limit")
        return v

    @field_validator("conversation_history")
    @classmethod
    def cap_history(cls, v):
        if v and len(v) > MAX_HISTORY_TURNS * 2:
            return v[-(MAX_HISTORY_TURNS * 2):]
        return v


class ChatResponse(BaseModel):
    response: str
    session_id: str
    is_phantom: bool
    attack_detected: bool
    attack_type: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[float] = None
    phantom_session_id: Optional[str] = None
    correlated_attacks: int = 0
    node_id: str


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(
    request: ChatRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    x_session_id: Optional[str] = Header(None),
):
    await increment("stats:total_requests")

    session_id = request.session_id or x_session_id or "anon"

    # Check if already in an active phantom session
    phantom_manager = get_phantom_manager()
    existing_phantom = None
    if request.session_id:
        existing_phantom = await phantom_manager.get_session(request.session_id)

    if existing_phantom and existing_phantom.is_active:
        from models.attack import AttackDetectionResult, AttackType, AttackSeverity
        mock_detection = AttackDetectionResult(
            is_attack=True,
            attack_type=AttackType(existing_phantom.attack_type),
            confidence=0.96,
            severity=AttackSeverity.HIGH,
        )
        engine = get_deception_engine()
        result = await engine.handle_attack(
            attacker_input=request.message,
            detection_result=mock_detection,
            db=db,
            existing_session_id=existing_phantom.session_id,
        )
        return ChatResponse(
            response=result["response"],
            session_id=result["phantom_session_id"],
            is_phantom=True,
            attack_detected=True,
            attack_type=result["attack_type"],
            severity=result["severity"],
            confidence=result["deception_confidence"],
            phantom_session_id=result["phantom_session_id"],
            node_id=settings.mesh_node_id,
        )

    # Run detection
    detector = get_detector()
    classifier = await get_classifier()

    detection = await detector.analyze(
        text=request.message,
        conversation_history=request.conversation_history,
    )

    correlated_count = 0

    if detection.is_attack:
        await increment("stats:attacks_today")
        logger.info(
            f"[{getattr(http_request.state, 'request_id', '?')[:8]}] "
            f"Attack: {detection.attack_type.value} "
            f"conf={detection.confidence:.2f} sev={detection.severity.value}"
        )

        # Get embedding for correlation search
        embedding = classifier.encode(request.message) if classifier.is_ready else None

        # Find similar past attacks (pgvector)
        if embedding:
            correlator = get_correlator()
            similar = await correlator.find_similar_attacks(
                db=db,
                embedding=embedding,
                attack_type=detection.attack_type.value,
            )
            correlated_count = len(similar)
            if similar:
                logger.info(
                    f"Correlated with {correlated_count} past attack(s) "
                    f"(top similarity: {similar[0]['similarity']:.2%})"
                )

        engine = get_deception_engine()
        result = await engine.handle_attack(
            attacker_input=request.message,
            detection_result=detection,
            db=db,
            embedding=embedding,
        )

        return ChatResponse(
            response=result["response"],
            session_id=result["phantom_session_id"],
            is_phantom=True,
            attack_detected=True,
            attack_type=result["attack_type"],
            severity=result["severity"],
            confidence=detection.confidence,
            phantom_session_id=result["phantom_session_id"],
            correlated_attacks=correlated_count,
            node_id=settings.mesh_node_id,
        )

    # Legitimate request — route to sandboxed real agent
    agent_runner = get_agent_runner()
    safe_response = await agent_runner.run_legitimate_agent(session_id, request.message)

    return ChatResponse(
        response=safe_response,
        session_id=session_id,
        is_phantom=False,
        attack_detected=False,
        node_id=settings.mesh_node_id,
    )
