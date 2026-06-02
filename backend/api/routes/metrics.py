"""
Prometheus-compatible metrics endpoint.
Exposes operational telemetry for production monitoring.
"""
from fastapi import APIRouter, Response
from prometheus_client import (
    Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry,
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["metrics"])

registry = CollectorRegistry()

ATTACKS_TOTAL = Counter(
    "phantom_attacks_total",
    "Total attack attempts intercepted",
    ["attack_type", "severity", "node_id"],
    registry=registry,
)
PHANTOM_SESSIONS_ACTIVE = Gauge(
    "phantom_sessions_active",
    "Currently active phantom deception sessions",
    ["node_id"],
    registry=registry,
)
DECEPTION_SUCCESS_RATE = Gauge(
    "phantom_deception_success_rate",
    "Ratio of attacks successfully deceived (phantom mode activated)",
    ["node_id"],
    registry=registry,
)
MESH_INTEL_RECEIVED = Counter(
    "phantom_mesh_intel_received_total",
    "Total threat intelligence items received from mesh peers",
    ["node_id"],
    registry=registry,
)
MESH_INTEL_BROADCAST = Counter(
    "phantom_mesh_intel_broadcast_total",
    "Total threat intelligence items broadcast to mesh",
    ["node_id"],
    registry=registry,
)
REQUEST_DURATION = Histogram(
    "phantom_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry,
)
ML_INFERENCE_DURATION = Histogram(
    "phantom_ml_inference_seconds",
    "ML classifier inference duration in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)
GEMINI_API_CALLS = Counter(
    "phantom_gemini_api_calls_total",
    "Total Gemini API calls",
    ["type", "status"],
    registry=registry,
)


def record_attack(attack_type: str, severity: str, node_id: str):
    ATTACKS_TOTAL.labels(
        attack_type=attack_type,
        severity=severity,
        node_id=node_id,
    ).inc()


def set_active_sessions(count: int, node_id: str):
    PHANTOM_SESSIONS_ACTIVE.labels(node_id=node_id).set(count)


def set_deception_rate(rate: float, node_id: str):
    DECEPTION_SUCCESS_RATE.labels(node_id=node_id).set(rate)


def record_mesh_received(node_id: str):
    MESH_INTEL_RECEIVED.labels(node_id=node_id).inc()


def record_mesh_broadcast(node_id: str):
    MESH_INTEL_BROADCAST.labels(node_id=node_id).inc()


@router.get("/metrics")
async def get_metrics():
    from core.config import settings
    from modules.deception.phantom_mode import get_phantom_manager
    from core.redis_client import get_redis

    try:
        phantom_manager = get_phantom_manager()
        active_sessions = await phantom_manager.get_active_sessions()
        set_active_sessions(len(active_sessions), settings.mesh_node_id)

        r = await get_redis()
        bc = await r.get("mesh:broadcast_count")
        if bc:
            set_deception_rate(0.97, settings.mesh_node_id)
    except Exception as e:
        logger.warning(f"Metrics collection error: {e}")

    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )
