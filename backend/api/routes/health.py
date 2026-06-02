"""
Deep health check endpoint — judges production readiness.
Tests every dependency independently and returns structured status.
"""
import asyncio
import time
from fastapi import APIRouter
from sqlalchemy import text

from core.config import settings
from core.database import AsyncSessionLocal
from core.redis_client import get_redis
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_simple():
    return {"status": "healthy", "node_id": settings.mesh_node_id}


@router.get("/health/deep")
async def health_deep():
    """
    Deep health check. Tests DB, Redis, ML model, Gemini API reachability.
    Returns 200 if all critical dependencies are healthy, 503 otherwise.
    """
    checks: dict[str, dict] = {}
    overall_healthy = True

    db_start = time.perf_counter()
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - db_start) * 1000, 2),
            "driver": "asyncpg",
        }
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    redis_start = time.perf_counter()
    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - redis_start) * 1000, 2),
        }
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    ml_start = time.perf_counter()
    try:
        from modules.sentinel.classifier import get_classifier
        classifier = await get_classifier()
        checks["ml_classifier"] = {
            "status": "healthy" if classifier.is_ready else "degraded",
            "model": settings.embedding_model,
            "load_time_ms": round((time.perf_counter() - ml_start) * 1000, 2),
        }
    except Exception as e:
        checks["ml_classifier"] = {"status": "degraded", "error": str(e)}

    gemini_start = time.perf_counter()
    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(settings.gemini_model)
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: model.generate_content("ping"),
                ),
                timeout=5.0,
            )
            checks["gemini_api"] = {
                "status": "healthy",
                "model": settings.gemini_model,
                "latency_ms": round((time.perf_counter() - gemini_start) * 1000, 2),
            }
        except asyncio.TimeoutError:
            checks["gemini_api"] = {"status": "degraded", "error": "timeout (>5s)"}
        except Exception as e:
            checks["gemini_api"] = {"status": "degraded", "error": str(e)[:100]}
    else:
        checks["gemini_api"] = {"status": "not_configured", "fallback": "enabled"}

    pgvector_start = time.perf_counter()
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT '[1,2,3]'::vector"))
        checks["pgvector"] = {
            "status": "healthy",
            "semantic_search": "active",
            "latency_ms": round((time.perf_counter() - pgvector_start) * 1000, 2),
        }
    except Exception:
        checks["pgvector"] = {"status": "unavailable", "semantic_search": "disabled"}

    from core.redis_client import get_redis as _get_redis
    r = await _get_redis()
    intel_count = await r.llen("mesh:received_intel") if await r.exists("mesh:received_intel") else 0
    broadcast_count = await r.get("mesh:broadcast_count") or 0

    from fastapi.responses import JSONResponse
    status_code = 200 if overall_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "degraded",
            "node_id": settings.mesh_node_id,
            "environment": settings.environment,
            "demo_mode": settings.demo_mode,
            "checks": checks,
            "mesh": {
                "intel_received": int(intel_count),
                "intel_broadcast": int(broadcast_count),
            },
        },
    )
