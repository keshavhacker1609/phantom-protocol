from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from core.database import get_db
from models.attack import AttackEvent
from models.session import AttackerProfile
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/threats", tags=["threats"])


@router.get("/feed")
async def get_threat_feed(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    severity: str = Query(default=None),
    attack_type: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(AttackEvent).order_by(desc(AttackEvent.created_at))

    if severity:
        query = query.where(AttackEvent.severity == severity.upper())
    if attack_type:
        query = query.where(AttackEvent.attack_type == attack_type.upper())

    total_result = await db.execute(
        select(func.count(AttackEvent.id)).where(
            *(
                ([AttackEvent.severity == severity.upper()] if severity else []) +
                ([AttackEvent.attack_type == attack_type.upper()] if attack_type else [])
            )
        )
    )
    total = total_result.scalar() or 0

    result = await db.execute(query.limit(limit).offset(offset))
    events = result.scalars().all()

    attacks = []
    for e in events:
        attacks.append({
            "id": str(e.id),
            "session_id": e.session_id,
            "attack_type": e.attack_type,
            "severity": e.severity,
            "confidence": round(e.confidence, 4),
            "anonymized_input": e.anonymized_input,
            "phantom_response": (
                e.phantom_response[:120] + "..."
                if e.phantom_response and len(e.phantom_response) > 120
                else e.phantom_response
            ),
            "is_phantom_active": e.is_phantom_active == "true",
            "attacker_intent": e.attacker_intent,
            "matched_patterns": (e.metadata or {}).get("matched_patterns", []),
            "semantic_score": (e.metadata or {}).get("semantic_score", 0.0),
            "node_id": e.node_id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })

    return {"attacks": attacks, "total": total, "offset": offset, "limit": limit}


@router.get("/profiles")
async def get_attacker_profiles(
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    sophistication: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(AttackerProfile).order_by(desc(AttackerProfile.created_at))

    if sophistication:
        query = query.where(AttackerProfile.sophistication_level == sophistication.upper())

    total_result = await db.execute(select(func.count(AttackerProfile.id)))
    total = total_result.scalar() or 0

    result = await db.execute(query.limit(limit).offset(offset))
    profiles = result.scalars().all()

    formatted = []
    for p in profiles:
        formatted.append({
            "id": str(p.id),
            "profile_id": p.profile_id,
            "session_id": p.session_id,
            "primary_intent": p.primary_intent,
            "target_assets": p.target_assets or [],
            "sophistication_level": p.sophistication_level,
            "attack_methodology": p.attack_methodology,
            "attack_steps": p.attack_steps or [],
            "attack_type": p.attack_type,
            "confidence_score": round(p.confidence_score, 4),
            "was_deceived": p.was_deceived,
            "turns_in_deception": p.turns_in_deception,
            "node_id": p.node_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })

    return {"profiles": formatted, "total": total, "offset": offset, "limit": limit}


@router.get("/summary")
async def get_threat_summary(db: AsyncSession = Depends(get_db)):
    by_type = await db.execute(
        select(AttackEvent.attack_type, func.count(AttackEvent.id).label("count"))
        .group_by(AttackEvent.attack_type)
        .order_by(func.count(AttackEvent.id).desc())
    )
    by_severity = await db.execute(
        select(AttackEvent.severity, func.count(AttackEvent.id).label("count"))
        .group_by(AttackEvent.severity)
        .order_by(func.count(AttackEvent.id).desc())
    )
    top_intents = await db.execute(
        select(AttackerProfile.primary_intent, func.count(AttackerProfile.id).label("count"))
        .group_by(AttackerProfile.primary_intent)
        .order_by(func.count(AttackerProfile.id).desc())
        .limit(5)
    )

    return {
        "by_type": [{"type": r.attack_type, "count": r.count} for r in by_type],
        "by_severity": [{"severity": r.severity, "count": r.count} for r in by_severity],
        "top_intents": [{"intent": r.primary_intent, "count": r.count} for r in top_intents],
    }
