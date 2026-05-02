import os

from app.connectors import action_connector
from app.models import ActionExecuteRequest, ActionStatus
from app.store import store


class ActionExecutor:
    """
    Minimal execution orchestrator:
    - dryRun => pending (safe mode)
    - non-dryRun => completed (simulated execution)
    """

    def execute(self, req: ActionExecuteRequest) -> ActionStatus:
        if not req.dryRun and req.riskTier in {"high", "critical"} and not req.approvalId:
            return store.create_action(
                request=req,
                state="failed",
                details={"mode": "live", "message": "Approval required for high-risk live actions"},
            )

        if not req.dryRun and req.approvalId:
            token = store.get_approval(req.approvalId)
            if not token:
                return store.create_action(
                    request=req,
                    state="failed",
                    details={"mode": "live", "message": "Invalid or expired approval token"},
                )

        if req.dryRun:
            return store.create_action(
                request=req,
                state="pending",
                details={"mode": "dry_run", "message": "Action validated but not executed"},
            )

        max_retries = max(0, int(os.getenv("ACTION_MAX_RETRIES", "2")))
        attempts = 0
        last_result: dict = {}
        while attempts <= max_retries:
            attempts += 1
            result = action_connector.execute(
                action_type=req.actionType,
                target=req.target,
                initiated_by=req.initiatedBy,
                dry_run=False,
            )
            last_result = result
            if result.get("ok"):
                return store.create_action(
                    request=req,
                    state="completed",
                    details={
                        "mode": "live",
                        "message": "Action executed successfully",
                        "attempts": attempts,
                        "connector": result,
                    },
                )

        return store.create_action(
            request=req,
            state="failed",
            details={
                "mode": "live",
                "message": "Action execution failed after retries",
                "attempts": attempts,
                "retryLimit": max_retries,
                "connector": last_result,
            },
        )


action_executor = ActionExecutor()
