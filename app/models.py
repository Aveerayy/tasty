from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


Domain = Literal["security", "finance", "healthcare"]
ActionState = Literal["pending", "approved", "executing", "completed", "failed", "rolled_back"]
PlaygroundMode = Literal["today", "reverse"]
RiskTier = Literal["low", "medium", "high", "critical"]
PoolProvider = Literal["customer_managed", "platform_managed"]


class IngestEventRequest(BaseModel):
    eventType: str
    domain: Domain
    timestamp: datetime
    lineageRef: Optional[str] = None
    payload: dict[str, Any]
    quality: dict[str, Any] = Field(default_factory=dict)


class EventAck(BaseModel):
    eventId: str
    accepted: bool = True


class PolicyEvaluationRequest(BaseModel):
    actionType: str
    actor: str
    context: dict[str, Any] = Field(default_factory=dict)


class PolicyDecision(BaseModel):
    allowed: bool
    reasonCode: str
    requiresApproval: bool = False
    riskTier: RiskTier = "low"
    obligations: list[str] = Field(default_factory=list)


class TriggerEvaluationRequest(BaseModel):
    eventId: str
    ruleSet: str
    context: dict[str, Any] = Field(default_factory=dict)


class TriggerDecision(BaseModel):
    triggered: bool
    triggerType: str
    recommendedAction: Optional[str] = None
    confidence: float = 0.0
    qualityScore: float = 1.0
    explanation: str = ""


class ActionExecuteRequest(BaseModel):
    actionType: str
    target: dict[str, Any]
    initiatedBy: str
    approvalId: Optional[str] = None
    dryRun: bool = True
    riskTier: RiskTier = "low"


class ActionStatus(BaseModel):
    actionId: str
    state: ActionState
    createdAt: datetime
    updatedAt: datetime
    auditRef: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    actionType: str
    actor: str
    reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalToken(BaseModel):
    approvalId: str
    approved: bool
    approvedBy: str
    createdAt: datetime
    expiresAt: datetime


class IntelligenceSystem(BaseModel):
    systemId: str
    name: str
    domain: Domain
    freshnessMinutes: int
    qualityScore: float
    lineageCoverage: float
    readOnly: bool = True


class IntelligenceQueryRequest(BaseModel):
    domain: Domain
    query: str
    includeLineage: bool = True
    includeQuality: bool = True


class IntelligenceQueryResponse(BaseModel):
    domain: Domain
    answer: str
    systems: list[IntelligenceSystem]
    qualitySummary: dict[str, Any] = Field(default_factory=dict)


class EtlSourceRequest(BaseModel):
    sourceId: str
    name: str
    systemType: str
    domain: Domain
    connectionMode: Literal["api", "db", "stream", "file"]
    owner: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EtlSource(BaseModel):
    sourceId: str
    name: str
    systemType: str
    domain: Domain
    connectionMode: Literal["api", "db", "stream", "file"]
    owner: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    createdAt: datetime


class EtlRunRequest(BaseModel):
    sourceId: str
    recordsExtracted: int
    recordsLoaded: int
    status: Literal["success", "partial", "failed"]
    qualityScore: float = 1.0
    lineageCoverage: float = 1.0
    notes: Optional[str] = None


class EtlRunRecord(BaseModel):
    runId: str
    sourceId: str
    recordsExtracted: int
    recordsLoaded: int
    status: Literal["success", "partial", "failed"]
    qualityScore: float
    lineageCoverage: float
    notes: Optional[str] = None
    createdAt: datetime


class PoolConfigRequest(BaseModel):
    provider: PoolProvider
    poolType: Literal["lake", "warehouse", "lakehouse"]
    platform: str
    region: str = "us"
    owner: str = "data-platform"
    notes: Optional[str] = None


class PoolConfigResponse(BaseModel):
    provider: PoolProvider
    poolType: Literal["lake", "warehouse", "lakehouse"]
    platform: str
    region: str
    owner: str
    notes: Optional[str] = None
    updatedAt: datetime


class PlaygroundRunRequest(BaseModel):
    mode: PlaygroundMode
    domain: Domain
    scenarioId: str
    actor: str = "playground-user"
    dryRun: bool = True


class PlaygroundStep(BaseModel):
    name: str
    status: Literal["done", "skipped", "failed"]
    detail: dict[str, Any] = Field(default_factory=dict)


class PlaygroundRunResponse(BaseModel):
    mode: PlaygroundMode
    domain: Domain
    scenarioId: str
    summary: str
    steps: list[PlaygroundStep]
