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

        return store.create_action(
            request=req,
            state="completed",
            details={"mode": "live", "message": "Action executed successfully"},
        )


action_executor = ActionExecutor()
