from fastapi import APIRouter
from datetime import datetime, timezone

from modules.mesh.broadcaster import get_broadcaster
from modules.mesh.receiver import get_receiver
from core.redis_client import get_redis
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/mesh", tags=["mesh"])


@router.get("/status")
async def get_mesh_status():
    broadcaster = get_broadcaster()
    status = await broadcaster.get_mesh_status()
    return status


@router.get("/intel")
async def get_received_intel(limit: int = 20):
    receiver = get_receiver()
    intel = await receiver.get_received_intel(limit=limit)

    formatted = []
    for item in intel:
        formatted.append({
            "threat_id": item.get("threat_id", ""),
            "source_node": item.get("source_node", ""),
            "attack_type": item.get("attack_type", ""),
            "target_asset_type": item.get("target_asset_type", ""),
            "sophistication_level": item.get("sophistication_level", ""),
            "affected_nodes": item.get("affected_nodes", 1),
            "confidence": item.get("confidence", 0.0),
            "pre_emptive_signatures": item.get("pre_emptive_signatures", []),
            "behavioral_indicators": item.get("behavioral_indicators", []),
            "timestamp": item.get("timestamp", ""),
            "pre_warned_minutes_ago": item.get("pre_warned_minutes_ago", 0),
        })

    return {"intel": formatted, "total": len(formatted)}


@router.get("/nodes")
async def get_connected_nodes():
    from core.config import settings
    r = await get_redis()

    peers_raw = await r.get("mesh:connected_peers")
    peers = []
    if peers_raw:
        import json
        try:
            peers = json.loads(peers_raw)
        except Exception:
            peers = []

    self_node = {
        "id": settings.mesh_node_id,
        "location": "LOCAL",
        "status": "ACTIVE",
        "attacks_shared": int(await r.get("mesh:broadcast_count") or 0),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "is_self": True,
    }

    all_nodes = [self_node] + [p for p in peers if p.get("id") != settings.mesh_node_id]
    active_count = sum(1 for n in all_nodes if n.get("status") == "ACTIVE")

    return {
        "nodes": all_nodes,
        "total": len(all_nodes),
        "active": active_count,
    }
