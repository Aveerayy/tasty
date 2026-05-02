from __future__ import annotations

from datetime import datetime, timezone
from datetime import timedelta
from uuid import uuid4

from app.models import (
    ActionExecuteRequest,
    ActionStatus,
    ApprovalToken,
    IngestEventRequest,
    IntelligenceSystem,
)


class InMemoryStore:
    def __init__(self) -> None:
        self.events: dict[str, IngestEventRequest] = {}
        self.actions: dict[str, ActionStatus] = {}
        self.approvals: dict[str, ApprovalToken] = {}
        self.audit: list[dict] = []
        self.intelligence_systems: list[IntelligenceSystem] = [
            IntelligenceSystem(
                systemId="sys-security-vuln-db",
                name="Security Vulnerability Catalog",
                domain="security",
                freshnessMinutes=5,
                qualityScore=0.94,
                lineageCoverage=0.91,
                readOnly=True,
            ),
            IntelligenceSystem(
                systemId="sys-finance-transactions",
                name="Finance Risk Signals",
                domain="finance",
                freshnessMinutes=2,
                qualityScore=0.92,
                lineageCoverage=0.89,
                readOnly=True,
            ),
            IntelligenceSystem(
                systemId="sys-healthcare-record-quality",
                name="Clinical Data Quality Graph",
                domain="healthcare",
                freshnessMinutes=15,
                qualityScore=0.9,
                lineageCoverage=0.93,
                readOnly=True,
            ),
        ]

    def ingest_event(self, event: IngestEventRequest) -> str:
        event_id = str(uuid4())
        self.events[event_id] = event
        self.audit.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "kind": "event_ingested",
                "event_id": event_id,
                "event_type": event.eventType,
                "domain": event.domain,
            }
        )
        return event_id

    def get_event(self, event_id: str) -> IngestEventRequest | None:
        return self.events.get(event_id)

    def create_action(self, request: ActionExecuteRequest, state: str, details: dict) -> ActionStatus:
        now = datetime.now(timezone.utc)
        action_id = str(uuid4())
        status = ActionStatus(
            actionId=action_id,
            state=state,  # type: ignore[arg-type]
            createdAt=now,
            updatedAt=now,
            auditRef=f"audit-{action_id}",
            details=details,
        )
        self.actions[action_id] = status
        self.audit.append(
            {
                "timestamp": now.isoformat(),
                "kind": "action_created",
                "action_id": action_id,
                "action_type": request.actionType,
                "initiated_by": request.initiatedBy,
                "state": state,
                "dry_run": request.dryRun,
            }
        )
        return status

    def update_action_state(self, action_id: str, state: str, details: dict | None = None) -> ActionStatus | None:
        status = self.actions.get(action_id)
        if not status:
            return None
        status.state = state  # type: ignore[assignment]
        status.updatedAt = datetime.now(timezone.utc)
        if details:
            status.details.update(details)
        self.audit.append(
            {
                "timestamp": status.updatedAt.isoformat(),
                "kind": "action_state_changed",
                "action_id": action_id,
                "state": state,
            }
        )
        return status

    def get_action(self, action_id: str) -> ActionStatus | None:
        return self.actions.get(action_id)

    def create_approval(self, actor: str, approved_by: str = "playground-approver") -> ApprovalToken:
        now = datetime.now(timezone.utc)
        approval_id = f"apr_{uuid4().hex[:12]}"
        token = ApprovalToken(
            approvalId=approval_id,
            approved=True,
            approvedBy=approved_by,
            createdAt=now,
            expiresAt=now + timedelta(hours=1),
        )
        self.approvals[approval_id] = token
        self.audit.append(
            {
                "timestamp": now.isoformat(),
                "kind": "approval_issued",
                "approval_id": approval_id,
                "actor": actor,
                "approved_by": approved_by,
            }
        )
        return token

    def get_approval(self, approval_id: str) -> ApprovalToken | None:
        token = self.approvals.get(approval_id)
        if not token:
            return None
        if token.expiresAt < datetime.now(timezone.utc):
            return None
        return token

    def list_systems(self, domain: str | None = None) -> list[IntelligenceSystem]:
        if domain:
            return [s for s in self.intelligence_systems if s.domain == domain]
        return list(self.intelligence_systems)

    def reset(self) -> None:
        self.events.clear()
        self.actions.clear()
        self.approvals.clear()
        self.audit.clear()


store = InMemoryStore()
