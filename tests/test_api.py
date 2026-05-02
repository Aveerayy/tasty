import os

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


def test_intelligence_layer_and_approval_flow() -> None:
    systems = client.get("/v1/intelligence/systems?domain=security")
    assert systems.status_code == 200
    assert len(systems.json()["systems"]) >= 1

    query = client.post(
        "/v1/intelligence/query",
        json={"domain": "security", "query": "show risk posture", "includeLineage": True, "includeQuality": True},
    )
    assert query.status_code == 200
    assert "qualitySummary" in query.json()

    # High risk live action without approval should fail
    fail_action = client.post(
        "/v1/actions/execute",
        json={
            "actionType": "hold_payment",
            "target": {"paymentId": "pay_1"},
            "initiatedBy": "fin-operator",
            "dryRun": False,
            "riskTier": "high",
        },
    )
    assert fail_action.status_code == 202
    assert fail_action.json()["state"] == "failed"

    approval = client.post(
        "/v1/approvals/issue",
        json={"actionType": "hold_payment", "actor": "fin-operator", "reason": "risk playbook"},
    )
    assert approval.status_code == 201
    approval_id = approval.json()["approvalId"]

    pass_action = client.post(
        "/v1/actions/execute",
        json={
            "actionType": "hold_payment",
            "target": {"paymentId": "pay_1"},
            "initiatedBy": "fin-operator",
            "approvalId": approval_id,
            "dryRun": False,
            "riskTier": "high",
        },
    )
    assert pass_action.status_code == 202
    assert pass_action.json()["state"] == "completed"


def test_etl_source_and_runs_update_intelligence() -> None:
    source = client.post(
        "/v1/etl/sources",
        json={
            "sourceId": "src_salesforce_crm",
            "name": "Salesforce CRM",
            "systemType": "salesforce",
            "domain": "finance",
            "connectionMode": "api",
            "owner": "data-platform",
            "metadata": {"region": "us"},
        },
    )
    assert source.status_code == 201

    run = client.post(
        "/v1/etl/runs",
        json={
            "sourceId": "src_salesforce_crm",
            "recordsExtracted": 1000,
            "recordsLoaded": 995,
            "status": "partial",
            "qualityScore": 0.8,
            "lineageCoverage": 0.85,
            "notes": "minor schema drift handled",
        },
    )
    assert run.status_code == 201
    assert run.json()["sourceId"] == "src_salesforce_crm"

    sources = client.get("/v1/etl/sources?domain=finance")
    assert sources.status_code == 200
    assert len(sources.json()["sources"]) >= 1

    runs = client.get("/v1/etl/runs?sourceId=src_salesforce_crm")
    assert runs.status_code == 200
    assert len(runs.json()["runs"]) >= 1


def test_pool_config_endpoints() -> None:
    current = client.get("/v1/platform/pool-config")
    assert current.status_code == 200
    assert current.json()["provider"] in {"customer_managed", "platform_managed"}

    updated = client.put(
        "/v1/platform/pool-config",
        json={
            "provider": "platform_managed",
            "poolType": "lakehouse",
            "platform": "caeesar-managed",
            "region": "us",
            "owner": "caeesar-cloud",
            "notes": "managed pilot",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["provider"] == "platform_managed"
    assert updated.json()["platform"] == "caeesar-managed"


def test_live_action_connector_simulated_when_no_webhook() -> None:
    approval = client.post(
        "/v1/approvals/issue",
        json={"actionType": "hold_payment", "actor": "fin-operator", "reason": "test execution"},
    )
    assert approval.status_code == 201
    approval_id = approval.json()["approvalId"]

    action = client.post(
        "/v1/actions/execute",
        json={
            "actionType": "hold_payment",
            "target": {"paymentId": "pay_2"},
            "initiatedBy": "fin-operator",
            "dryRun": False,
            "riskTier": "high",
            "approvalId": approval_id,
        },
    )
    assert action.status_code == 202
    assert action.json()["state"] == "completed"
    assert action.json()["details"]["connector"]["connectorMode"] == "simulated"


def test_auth_rbac_enabled_blocks_without_headers() -> None:
    prev_enabled = os.environ.get("AUTH_ENABLED")
    prev_key = os.environ.get("CONTROL_PLANE_API_KEY")
    try:
        os.environ["AUTH_ENABLED"] = "true"
        os.environ["CONTROL_PLANE_API_KEY"] = "secret-key"

        ingest = client.post(
            "/v1/events/ingest",
            json={
                "eventType": "critical_vulnerability_detected",
                "domain": "security",
                "timestamp": "2026-05-01T00:00:00Z",
                "payload": {"application": "billing-api"},
            },
        )
        assert ingest.status_code == 401

        ingest_ok = client.post(
            "/v1/events/ingest",
            headers={"x-api-key": "secret-key", "x-actor-role": "operator"},
            json={
                "eventType": "critical_vulnerability_detected",
                "domain": "security",
                "timestamp": "2026-05-01T00:00:00Z",
                "payload": {"application": "billing-api"},
            },
        )
        assert ingest_ok.status_code == 202

        pool_forbidden = client.put(
            "/v1/platform/pool-config",
            headers={"x-api-key": "secret-key", "x-actor-role": "operator"},
            json={
                "provider": "customer_managed",
                "poolType": "warehouse",
                "platform": "snowflake",
                "region": "us",
                "owner": "data-platform",
            },
        )
        assert pool_forbidden.status_code == 403
    finally:
        if prev_enabled is None:
            os.environ.pop("AUTH_ENABLED", None)
        else:
            os.environ["AUTH_ENABLED"] = prev_enabled
        if prev_key is None:
            os.environ.pop("CONTROL_PLANE_API_KEY", None)
        else:
            os.environ["CONTROL_PLANE_API_KEY"] = prev_key
