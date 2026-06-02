from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from core.config import settings
from core.database import init_db, close_db, engine
from core.redis_client import close_redis
from middleware.request_id import RequestIDMiddleware
from middleware.error_handler import (
    global_exception_handler,
    validation_error_handler,
)
from modules.sentinel.classifier import get_classifier
from modules.sandbox.docker_manager import get_docker_manager
from modules.mesh.receiver import get_receiver
from modules.correlator.engine import get_correlator
from api.routes import agent, dashboard, threats, mesh
from api.routes.health import router as health_router
from api.routes.metrics import router as metrics_router
from api.websocket.live_feed import live_feed_endpoint
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Phantom Protocol v{settings.app_version}")
    logger.info(f"Node ID: {settings.mesh_node_id}")
    logger.info(f"Environment: {settings.environment}")

    # Database schema
    await init_db()
    await _init_pgvector_schema()

    # ML classifier (warm up in background — don't block startup)
    import asyncio
    asyncio.create_task(_warm_up_classifier())

    # Docker sandbox
    docker_manager = get_docker_manager()
    await docker_manager.initialize()

    # Mesh receiver
    receiver = get_receiver()
    await receiver.start_listening()

    logger.info("Phantom Protocol OPERATIONAL")
    yield

    logger.info("Shutting down...")
    await receiver.stop()
    await close_db()
    await close_redis()


async def _warm_up_classifier():
    from sqlalchemy import text
    try:
        classifier = await get_classifier()
        if classifier.is_ready:
            logger.info("Sentinel ML classifier ready")

        async with engine.connect() as conn:
            from sqlalchemy.ext.asyncio import AsyncSession
            from core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                correlator = get_correlator()
                await correlator.check_pgvector(db)
    except Exception as e:
        logger.warning(f"Warm-up partial failure: {e}")


async def _init_pgvector_schema():
    from sqlalchemy import text
    from models.embedding import EMBEDDING_DDL
    try:
        async with engine.begin() as conn:
            await conn.execute(text(EMBEDDING_DDL))
    except Exception as e:
        logger.warning(f"pgvector schema init skipped: {e}")


app = FastAPI(
    title="Phantom Protocol",
    description="AI Agent Honeypot & Deception Defense Network",
    version=settings.app_version,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)

# Middleware (order matters — outermost first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware, node_id=settings.mesh_node_id)

# Exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

# Routers
app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(agent.router)
app.include_router(dashboard.router)
app.include_router(threats.router)
app.include_router(mesh.router)


@app.websocket("/ws/live-feed")
async def websocket_endpoint(websocket: WebSocket):
    await live_feed_endpoint(websocket)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "Phantom Protocol",
        "version": settings.app_version,
        "tagline": "Every attacker thinks they succeeded. None of them did.",
        "status": "OPERATIONAL",
        "node_id": settings.mesh_node_id,
        "docs": "/docs",
        "health": "/health/deep",
        "metrics": "/metrics",
    }
