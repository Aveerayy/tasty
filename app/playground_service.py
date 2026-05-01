from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app.executor import action_executor
from app.models import (
    ActionExecuteRequest,
    IngestEventRequest,
    PlaygroundRunRequest,
    PlaygroundRunResponse,
    PlaygroundStep,
    PolicyEvaluationRequest,
    TriggerEvaluationRequest,
)
from app.policy import policy_engine
from app.store import store
from app.triggers import trigger_engine


class PlaygroundService:
    def __init__(self) -> None:
        self._scenarios = {
            "security": [
                {
                    "id": "sec-vuln-critical",
                    "name": "Critical package vulnerability",
                    "todayPrompt": "Find vulnerabilities and create a patch for billing-api.",
                    "event": {
                        "eventType": "critical_vulnerability_detected",
                        "payload": {
                            "application": "billing-api",
                            "environment": "production",
                            "packageName": "openssl",
                            "currentVersion": "1.0.2",
                            "fixedVersion": "1.0.3",
                            "cve": "CVE-2026-0001",
                            "severity": "critical",
                        },
                    },
                    "ruleSet": "security-default",
                }
            ],
            "finance": [
                {
                    "id": "fin-payment-risk",
                    "name": "Payment risk anomaly spike",
                    "todayPrompt": "Check payment anomalies and hold suspicious transfers.",
                    "event": {
                        "eventType": "payment_risk_spike",
                        "payload": {
                            "paymentId": "pay_1288",
                            "accountId": "acct_44",
                            "riskScore": 0.94,
                        },
                    },
                    "ruleSet": "finance-default",
                }
            ],
            "healthcare": [
                {
                    "id": "hc-data-quality",
                    "name": "Clinical record quality drift",
                    "todayPrompt": "Review clinical data errors and open stewardship tasks.",
                    "event": {
                        "eventType": "clinical_data_quality_alert",
                        "payload": {
                            "patientRecordId": "pr_552",
                            "missingCriticalFields": True,
                        },
                    },
                    "ruleSet": "healthcare-default",
                }
            ],
        }

    def list_scenarios(self) -> dict[str, list[dict[str, Any]]]:
        return deepcopy(self._scenarios)

    def run(self, request: PlaygroundRunRequest) -> PlaygroundRunResponse:
        scenario = self._find_scenario(request.domain, request.scenarioId)
        if not scenario:
            return PlaygroundRunResponse(
                mode=request.mode,
                domain=request.domain,
                scenarioId=request.scenarioId,
                summary="Scenario not found",
                steps=[PlaygroundStep(name="scenario_lookup", status="failed", detail={})],
            )

        if request.mode == "today":
            return self._run_today(request, scenario)
        return self._run_reverse(request, scenario)

    def _run_today(self, request: PlaygroundRunRequest, scenario: dict[str, Any]) -> PlaygroundRunResponse:
        steps: list[PlaygroundStep] = []

        steps.append(
            PlaygroundStep(
                name="user_prompt_received",
                status="done",
                detail={"prompt": scenario["todayPrompt"]},
            )
        )

        event_request = IngestEventRequest(
            eventType=scenario["event"]["eventType"],
            domain=request.domain,
            timestamp=datetime.now(timezone.utc),
            payload=scenario["event"]["payload"],
        )
        event_id = store.ingest_event(event_request)
        steps.append(
            PlaygroundStep(
                name="agent_queries_data",
                status="done",
                detail={"eventId": event_id, "approach": "prompt-first"},
            )
        )

        action_type = "create_patch_pr" if request.domain == "security" else (
            "hold_payment" if request.domain == "finance" else "open_data_stewardship_task"
        )
        policy = policy_engine.evaluate(
            PolicyEvaluationRequest(actionType=action_type, actor=request.actor, context={"mode": "today"})
        )
        steps.append(
            PlaygroundStep(
                name="policy_check",
                status="done" if policy.allowed else "failed",
                detail=policy.model_dump(),
            )
        )

        if not policy.allowed:
            return PlaygroundRunResponse(
                mode=request.mode,
                domain=request.domain,
                scenarioId=request.scenarioId,
                summary="Today-flow blocked by policy.",
                steps=steps,
            )

        action = action_executor.execute(
            ActionExecuteRequest(
                actionType=action_type,
                target=scenario["event"]["payload"],
                initiatedBy=request.actor,
                dryRun=request.dryRun,
            )
        )
        steps.append(PlaygroundStep(name="action_execution", status="done", detail=action.model_dump(mode="json")))

        return PlaygroundRunResponse(
            mode=request.mode,
            domain=request.domain,
            scenarioId=request.scenarioId,
            summary="Today model completed: prompt -> read -> policy -> action.",
            steps=steps,
        )

    def _run_reverse(self, request: PlaygroundRunRequest, scenario: dict[str, Any]) -> PlaygroundRunResponse:
        steps: list[PlaygroundStep] = []

        event_request = IngestEventRequest(
            eventType=scenario["event"]["eventType"],
            domain=request.domain,
            timestamp=datetime.now(timezone.utc),
            payload=scenario["event"]["payload"],
        )
        event_id = store.ingest_event(event_request)
        steps.append(
            PlaygroundStep(
                name="data_change_detected",
                status="done",
                detail={"eventId": event_id},
            )
        )

        trigger = trigger_engine.evaluate(event_request, scenario["ruleSet"])
        steps.append(
            PlaygroundStep(
                name="trigger_evaluated",
                status="done" if trigger.triggered else "failed",
                detail=trigger.model_dump(),
            )
        )

        if not trigger.triggered or not trigger.recommendedAction:
            return PlaygroundRunResponse(
                mode=request.mode,
                domain=request.domain,
                scenarioId=request.scenarioId,
                summary="Reverse model evaluated but no trigger fired.",
                steps=steps,
            )

        policy = policy_engine.evaluate(
            PolicyEvaluationRequest(
                actionType=trigger.recommendedAction,
                actor=request.actor,
                context={"mode": "reverse", "eventId": event_id},
            )
        )
        steps.append(PlaygroundStep(name="policy_loop", status="done" if policy.allowed else "failed", detail=policy.model_dump()))

        if not policy.allowed:
            return PlaygroundRunResponse(
                mode=request.mode,
                domain=request.domain,
                scenarioId=request.scenarioId,
                summary="Reverse model blocked by policy.",
                steps=steps,
            )

        if policy.requiresApproval:
            steps.append(
                PlaygroundStep(
                    name="approval_loop",
                    status="done",
                    detail={"approval": "simulated_approved", "reason": "playground auto-approval"},
                )
            )
        else:
            steps.append(PlaygroundStep(name="approval_loop", status="skipped", detail={"reason": "not required"}))

        action = action_executor.execute(
            ActionExecuteRequest(
                actionType=trigger.recommendedAction,
                target=event_request.payload,
                initiatedBy=request.actor,
                dryRun=request.dryRun,
            )
        )
        steps.append(PlaygroundStep(name="execution_loop", status="done", detail=action.model_dump(mode="json")))

        return PlaygroundRunResponse(
            mode=request.mode,
            domain=request.domain,
            scenarioId=request.scenarioId,
            summary="Reverse model completed: data change -> trigger -> policy/approval -> action.",
            steps=steps,
        )

    def _find_scenario(self, domain: str, scenario_id: str) -> dict[str, Any] | None:
        for scenario in self._scenarios.get(domain, []):
            if scenario["id"] == scenario_id:
                return deepcopy(scenario)
        return None


playground_service = PlaygroundService()
