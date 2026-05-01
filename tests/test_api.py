from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_security_reverse_trigger_flow() -> None:
    ingest = client.post(
        "/v1/events/ingest",
        json={
            "eventType": "critical_vulnerability_detected",
            "domain": "security",
            "timestamp": "2026-05-01T00:00:00Z",
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
    )
    assert ingest.status_code == 202
    event_id = ingest.json()["eventId"]

    trigger = client.post(
        "/v1/triggers/evaluate",
        json={"eventId": event_id, "ruleSet": "security-default"},
    )
    assert trigger.status_code == 200
    assert trigger.json()["triggered"] is True
    assert trigger.json()["recommendedAction"] == "create_patch_pr"

    policy = client.post(
        "/v1/policy/evaluate",
        json={"actionType": "create_patch_pr", "actor": "sec-operator", "context": {}},
    )
    assert policy.status_code == 200
    assert policy.json()["allowed"] is True
    assert policy.json()["requiresApproval"] is True

    action = client.post(
        "/v1/actions/execute",
        json={
            "actionType": "create_patch_pr",
            "target": {"repo": "org/app"},
            "initiatedBy": "sec-operator",
            "approvalId": "approval-1",
            "dryRun": True,
        },
    )
    assert action.status_code == 202
    assert action.json()["state"] == "pending"


def test_playground_endpoints() -> None:
    scenarios = client.get("/v1/playground/scenarios")
    assert scenarios.status_code == 200
    body = scenarios.json()
    assert "security" in body
    assert len(body["security"]) > 0

    run_today = client.post(
        "/v1/playground/run",
        json={
            "mode": "today",
            "domain": "security",
            "scenarioId": "sec-vuln-critical",
            "actor": "playground-user",
            "dryRun": True,
        },
    )
    assert run_today.status_code == 200
    assert "today" == run_today.json()["mode"]

    run_reverse = client.post(
        "/v1/playground/run",
        json={
            "mode": "reverse",
            "domain": "security",
            "scenarioId": "sec-vuln-critical",
            "actor": "playground-user",
            "dryRun": True,
        },
    )
    assert run_reverse.status_code == 200
    assert "reverse" == run_reverse.json()["mode"]

    page = client.get("/playground")
    assert page.status_code == 200
    assert "tasty Playground" in page.text
