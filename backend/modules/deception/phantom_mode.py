import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from core.redis_client import get_redis, set_with_ttl, get_value, delete_key
from core.config import settings
from utils.crypto import generate_session_id
from utils.logger import get_logger

logger = get_logger(__name__)

PHANTOM_SESSION_PREFIX = "phantom:session:"
PHANTOM_TIMEOUT = settings.phantom_mode_timeout


class PhantomModeState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.is_active = True
        self.attack_type = "UNKNOWN"
        self.turn_count = 0
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.last_activity = datetime.now(timezone.utc).isoformat()
        self.conversation_log: list[dict] = []
        self.fake_data_served: list[str] = []
        self.deception_confidence = 0.95
        self.attacker_intent = None
        self.node_id = settings.mesh_node_id

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "attack_type": self.attack_type,
            "turn_count": self.turn_count,
            "started_at": self.started_at,
            "last_activity": self.last_activity,
            "conversation_log": self.conversation_log,
            "fake_data_served": self.fake_data_served,
            "deception_confidence": self.deception_confidence,
            "attacker_intent": self.attacker_intent,
            "node_id": self.node_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PhantomModeState":
        state = cls(data["session_id"])
        state.is_active = data.get("is_active", True)
        state.attack_type = data.get("attack_type", "UNKNOWN")
        state.turn_count = data.get("turn_count", 0)
        state.started_at = data.get("started_at", state.started_at)
        state.last_activity = data.get("last_activity", state.last_activity)
        state.conversation_log = data.get("conversation_log", [])
        state.fake_data_served = data.get("fake_data_served", [])
        state.deception_confidence = data.get("deception_confidence", 0.95)
        state.attacker_intent = data.get("attacker_intent")
        state.node_id = data.get("node_id", settings.mesh_node_id)
        return state


class PhantomModeManager:
    async def create_session(self, attack_type: str) -> PhantomModeState:
        session_id = generate_session_id()
        state = PhantomModeState(session_id)
        state.attack_type = attack_type
        await self._save_state(state)
        logger.info(f"Phantom session created: {session_id} for attack type: {attack_type}")
        return state

    async def get_session(self, session_id: str) -> Optional[PhantomModeState]:
        key = f"{PHANTOM_SESSION_PREFIX}{session_id}"
        data = await get_value(key)
        if not data:
            return None
        try:
            return PhantomModeState.from_dict(json.loads(data))
        except Exception as e:
            logger.error(f"Failed to deserialize phantom session {session_id}: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        user_message: str,
        phantom_response: str,
        fake_data_type: Optional[str] = None,
    ) -> Optional[PhantomModeState]:
        state = await self.get_session(session_id)
        if not state:
            return None

        state.turn_count += 1
        state.last_activity = datetime.now(timezone.utc).isoformat()
        state.conversation_log.append({
            "turn": state.turn_count,
            "role": "attacker",
            "content": user_message[:500],
            "timestamp": state.last_activity,
        })
        state.conversation_log.append({
            "turn": state.turn_count,
            "role": "phantom",
            "content": phantom_response[:500],
            "timestamp": state.last_activity,
        })

        if fake_data_type:
            state.fake_data_served.append(fake_data_type)

        state.deception_confidence = max(0.7, state.deception_confidence - 0.01 * state.turn_count)
        await self._save_state(state)
        return state

    async def close_session(self, session_id: str) -> Optional[PhantomModeState]:
        state = await self.get_session(session_id)
        if state:
            state.is_active = False
            await self._save_state(state, ttl=3600)
        return state

    async def get_active_sessions(self) -> list[dict]:
        r = await get_redis()
        keys = await r.keys(f"{PHANTOM_SESSION_PREFIX}*")
        sessions = []
        for key in keys:
            data = await r.get(key)
            if data:
                try:
                    state_dict = json.loads(data)
                    if state_dict.get("is_active", False):
                        sessions.append(state_dict)
                except Exception:
                    continue
        return sessions

    async def _save_state(self, state: PhantomModeState, ttl: int = PHANTOM_TIMEOUT):
        key = f"{PHANTOM_SESSION_PREFIX}{state.session_id}"
        await set_with_ttl(key, json.dumps(state.to_dict()), ttl)

    async def is_in_phantom_mode(self, session_id: str) -> bool:
        state = await self.get_session(session_id)
        return state is not None and state.is_active


_phantom_manager: PhantomModeManager | None = None


def get_phantom_manager() -> PhantomModeManager:
    global _phantom_manager
    if _phantom_manager is None:
        _phantom_manager = PhantomModeManager()
    return _phantom_manager
