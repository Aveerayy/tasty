from __future__ import annotations

import os
from datetime import datetime, timezone
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, MetaData, String, Table, create_engine, delete, insert, select, update
from sqlalchemy.engine import Engine

from app.models import (
    ActionExecuteRequest,
    ActionStatus,
    ApprovalToken,
    PoolConfigRequest,
    PoolConfigResponse,
    IngestEventRequest,
    IntelligenceSystem,
    EtlSource,
    EtlSourceRequest,
    EtlRunRecord,
    EtlRunRequest,
)


class InMemoryStore:
    def __init__(self) -> None:
        self.events: dict[str, IngestEventRequest] = {}
        self.actions: dict[str, ActionStatus] = {}
        self.approvals: dict[str, ApprovalToken] = {}
        self.audit: list[dict] = []
        self.etl_sources: dict[str, EtlSource] = {}
        self.etl_runs: list[EtlRunRecord] = []
        self.pool_config = PoolConfigResponse(
            provider="customer_managed",
            poolType="warehouse",
            platform="snowflake",
            region="us",
            owner="data-platform",
            notes="default BYO pool",
            updatedAt=datetime.now(timezone.utc),
        )
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

    def register_source(self, request: EtlSourceRequest) -> EtlSource:
        source = EtlSource(
            sourceId=request.sourceId,
            name=request.name,
            systemType=request.systemType,
            domain=request.domain,
            connectionMode=request.connectionMode,
            owner=request.owner,
            metadata=request.metadata,
            createdAt=datetime.now(timezone.utc),
        )
        self.etl_sources[source.sourceId] = source
        self.audit.append(
            {
                "timestamp": source.createdAt.isoformat(),
                "kind": "etl_source_registered",
                "source_id": source.sourceId,
                "domain": source.domain,
            }
        )
        return source

    def list_sources(self, domain: str | None = None) -> list[EtlSource]:
        values = list(self.etl_sources.values())
        if domain:
            values = [s for s in values if s.domain == domain]
        return values

    def record_etl_run(self, request: EtlRunRequest) -> EtlRunRecord:
        run = EtlRunRecord(
            runId=f"run_{uuid4().hex[:12]}",
            sourceId=request.sourceId,
            recordsExtracted=request.recordsExtracted,
            recordsLoaded=request.recordsLoaded,
            status=request.status,
            qualityScore=request.qualityScore,
            lineageCoverage=request.lineageCoverage,
            notes=request.notes,
            createdAt=datetime.now(timezone.utc),
        )
        self.etl_runs.append(run)
        self.audit.append(
            {
                "timestamp": run.createdAt.isoformat(),
                "kind": "etl_run_recorded",
                "run_id": run.runId,
                "source_id": run.sourceId,
                "status": run.status,
            }
        )
        self._apply_run_to_intelligence(run)
        return run

    def list_etl_runs(self, source_id: str | None = None) -> list[EtlRunRecord]:
        if source_id:
            return [r for r in self.etl_runs if r.sourceId == source_id]
        return list(self.etl_runs)

    def set_pool_config(self, request: PoolConfigRequest) -> PoolConfigResponse:
        self.pool_config = PoolConfigResponse(
            provider=request.provider,
            poolType=request.poolType,
            platform=request.platform,
            region=request.region,
            owner=request.owner,
            notes=request.notes,
            updatedAt=datetime.now(timezone.utc),
        )
        return self.pool_config

    def get_pool_config(self) -> PoolConfigResponse:
        return self.pool_config

    def _apply_run_to_intelligence(self, run: EtlRunRecord) -> None:
        source = self.etl_sources.get(run.sourceId)
        if not source:
            return
        for system in self.intelligence_systems:
            if system.domain != source.domain:
                continue
            system.qualityScore = round((system.qualityScore * 0.7) + (run.qualityScore * 0.3), 3)
            system.lineageCoverage = round((system.lineageCoverage * 0.7) + (run.lineageCoverage * 0.3), 3)
            system.freshnessMinutes = 1 if run.status == "success" else min(system.freshnessMinutes + 5, 120)

    def reset(self) -> None:
        self.events.clear()
        self.actions.clear()
        self.approvals.clear()
        self.etl_sources.clear()
        self.etl_runs.clear()
        self.audit.clear()


class PostgresStore:
    def __init__(self, database_url: str) -> None:
        self.engine: Engine = create_engine(database_url, future=True)
        self.metadata = MetaData()

        self.events = Table(
            "events",
            self.metadata,
            Column("event_id", String, primary_key=True),
            Column("event_type", String, nullable=False),
            Column("domain", String, nullable=False),
            Column("timestamp", DateTime(timezone=True), nullable=False),
            Column("lineage_ref", String, nullable=True),
            Column("payload", JSON, nullable=False),
            Column("quality", JSON, nullable=False),
        )
        self.actions = Table(
            "actions",
            self.metadata,
            Column("action_id", String, primary_key=True),
            Column("state", String, nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("updated_at", DateTime(timezone=True), nullable=False),
            Column("audit_ref", String, nullable=True),
            Column("details", JSON, nullable=False),
            Column("action_type", String, nullable=False),
            Column("initiated_by", String, nullable=False),
            Column("dry_run", Boolean, nullable=False),
        )
        self.approvals = Table(
            "approvals",
            self.metadata,
            Column("approval_id", String, primary_key=True),
            Column("approved", Boolean, nullable=False),
            Column("approved_by", String, nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("expires_at", DateTime(timezone=True), nullable=False),
            Column("actor", String, nullable=False),
        )
        self.intelligence_systems = Table(
            "intelligence_systems",
            self.metadata,
            Column("system_id", String, primary_key=True),
            Column("name", String, nullable=False),
            Column("domain", String, nullable=False),
            Column("freshness_minutes", Integer, nullable=False),
            Column("quality_score", Float, nullable=False),
            Column("lineage_coverage", Float, nullable=False),
            Column("read_only", Boolean, nullable=False),
        )
        self.etl_sources = Table(
            "etl_sources",
            self.metadata,
            Column("source_id", String, primary_key=True),
            Column("name", String, nullable=False),
            Column("system_type", String, nullable=False),
            Column("domain", String, nullable=False),
            Column("connection_mode", String, nullable=False),
            Column("owner", String, nullable=False),
            Column("metadata_json", JSON, nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        self.etl_runs = Table(
            "etl_runs",
            self.metadata,
            Column("run_id", String, primary_key=True),
            Column("source_id", String, nullable=False),
            Column("records_extracted", Integer, nullable=False),
            Column("records_loaded", Integer, nullable=False),
            Column("status", String, nullable=False),
            Column("quality_score", Float, nullable=False),
            Column("lineage_coverage", Float, nullable=False),
            Column("notes", String, nullable=True),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        self.platform_settings = Table(
            "platform_settings",
            self.metadata,
            Column("key", String, primary_key=True),
            Column("value", JSON, nullable=False),
            Column("updated_at", DateTime(timezone=True), nullable=False),
        )
        self.audit = Table(
            "audit_log",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("timestamp", DateTime(timezone=True), nullable=False),
            Column("kind", String, nullable=False),
            Column("payload", JSON, nullable=False),
        )

        self.metadata.create_all(self.engine)
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        with self.engine.begin() as conn:
            count = conn.execute(select(self.intelligence_systems.c.system_id)).first()
            if not count:
                conn.execute(
                    insert(self.intelligence_systems),
                    [
                        {
                            "system_id": "sys-security-vuln-db",
                            "name": "Security Vulnerability Catalog",
                            "domain": "security",
                            "freshness_minutes": 5,
                            "quality_score": 0.94,
                            "lineage_coverage": 0.91,
                            "read_only": True,
                        },
                        {
                            "system_id": "sys-finance-transactions",
                            "name": "Finance Risk Signals",
                            "domain": "finance",
                            "freshness_minutes": 2,
                            "quality_score": 0.92,
                            "lineage_coverage": 0.89,
                            "read_only": True,
                        },
                        {
                            "system_id": "sys-healthcare-record-quality",
                            "name": "Clinical Data Quality Graph",
                            "domain": "healthcare",
                            "freshness_minutes": 15,
                            "quality_score": 0.9,
                            "lineage_coverage": 0.93,
                            "read_only": True,
                        },
                    ],
                )
            setting = conn.execute(
                select(self.platform_settings.c.key).where(self.platform_settings.c.key == "pool_config")
            ).first()
            if not setting:
                conn.execute(
                    insert(self.platform_settings),
                    {
                        "key": "pool_config",
                        "value": {
                            "provider": "customer_managed",
                            "poolType": "warehouse",
                            "platform": "snowflake",
                            "region": "us",
                            "owner": "data-platform",
                            "notes": "default BYO pool",
                        },
                        "updated_at": datetime.now(timezone.utc),
                    },
                )

    def _audit(self, kind: str, payload: dict) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.audit),
                {"timestamp": datetime.now(timezone.utc), "kind": kind, "payload": payload},
            )

    def ingest_event(self, event: IngestEventRequest) -> str:
        event_id = str(uuid4())
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.events),
                {
                    "event_id": event_id,
                    "event_type": event.eventType,
                    "domain": event.domain,
                    "timestamp": event.timestamp,
                    "lineage_ref": event.lineageRef,
                    "payload": event.payload,
                    "quality": event.quality,
                },
            )
        self._audit("event_ingested", {"event_id": event_id, "event_type": event.eventType, "domain": event.domain})
        return event_id

    def get_event(self, event_id: str) -> IngestEventRequest | None:
        with self.engine.begin() as conn:
            row = conn.execute(select(self.events).where(self.events.c.event_id == event_id)).mappings().first()
        if not row:
            return None
        return IngestEventRequest(
            eventType=row["event_type"],
            domain=row["domain"],
            timestamp=row["timestamp"],
            lineageRef=row["lineage_ref"],
            payload=row["payload"] or {},
            quality=row["quality"] or {},
        )

    def create_action(self, request: ActionExecuteRequest, state: str, details: dict) -> ActionStatus:
        now = datetime.now(timezone.utc)
        action_id = str(uuid4())
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.actions),
                {
                    "action_id": action_id,
                    "state": state,
                    "created_at": now,
                    "updated_at": now,
                    "audit_ref": f"audit-{action_id}",
                    "details": details,
                    "action_type": request.actionType,
                    "initiated_by": request.initiatedBy,
                    "dry_run": request.dryRun,
                },
            )
        self._audit("action_created", {"action_id": action_id, "state": state})
        return ActionStatus(
            actionId=action_id,
            state=state,  # type: ignore[arg-type]
            createdAt=now,
            updatedAt=now,
            auditRef=f"audit-{action_id}",
            details=details,
        )

    def update_action_state(self, action_id: str, state: str, details: dict | None = None) -> ActionStatus | None:
        with self.engine.begin() as conn:
            row = conn.execute(select(self.actions).where(self.actions.c.action_id == action_id)).mappings().first()
            if not row:
                return None
            merged = dict(row["details"] or {})
            if details:
                merged.update(details)
            now = datetime.now(timezone.utc)
            conn.execute(
                update(self.actions)
                .where(self.actions.c.action_id == action_id)
                .values(state=state, updated_at=now, details=merged),
            )
        self._audit("action_state_changed", {"action_id": action_id, "state": state})
        return ActionStatus(
            actionId=action_id,
            state=state,  # type: ignore[arg-type]
            createdAt=row["created_at"],
            updatedAt=now,
            auditRef=row["audit_ref"],
            details=merged,
        )

    def get_action(self, action_id: str) -> ActionStatus | None:
        with self.engine.begin() as conn:
            row = conn.execute(select(self.actions).where(self.actions.c.action_id == action_id)).mappings().first()
        if not row:
            return None
        return ActionStatus(
            actionId=row["action_id"],
            state=row["state"],  # type: ignore[arg-type]
            createdAt=row["created_at"],
            updatedAt=row["updated_at"],
            auditRef=row["audit_ref"],
            details=row["details"] or {},
        )

    def create_approval(self, actor: str, approved_by: str = "playground-approver") -> ApprovalToken:
        now = datetime.now(timezone.utc)
        token = ApprovalToken(
            approvalId=f"apr_{uuid4().hex[:12]}",
            approved=True,
            approvedBy=approved_by,
            createdAt=now,
            expiresAt=now + timedelta(hours=1),
        )
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.approvals),
                {
                    "approval_id": token.approvalId,
                    "approved": token.approved,
                    "approved_by": token.approvedBy,
                    "created_at": token.createdAt,
                    "expires_at": token.expiresAt,
                    "actor": actor,
                },
            )
        self._audit("approval_issued", {"approval_id": token.approvalId, "actor": actor})
        return token

    def get_approval(self, approval_id: str) -> ApprovalToken | None:
        with self.engine.begin() as conn:
            row = conn.execute(select(self.approvals).where(self.approvals.c.approval_id == approval_id)).mappings().first()
        if not row:
            return None
        if row["expires_at"] < datetime.now(timezone.utc):
            return None
        return ApprovalToken(
            approvalId=row["approval_id"],
            approved=row["approved"],
            approvedBy=row["approved_by"],
            createdAt=row["created_at"],
            expiresAt=row["expires_at"],
        )

    def list_systems(self, domain: str | None = None) -> list[IntelligenceSystem]:
        query = select(self.intelligence_systems)
        if domain:
            query = query.where(self.intelligence_systems.c.domain == domain)
        with self.engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [
            IntelligenceSystem(
                systemId=r["system_id"],
                name=r["name"],
                domain=r["domain"],
                freshnessMinutes=r["freshness_minutes"],
                qualityScore=r["quality_score"],
                lineageCoverage=r["lineage_coverage"],
                readOnly=r["read_only"],
            )
            for r in rows
        ]

    def register_source(self, request: EtlSourceRequest) -> EtlSource:
        source = EtlSource(
            sourceId=request.sourceId,
            name=request.name,
            systemType=request.systemType,
            domain=request.domain,
            connectionMode=request.connectionMode,
            owner=request.owner,
            metadata=request.metadata,
            createdAt=datetime.now(timezone.utc),
        )
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.etl_sources),
                {
                    "source_id": source.sourceId,
                    "name": source.name,
                    "system_type": source.systemType,
                    "domain": source.domain,
                    "connection_mode": source.connectionMode,
                    "owner": source.owner,
                    "metadata_json": source.metadata,
                    "created_at": source.createdAt,
                },
            )
        self._audit("etl_source_registered", {"source_id": source.sourceId, "domain": source.domain})
        return source

    def list_sources(self, domain: str | None = None) -> list[EtlSource]:
        query = select(self.etl_sources)
        if domain:
            query = query.where(self.etl_sources.c.domain == domain)
        with self.engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [
            EtlSource(
                sourceId=r["source_id"],
                name=r["name"],
                systemType=r["system_type"],
                domain=r["domain"],
                connectionMode=r["connection_mode"],  # type: ignore[arg-type]
                owner=r["owner"],
                metadata=r["metadata_json"] or {},
                createdAt=r["created_at"],
            )
            for r in rows
        ]

    def record_etl_run(self, request: EtlRunRequest) -> EtlRunRecord:
        run = EtlRunRecord(
            runId=f"run_{uuid4().hex[:12]}",
            sourceId=request.sourceId,
            recordsExtracted=request.recordsExtracted,
            recordsLoaded=request.recordsLoaded,
            status=request.status,
            qualityScore=request.qualityScore,
            lineageCoverage=request.lineageCoverage,
            notes=request.notes,
            createdAt=datetime.now(timezone.utc),
        )
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.etl_runs),
                {
                    "run_id": run.runId,
                    "source_id": run.sourceId,
                    "records_extracted": run.recordsExtracted,
                    "records_loaded": run.recordsLoaded,
                    "status": run.status,
                    "quality_score": run.qualityScore,
                    "lineage_coverage": run.lineageCoverage,
                    "notes": run.notes,
                    "created_at": run.createdAt,
                },
            )
            source = conn.execute(
                select(self.etl_sources.c.domain).where(self.etl_sources.c.source_id == run.sourceId)
            ).first()
            if source:
                rows = conn.execute(
                    select(self.intelligence_systems).where(self.intelligence_systems.c.domain == source[0])
                ).mappings().all()
                for row in rows:
                    next_quality = round((row["quality_score"] * 0.7) + (run.qualityScore * 0.3), 3)
                    next_lineage = round((row["lineage_coverage"] * 0.7) + (run.lineageCoverage * 0.3), 3)
                    next_freshness = 1 if run.status == "success" else min(int(row["freshness_minutes"]) + 5, 120)
                    conn.execute(
                        update(self.intelligence_systems)
                        .where(self.intelligence_systems.c.system_id == row["system_id"])
                        .values(
                            quality_score=next_quality,
                            lineage_coverage=next_lineage,
                            freshness_minutes=next_freshness,
                        )
                    )
        self._audit("etl_run_recorded", {"run_id": run.runId, "source_id": run.sourceId, "status": run.status})
        return run

    def list_etl_runs(self, source_id: str | None = None) -> list[EtlRunRecord]:
        query = select(self.etl_runs)
        if source_id:
            query = query.where(self.etl_runs.c.source_id == source_id)
        with self.engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [
            EtlRunRecord(
                runId=r["run_id"],
                sourceId=r["source_id"],
                recordsExtracted=r["records_extracted"],
                recordsLoaded=r["records_loaded"],
                status=r["status"],  # type: ignore[arg-type]
                qualityScore=r["quality_score"],
                lineageCoverage=r["lineage_coverage"],
                notes=r["notes"],
                createdAt=r["created_at"],
            )
            for r in rows
        ]

    def set_pool_config(self, request: PoolConfigRequest) -> PoolConfigResponse:
        now = datetime.now(timezone.utc)
        value = {
            "provider": request.provider,
            "poolType": request.poolType,
            "platform": request.platform,
            "region": request.region,
            "owner": request.owner,
            "notes": request.notes,
        }
        with self.engine.begin() as conn:
            existing = conn.execute(
                select(self.platform_settings.c.key).where(self.platform_settings.c.key == "pool_config")
            ).first()
            if existing:
                conn.execute(
                    update(self.platform_settings)
                    .where(self.platform_settings.c.key == "pool_config")
                    .values(value=value, updated_at=now),
                )
            else:
                conn.execute(
                    insert(self.platform_settings).values(key="pool_config", value=value, updated_at=now)
                )
        self._audit("pool_config_updated", value)
        return PoolConfigResponse(updatedAt=now, **value)  # type: ignore[arg-type]

    def get_pool_config(self) -> PoolConfigResponse:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(self.platform_settings).where(self.platform_settings.c.key == "pool_config")
            ).mappings().first()
        if not row:
            return PoolConfigResponse(
                provider="customer_managed",
                poolType="warehouse",
                platform="snowflake",
                region="us",
                owner="data-platform",
                notes="default BYO pool",
                updatedAt=datetime.now(timezone.utc),
            )
        value = row["value"] or {}
        return PoolConfigResponse(
            provider=value.get("provider", "customer_managed"),
            poolType=value.get("poolType", "warehouse"),
            platform=value.get("platform", "snowflake"),
            region=value.get("region", "us"),
            owner=value.get("owner", "data-platform"),
            notes=value.get("notes"),
            updatedAt=row["updated_at"],
        )

    def reset(self) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(self.events))
            conn.execute(delete(self.actions))
            conn.execute(delete(self.approvals))
            conn.execute(delete(self.etl_sources))
            conn.execute(delete(self.etl_runs))
            conn.execute(delete(self.audit))
        self._seed_defaults()


def create_store():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return PostgresStore(database_url)
    return InMemoryStore()


store = create_store()
