from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


Domain = Literal["security", "finance", "healthcare"]
ActionState = Literal["pending", "approved", "executing", "completed", "failed", "rolled_back"]
PlaygroundMode = Literal["today", "reverse"]


class IngestEventRequest(BaseModel):
    eventType: str
    domain: Domain
    timestamp: datetime
    lineageRef: Optional[str] = None
    payload: dict[str, Any]


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


class ActionExecuteRequest(BaseModel):
    actionType: str
    target: dict[str, Any]
    initiatedBy: str
    approvalId: Optional[str] = None
    dryRun: bool = True


class ActionStatus(BaseModel):
    actionId: str
    state: ActionState
    createdAt: datetime
    updatedAt: datetime
    auditRef: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


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
