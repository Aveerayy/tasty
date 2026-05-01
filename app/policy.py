from app.models import PolicyDecision, PolicyEvaluationRequest


class PolicyEngine:
    """
    Minimal policy engine with safe defaults:
    - Deny if actor is missing/anonymous.
    - Require approval for high-impact actions.
    """

    HIGH_IMPACT_ACTIONS = {"create_patch_pr", "deploy_hotfix", "isolate_session", "hold_payment"}

    def evaluate(self, request: PolicyEvaluationRequest) -> PolicyDecision:
        actor = request.actor.strip().lower()
        if not actor or actor in {"anonymous", "unknown"}:
            return PolicyDecision(
                allowed=False,
                reasonCode="actor_not_trusted",
                requiresApproval=False,
                obligations=[],
            )

        requires_approval = request.actionType in self.HIGH_IMPACT_ACTIONS
        obligations = ["log_audit", "record_lineage"]
        if requires_approval:
            obligations.append("human_approval")

        return PolicyDecision(
            allowed=True,
            reasonCode="allowed_by_default_policy",
            requiresApproval=requires_approval,
            obligations=obligations,
        )


policy_engine = PolicyEngine()
