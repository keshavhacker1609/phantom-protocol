import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from utils.logger import get_logger

logger = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"
NODE_ID_HEADER = "X-Node-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, node_id: str = ""):
        super().__init__(app)
        self.node_id = node_id

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[NODE_ID_HEADER] = self.node_id
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"

        if not request.url.path.startswith("/ws"):
            logger.info(
                f"{request.method} {request.url.path} "
                f"→ {response.status_code} ({elapsed_ms}ms) "
                f"[{request_id[:8]}]"
            )

        return response
