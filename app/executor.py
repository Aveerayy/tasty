from app.models import ActionExecuteRequest, ActionStatus
from app.store import store


class ActionExecutor:
    """
    Minimal execution orchestrator:
    - dryRun => pending (safe mode)
    - non-dryRun => completed (simulated execution)
    """

    def execute(self, req: ActionExecuteRequest) -> ActionStatus:
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
