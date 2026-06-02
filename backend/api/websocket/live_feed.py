import asyncio
import json
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional

from core.redis_client import get_redis
from utils.logger import get_logger

logger = get_logger(__name__)


class LiveFeedManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self._connections)}")

        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to Phantom Protocol live feed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node_id": _get_node_id(),
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self._connections)}")

    async def broadcast(self, message: dict):
        dead = []
        for conn in self._connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


_feed_manager = LiveFeedManager()


def get_feed_manager() -> LiveFeedManager:
    return _feed_manager


def _get_node_id() -> str:
    from core.config import settings
    return settings.mesh_node_id


async def live_feed_endpoint(websocket: WebSocket):
    manager = get_feed_manager()
    await manager.connect(websocket)

    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe("phantom:live_feed")

    redis_task = asyncio.create_task(_redis_listener(pubsub, websocket, manager))
    ping_task = asyncio.create_task(_ping_sender(websocket))

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                continue
    finally:
        redis_task.cancel()
        ping_task.cancel()
        await pubsub.unsubscribe("phantom:live_feed")
        manager.disconnect(websocket)


async def _redis_listener(pubsub, websocket: WebSocket, manager: LiveFeedManager):
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    event = json.loads(message["data"])
                    await websocket.send_json(event)
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket message: {e}")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Redis listener error: {e}")


async def _ping_sender(websocket: WebSocket):
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "connections": _feed_manager.connection_count,
            })
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
