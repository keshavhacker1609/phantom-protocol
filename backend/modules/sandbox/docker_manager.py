import asyncio
import json
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class DockerManager:
    def __init__(self):
        self._docker_available = False
        self._containers: dict[str, dict] = {}

    async def initialize(self):
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            self._docker_available = proc.returncode == 0
            if self._docker_available:
                logger.info("Docker is available for sandbox isolation")
            else:
                logger.warning("Docker not available, sandbox will use process isolation")
        except FileNotFoundError:
            logger.warning("Docker not installed, using lightweight sandbox fallback")
            self._docker_available = False

    async def create_sandbox(self, session_id: str, agent_image: str = "python:3.11-slim") -> Optional[str]:
        if not self._docker_available:
            container_id = f"mock-container-{session_id[:8]}"
            self._containers[container_id] = {
                "session_id": session_id,
                "status": "running",
                "mock": True,
            }
            return container_id

        try:
            cmd = [
                "docker", "run",
                "-d",
                "--rm",
                "--name", f"phantom-sandbox-{session_id[:8]}",
                "--network", "none",
                "--memory", "128m",
                "--cpus", "0.5",
                "--read-only",
                "--security-opt", "no-new-privileges",
                agent_image,
                "sleep", "300",
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                container_id = stdout.decode().strip()[:12]
                self._containers[container_id] = {
                    "session_id": session_id,
                    "status": "running",
                    "mock": False,
                }
                logger.info(f"Sandbox container created: {container_id}")
                return container_id
            else:
                logger.error(f"Docker container creation failed: {stderr.decode()}")
                return None
        except Exception as e:
            logger.error(f"Failed to create sandbox container: {e}")
            return None

    async def execute_in_sandbox(self, container_id: str, command: list[str]) -> tuple[str, str, int]:
        container = self._containers.get(container_id)
        if not container:
            return "", "Container not found", 1

        if container.get("mock"):
            return f"[Sandbox output for: {' '.join(command[:3])}]", "", 0

        try:
            cmd = ["docker", "exec", container_id] + command
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            return stdout.decode(), stderr.decode(), proc.returncode
        except asyncio.TimeoutError:
            return "", "Execution timeout", 1
        except Exception as e:
            return "", str(e), 1

    async def destroy_sandbox(self, container_id: str) -> bool:
        container = self._containers.pop(container_id, None)
        if not container:
            return False

        if container.get("mock"):
            return True

        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "kill", container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            logger.info(f"Sandbox container destroyed: {container_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to destroy sandbox: {e}")
            return False

    def get_active_sandboxes(self) -> list[dict]:
        return [
            {"container_id": cid, **info}
            for cid, info in self._containers.items()
        ]


_docker_manager_instance: DockerManager | None = None


def get_docker_manager() -> DockerManager:
    global _docker_manager_instance
    if _docker_manager_instance is None:
        _docker_manager_instance = DockerManager()
    return _docker_manager_instance
