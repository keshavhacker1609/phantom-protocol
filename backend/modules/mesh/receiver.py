import asyncio
import json
import websockets
from datetime import datetime, timezone

from core.config import settings
from core.redis_client import get_redis, publish_event
from utils.logger import get_logger

logger = get_logger(__name__)

MESH_INTEL_CHANNEL = "mesh:threat_intel"
RECEIVED_INTEL_KEY = "mesh:received_intel"
MAX_STORED_INTEL = 100


class MeshReceiver:
    def __init__(self):
        self.node_id = settings.mesh_node_id
        self._running = False
        self._pre_loaded_signatures: set[str] = set()

    async def start_listening(self):
        self._running = True
        asyncio.create_task(self._redis_listener())
        if not settings.demo_mode:
            asyncio.create_task(self._external_mesh_listener())
        logger.info(f"Mesh receiver started (demo_mode={settings.demo_mode})")

    async def stop(self):
        self._running = False

    async def _redis_listener(self):
        r = await get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe(MESH_INTEL_CHANNEL)
        logger.info(f"Subscribed to Redis channel: {MESH_INTEL_CHANNEL}")
        try:
            async for message in pubsub.listen():
                if not self._running:
                    break
                if message["type"] == "message":
                    try:
                        await self._process_intel(json.loads(message["data"]))
                    except Exception as e:
                        logger.warning(f"Failed to process mesh intel: {e}")
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(MESH_INTEL_CHANNEL)

    async def _external_mesh_listener(self):
        while self._running:
            try:
                async with websockets.connect(
                    settings.mesh_network_url,
                    open_timeout=10,
                    ping_interval=30,
                ) as ws:
                    await ws.send(json.dumps({
                        "type": "register",
                        "node_id": self.node_id,
                    }))
                    logger.info(f"Connected to external mesh: {settings.mesh_network_url}")
                    async for message in ws:
                        if not self._running:
                            break
                        try:
                            data = json.loads(message)
                            if data.get("type") == "threat_intel":
                                await self._process_intel(data.get("payload", {}))
                        except Exception as e:
                            logger.warning(f"Failed to handle mesh message: {e}")
            except Exception as e:
                logger.warning(f"External mesh connection failed: {e}. Retrying in 30s...")
                await asyncio.sleep(30)

    async def _process_intel(self, intel: dict):
        if not intel:
            return

        r = await get_redis()
        await r.lpush(RECEIVED_INTEL_KEY, json.dumps(intel))
        await r.ltrim(RECEIVED_INTEL_KEY, 0, MAX_STORED_INTEL - 1)
        await r.expire(RECEIVED_INTEL_KEY, 86400)

        new_sigs = [
            s for s in intel.get("pre_emptive_signatures", [])
            if s not in self._pre_loaded_signatures
        ]
        if new_sigs:
            self._pre_loaded_signatures.update(new_sigs)
            logger.info(f"Pre-loaded {len(new_sigs)} attack signatures from mesh peer")

        await publish_event(
            "phantom:live_feed",
            json.dumps({
                "type": "mesh_intel_received",
                "threat_id": intel.get("threat_id", ""),
                "attack_type": intel.get("attack_type", ""),
                "sophistication": intel.get("sophistication_level", ""),
                "affected_nodes": intel.get("affected_nodes", 1),
                "pre_warned_minutes_ago": intel.get("pre_warned_minutes_ago", 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        )

    async def get_received_intel(self, limit: int = 20) -> list[dict]:
        r = await get_redis()
        raw_items = await r.lrange(RECEIVED_INTEL_KEY, 0, limit - 1)
        result = []
        for item in raw_items:
            try:
                result.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        return result

    def is_pre_warned(self, attack_signature: str) -> bool:
        return attack_signature in self._pre_loaded_signatures

    def get_pre_loaded_signature_count(self) -> int:
        return len(self._pre_loaded_signatures)


_receiver_instance: MeshReceiver | None = None


def get_receiver() -> MeshReceiver:
    global _receiver_instance
    if _receiver_instance is None:
        _receiver_instance = MeshReceiver()
    return _receiver_instance
