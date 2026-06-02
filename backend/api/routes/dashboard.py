from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, timedelta

from core.database import get_db
from core.redis_client import get_redis
from modules.deception.phantom_mode import get_phantom_manager
from modules.mesh.broadcaster import get_broadcaster
from models.attack import AttackEvent
from models.session import PhantomSession, AttackerProfile
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    from core.config import settings
    r = await get_redis()

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    attacks_today_result = await db.execute(
        select(func.count(AttackEvent.id))
        .where(AttackEvent.created_at >= today_start)
    )
    attacks_today = attacks_today_result.scalar() or 0

    total_attacks_result = await db.execute(select(func.count(AttackEvent.id)))
    total_attacks = total_attacks_result.scalar() or 0

    total_profiles_result = await db.execute(select(func.count(AttackerProfile.id)))
    total_profiles = total_profiles_result.scalar() or 0

    phantom_manager = get_phantom_manager()
    active_sessions = await phantom_manager.get_active_sessions()

    broadcaster = get_broadcaster()
    mesh_status = await broadcaster.get_mesh_status()

    intel_exists = await r.exists("mesh:received_intel")
    received_intel = await r.llen("mesh:received_intel") if intel_exists else 0

    broadcast_count_raw = await r.get("mesh:broadcast_count")
    broadcast_count = int(broadcast_count_raw) if broadcast_count_raw else 0

    total_phantom_result = await db.execute(
        select(func.count(AttackEvent.id))
        .where(AttackEvent.is_phantom_active == "true")
    )
    total_phantom = total_phantom_result.scalar() or 0

    deception_rate = round(total_phantom / total_attacks, 4) if total_attacks > 0 else 0.0

    by_type_result = await db.execute(
        select(AttackEvent.attack_type, func.count(AttackEvent.id).label("count"))
        .group_by(AttackEvent.attack_type)
        .order_by(func.count(AttackEvent.id).desc())
        .limit(7)
    )
    attack_breakdown = [
        {"type": row.attack_type, "count": row.count}
        for row in by_type_result
    ]

    return {
        "attacks_intercepted_today": attacks_today,
        "active_phantom_sessions": len(active_sessions),
        "mesh_nodes_connected": mesh_status.get("connected_nodes", 0),
        "preemptive_warnings_sent": broadcast_count,
        "preemptive_warnings_received": int(received_intel),
        "total_attacks_all_time": total_attacks,
        "total_attacker_profiles": total_profiles,
        "deception_success_rate": deception_rate,
        "attack_breakdown": attack_breakdown,
        "node_id": settings.mesh_node_id,
        "status": "OPERATIONAL",
    }


@router.get("/sessions")
async def get_active_sessions(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    phantom_manager = get_phantom_manager()
    live_sessions = await phantom_manager.get_active_sessions()

    result = await db.execute(
        select(PhantomSession)
        .order_by(PhantomSession.started_at.desc())
        .limit(limit)
    )
    db_sessions = result.scalars().all()

    session_map: dict[str, dict] = {}

    for s in db_sessions:
        session_map[s.session_id] = {
            "session_id": s.session_id,
            "status": s.status,
            "attack_type": s.attack_type,
            "conversation_turns": s.conversation_turns,
            "deception_confidence": s.deception_confidence,
            "primary_intent": s.primary_intent,
            "target_assets": s.target_assets or [],
            "sophistication_level": s.sophistication_level,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "last_activity": s.last_activity.isoformat() if s.last_activity else None,
        }

    for session in live_sessions:
        sid = session.get("session_id")
        if sid and sid not in session_map:
            session_map[sid] = {
                "session_id": sid,
                "status": "ACTIVE",
                "attack_type": session.get("attack_type"),
                "conversation_turns": session.get("turn_count", 0),
                "deception_confidence": session.get("deception_confidence", 0.0),
                "primary_intent": session.get("attacker_intent"),
                "target_assets": [],
                "sophistication_level": None,
                "started_at": session.get("started_at"),
                "last_activity": session.get("last_activity"),
            }

    sessions = list(session_map.values())
    sessions.sort(key=lambda s: s.get("started_at") or "", reverse=True)

    return {"sessions": sessions[:limit], "total": len(sessions)}
