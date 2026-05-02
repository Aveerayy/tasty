from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.executor import action_executor
from app.intelligence import intelligence_layer
from app.models import (
    ActionExecuteRequest,
    ActionStatus,
    ApprovalRequest,
    ApprovalToken,
    EventAck,
    EtlRunRecord,
    EtlRunRequest,
    EtlSource,
    EtlSourceRequest,
    IngestEventRequest,
    IntelligenceQueryRequest,
    IntelligenceQueryResponse,
    PlaygroundRunRequest,
    PlaygroundRunResponse,
    PoolConfigRequest,
    PoolConfigResponse,
    PolicyDecision,
    PolicyEvaluationRequest,
    TriggerDecision,
    TriggerEvaluationRequest,
)
from app.policy import policy_engine
from app.playground_service import playground_service
from app.store import store
from app.triggers import trigger_engine

app = FastAPI(
    title="tasty control plane",
    version="0.1.0",
    description="Lineage-first governance control plane for AI agent workflows",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/events/ingest", response_model=EventAck, status_code=202)
def ingest_event(request: IngestEventRequest) -> EventAck:
    event_id = store.ingest_event(request)
    return EventAck(eventId=event_id, accepted=True)


@app.post("/v1/policy/evaluate", response_model=PolicyDecision)
def evaluate_policy(request: PolicyEvaluationRequest) -> PolicyDecision:
    return policy_engine.evaluate(request)


@app.post("/v1/triggers/evaluate", response_model=TriggerDecision)
def evaluate_triggers(request: TriggerEvaluationRequest) -> TriggerDecision:
    event = store.get_event(request.eventId)
    if not event:
        raise HTTPException(status_code=404, detail=f"event not found: {request.eventId}")
    return trigger_engine.evaluate(event, request.ruleSet)


@app.post("/v1/actions/execute", response_model=ActionStatus, status_code=202)
def execute_action(request: ActionExecuteRequest) -> ActionStatus:
    return action_executor.execute(request)


@app.get("/v1/actions/{action_id}", response_model=ActionStatus)
def get_action_status(action_id: str) -> ActionStatus:
    status = store.get_action(action_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"action not found: {action_id}")
    return status


@app.post("/v1/approvals/issue", response_model=ApprovalToken, status_code=201)
def issue_approval(request: ApprovalRequest) -> ApprovalToken:
    return store.create_approval(actor=request.actor)


@app.get("/v1/intelligence/systems")
def list_intelligence_systems(domain: Optional[str] = None) -> dict:
    systems = store.list_systems(domain)
    return {"systems": [s.model_dump() for s in systems]}


@app.post("/v1/intelligence/query", response_model=IntelligenceQueryResponse)
def intelligence_query(request: IntelligenceQueryRequest) -> IntelligenceQueryResponse:
    return intelligence_layer.query(request)


@app.post("/v1/etl/sources", response_model=EtlSource, status_code=201)
def register_etl_source(request: EtlSourceRequest) -> EtlSource:
    return store.register_source(request)


@app.get("/v1/etl/sources")
def list_etl_sources(domain: Optional[str] = None) -> dict:
    sources = store.list_sources(domain)
    return {"sources": [s.model_dump(mode="json") for s in sources]}


@app.post("/v1/etl/runs", response_model=EtlRunRecord, status_code=201)
def record_etl_run(request: EtlRunRequest) -> EtlRunRecord:
    if request.sourceId not in {s.sourceId for s in store.list_sources()}:
        raise HTTPException(status_code=404, detail=f"etl source not found: {request.sourceId}")
    return store.record_etl_run(request)


@app.get("/v1/etl/runs")
def list_etl_runs(sourceId: Optional[str] = None) -> dict:
    runs = store.list_etl_runs(source_id=sourceId)
    return {"runs": [r.model_dump(mode="json") for r in runs]}


@app.get("/v1/platform/pool-config", response_model=PoolConfigResponse)
def get_pool_config() -> PoolConfigResponse:
    return store.get_pool_config()


@app.put("/v1/platform/pool-config", response_model=PoolConfigResponse)
def update_pool_config(request: PoolConfigRequest) -> PoolConfigResponse:
    return store.set_pool_config(request)


@app.get("/playground", response_class=HTMLResponse)
def playground() -> str:
    page = Path(__file__).parent / "static" / "playground.html"
    return page.read_text(encoding="utf-8")


@app.get("/v1/playground/scenarios")
def playground_scenarios() -> dict:
    return playground_service.list_scenarios()


@app.post("/v1/playground/run", response_model=PlaygroundRunResponse)
def playground_run(request: PlaygroundRunRequest) -> PlaygroundRunResponse:
    return playground_service.run(request)


@app.post("/v1/playground/reset")
def playground_reset() -> dict:
    store.reset()
    return {"ok": True}
