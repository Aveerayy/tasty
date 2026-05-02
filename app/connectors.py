from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


class ActionConnector:
    WEBHOOK_ACTIONS = {"create_patch_pr", "hold_payment", "open_data_stewardship_task", "deploy_hotfix", "isolate_session"}

    def execute(self, action_type: str, target: dict[str, Any], initiated_by: str, dry_run: bool) -> dict[str, Any]:
        if dry_run:
            return {"ok": True, "mode": "dry_run", "connectorMode": "simulated", "message": "Dry run only"}

        webhook_url = os.getenv("ACTION_WEBHOOK_URL", "").strip()
        if action_type in self.WEBHOOK_ACTIONS and webhook_url:
            payload = {
                "actionType": action_type,
                "target": target,
                "initiatedBy": initiated_by,
            }
            body = json.dumps(payload).encode("utf-8")
            req = request.Request(
                webhook_url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=5) as resp:  # nosec B310
                    status_code = getattr(resp, "status", 200)
                    if 200 <= status_code < 300:
                        return {
                            "ok": True,
                            "mode": "live",
                            "connectorMode": "webhook",
                            "message": "Webhook connector executed",
                            "statusCode": status_code,
                        }
                    return {
                        "ok": False,
                        "mode": "live",
                        "connectorMode": "webhook",
                        "message": f"Webhook returned non-success status {status_code}",
                        "statusCode": status_code,
                    }
            except (error.URLError, TimeoutError) as exc:
                return {
                    "ok": False,
                    "mode": "live",
                    "connectorMode": "webhook",
                    "message": f"Webhook connector failed: {exc}",
                }

        return {
            "ok": True,
            "mode": "live",
            "connectorMode": "simulated",
            "message": "No webhook configured; simulated live execution",
        }


action_connector = ActionConnector()
