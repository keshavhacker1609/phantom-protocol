from sqlalchemy import Column, String, Float, DateTime, JSON, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import uuid

from core.database import Base


class PhantomSession(Base):
    __tablename__ = "phantom_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, COMPLETED, EXPIRED
    attack_type = Column(String(50))
    attacker_ip_hash = Column(String(64))
    conversation_turns = Column(Integer, default=0)
    deception_confidence = Column(Float, default=0.9)

    # Profiler output
    primary_intent = Column(String(200))
    target_assets = Column(JSON, default=[])
    sophistication_level = Column(String(50))
    methodology = Column(Text)

    # Conversation log (anonymized)
    conversation_log = Column(JSON, default=[])
    fake_data_served = Column(JSON, default=[])

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Mesh broadcast status
    broadcast_to_mesh = Column(Boolean, default=False)
    node_id = Column(String(50))


class AttackerProfile(Base):
    __tablename__ = "attacker_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(String(64), unique=True, nullable=False, index=True)
    session_id = Column(String(64), nullable=False)
    primary_intent = Column(String(200), nullable=False)
    target_assets = Column(JSON, default=[])
    sophistication_level = Column(String(50), nullable=False)
    attack_methodology = Column(Text)
    attack_steps = Column(JSON, default=[])
    attack_type = Column(String(50))
    confidence_score = Column(Float, default=0.8)
    was_deceived = Column(Boolean, default=True)
    turns_in_deception = Column(Integer, default=0)
    node_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PhantomSessionCreate(BaseModel):
    session_id: str
    attack_type: str
    attacker_ip_hash: Optional[str] = None
    node_id: Optional[str] = None


class PhantomSessionResponse(BaseModel):
    id: str
    session_id: str
    status: str
    attack_type: Optional[str]
    conversation_turns: int
    deception_confidence: float
    primary_intent: Optional[str]
    target_assets: List[str]
    sophistication_level: Optional[str]
    started_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


class AttackerProfileResponse(BaseModel):
    id: str
    profile_id: str
    session_id: str
    primary_intent: str
    target_assets: List[str]
    sophistication_level: str
    attack_methodology: Optional[str]
    attack_steps: List[str]
    attack_type: Optional[str]
    confidence_score: float
    was_deceived: bool
    turns_in_deception: int
    created_at: datetime

    class Config:
        from_attributes = True
