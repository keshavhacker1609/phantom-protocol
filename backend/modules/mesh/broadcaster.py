import asyncio
import json
import websockets
from datetime import datetime, timezone

from modules.mesh.anonymizer import get_anonymizer
from core.config import settings
from core.redis_client import get_redis, publish_event, increment
from utils.crypto import generate_threat_id
from utils.logger import get_logger

logger = get_logger(__name__)

MESH_INTEL_CHANNEL = "mesh:threat_intel"
MESH_PEERS_KEY = "mesh:connected_peers"


class MeshBroadcaster:
    def __init__(self):
        self.anonymizer = get_anonymizer()
        self.node_id = settings.mesh_node_id

    async def broadcast_threat(
        self,
        attack_type: str,
        methodology_fingerprint: str,
        intent: dict,
        methodology: dict,
        session_id: str,
    ) -> str:
        threat_id = generate_threat_id()

        shareable = self.anonymizer.extract_shareable_intel(
            session_data={
                "attack_type": attack_type,
                "intent": intent,
                "methodology": methodology,
            },
            fingerprint=methodology_fingerprint,
        )

        payload = {
            "threat_id": threat_id,
            "source_node": self._hash_node(self.node_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **shareable,
        }

        anonymized_payload = self.anonymizer.anonymize_payload(payload, self.node_id)

        await publish_event(MESH_INTEL_CHANNEL, json.dumps(anonymized_payload))
        await increment("mesh:broadcast_count")

        await publish_event(
            "phantom:live_feed",
            json.dumps({
                "type": "mesh_broadcast",
                "threat_id": threat_id,
                "attack_type": attack_type,
                "nodes_warned": await self._get_peer_count(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        )

        if not settings.demo_mode:
            asyncio.create_task(self._broadcast_to_external(anonymized_payload))

        logger.info(f"Threat {threat_id} broadcast to mesh (attack: {attack_type})")
        return threat_id

    async def _broadcast_to_external(self, payload: dict):
        try:
            async with websockets.connect(settings.mesh_network_url, open_timeout=5) as ws:
                await ws.send(json.dumps({
                    "type": "threat_intel",
                    "node_id": self._hash_node(self.node_id),
                    "payload": payload,
                }))
                logger.info(f"Threat broadcast to external mesh node")
        except Exception as e:
            logger.warning(f"External mesh broadcast failed: {e}")

    async def get_mesh_status(self) -> dict:
        r = await get_redis()

        peers_raw = await r.get(MESH_PEERS_KEY)
        peers = []
        if peers_raw:
            try:
                peers = json.loads(peers_raw)
            except Exception:
                peers = []

        intel_count_raw = await r.llen("mesh:received_intel") if await r.exists("mesh:received_intel") else 0
        broadcast_count_raw = await r.get("mesh:broadcast_count")

        return {
            "node_id": self.node_id,
            "status": "CONNECTED",
            "connected_nodes": len(peers),
            "total_nodes": len(peers) + 1,
            "intel_shared": int(broadcast_count_raw) if broadcast_count_raw else 0,
            "intel_received": int(intel_count_raw),
            "demo_mode": settings.demo_mode,
        }

    async def _get_peer_count(self) -> int:
        r = await get_redis()
        peers_raw = await r.get(MESH_PEERS_KEY)
        if not peers_raw:
            return 0
        try:
            return len(json.loads(peers_raw))
        except Exception:
            return 0

    def _hash_node(self, node_id: str) -> str:
        import hashlib
        return hashlib.sha256(node_id.encode()).hexdigest()[:12]


_broadcaster_instance: MeshBroadcaster | None = None


def get_broadcaster() -> MeshBroadcaster:
    global _broadcaster_instance
    if _broadcaster_instance is None:
        _broadcaster_instance = MeshBroadcaster()
    return _broadcaster_instance
