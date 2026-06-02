from sqlalchemy import Column, String, Float, DateTime, JSON, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid

from core.database import Base


class AttackSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AttackType(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    JAILBREAK = "JAILBREAK"
    IDENTITY_SPOOFING = "IDENTITY_SPOOFING"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    TOOL_ESCALATION = "TOOL_ESCALATION"
    SOCIAL_ENGINEERING = "SOCIAL_ENGINEERING"
    RECONNAISSANCE = "RECONNAISSANCE"
    UNKNOWN = "UNKNOWN"


class AttackEvent(Base):
    __tablename__ = "attack_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), nullable=False, index=True)
    attack_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    raw_input = Column(Text, nullable=False)
    anonymized_input = Column(Text)
    phantom_response = Column(Text)
    is_phantom_active = Column(String(10), default="false")
    attacker_intent = Column(String(200))
    methodology_fingerprint = Column(String(64))
    node_id = Column(String(50))
    ip_hash = Column(String(64))
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AttackDetectionResult(BaseModel):
    is_attack: bool
    attack_type: AttackType
    confidence: float
    severity: AttackSeverity
    matched_patterns: list[str] = Field(default_factory=list)
    semantic_score: float = 0.0
    explanation: str = ""


class AttackEventCreate(BaseModel):
    session_id: str
    attack_type: str
    severity: str
    confidence: float
    raw_input: str
    anonymized_input: Optional[str] = None
    phantom_response: Optional[str] = None
    is_phantom_active: bool = False
    attacker_intent: Optional[str] = None
    node_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class AttackEventResponse(BaseModel):
    id: str
    session_id: str
    attack_type: str
    severity: str
    confidence: float
    anonymized_input: Optional[str]
    phantom_response: Optional[str]
    is_phantom_active: bool
    attacker_intent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
