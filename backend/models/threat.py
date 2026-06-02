from sqlalchemy import Column, String, Float, DateTime, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import uuid

from core.database import Base


class ThreatIntelligence(Base):
    __tablename__ = "threat_intelligence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    threat_id = Column(String(64), unique=True, nullable=False, index=True)
    source_node_id = Column(String(50), nullable=False)
    attack_type = Column(String(50), nullable=False)
    methodology_fingerprint = Column(String(64), nullable=False)
    target_asset_type = Column(String(100))
    sophistication_level = Column(String(50))
    pre_emptive_signatures = Column(JSON, default=[])
    behavioral_indicators = Column(JSON, default=[])
    affected_nodes = Column(Integer, default=1)
    confidence = Column(Float, default=0.8)
    is_active = Column(String(10), default="true")
    raw_intel = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))


class ThreatIntelCreate(BaseModel):
    threat_id: str
    source_node_id: str
    attack_type: str
    methodology_fingerprint: str
    target_asset_type: Optional[str] = None
    sophistication_level: Optional[str] = None
    pre_emptive_signatures: List[str] = Field(default_factory=list)
    behavioral_indicators: List[str] = Field(default_factory=list)
    affected_nodes: int = 1
    confidence: float = 0.8
    raw_intel: dict = Field(default_factory=dict)


class ThreatIntelResponse(BaseModel):
    id: str
    threat_id: str
    source_node_id: str
    attack_type: str
    methodology_fingerprint: str
    target_asset_type: Optional[str]
    sophistication_level: Optional[str]
    pre_emptive_signatures: List[str]
    behavioral_indicators: List[str]
    affected_nodes: int
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class MeshBroadcastPayload(BaseModel):
    threat_id: str
    source_node: str
    attack_type: str
    methodology_fingerprint: str
    target_asset_type: str
    sophistication_level: str
    pre_emptive_signatures: List[str]
    behavioral_indicators: List[str]
    confidence: float
    timestamp: str
