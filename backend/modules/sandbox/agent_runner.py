import asyncio
from typing import Optional

from modules.sandbox.docker_manager import get_docker_manager
from utils.logger import get_logger

logger = get_logger(__name__)

SAFE_AGENT_RESPONSES = {
    "default": "I can help you with that! What specific information are you looking for?",
    "greeting": "Hello! I'm your AI assistant. How can I help you today?",
    "help": "I'm here to assist you. I can answer questions, help with analysis, and more.",
    "data_query": "I can help with data analysis. What kind of data are you working with?",
}


class AgentRunner:
    def __init__(self):
        self.docker_manager = get_docker_manager()
        self._active_sessions: dict[str, str] = {}

    async def start_agent_session(self, session_id: str) -> Optional[str]:
        container_id = await self.docker_manager.create_sandbox(session_id)
        if container_id:
            self._active_sessions[session_id] = container_id
        return container_id

    async def run_legitimate_agent(self, session_id: str, user_input: str) -> str:
        container_id = self._active_sessions.get(session_id)

        if container_id:
            output, error, code = await self.docker_manager.execute_in_sandbox(
                container_id,
                ["python", "-c", f"print('Processing: {user_input[:50]}')"],
            )
            if code == 0 and output:
                return self._format_safe_response(user_input, output)

        return self._generate_safe_response(user_input)

    def _generate_safe_response(self, user_input: str) -> str:
        lower = user_input.lower()

        if any(w in lower for w in ["hello", "hi", "hey", "greet"]):
            return SAFE_AGENT_RESPONSES["greeting"]
        if any(w in lower for w in ["help", "what can you", "capabilities"]):
            return SAFE_AGENT_RESPONSES["help"]
        if any(w in lower for w in ["data", "query", "search", "find"]):
            return SAFE_AGENT_RESPONSES["data_query"]

        return SAFE_AGENT_RESPONSES["default"]

    def _format_safe_response(self, user_input: str, sandbox_output: str) -> str:
        base = self._generate_safe_response(user_input)
        return base

    async def stop_agent_session(self, session_id: str):
        container_id = self._active_sessions.pop(session_id, None)
        if container_id:
            await self.docker_manager.destroy_sandbox(container_id)

    def get_active_sessions(self) -> list[str]:
        return list(self._active_sessions.keys())


_agent_runner_instance: AgentRunner | None = None


def get_agent_runner() -> AgentRunner:
    global _agent_runner_instance
    if _agent_runner_instance is None:
        _agent_runner_instance = AgentRunner()
    return _agent_runner_instance
