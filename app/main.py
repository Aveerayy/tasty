from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.executor import action_executor
from app.models import (
    ActionExecuteRequest,
    ActionStatus,
    EventAck,
    IngestEventRequest,
    PlaygroundRunRequest,
    PlaygroundRunResponse,
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
