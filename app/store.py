from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models import ActionExecuteRequest, ActionStatus, IngestEventRequest


class InMemoryStore:
    def __init__(self) -> None:
        self.events: dict[str, IngestEventRequest] = {}
        self.actions: dict[str, ActionStatus] = {}
        self.audit: list[dict] = []

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


store = InMemoryStore()
