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
                riskTier="critical",
                obligations=[],
            )

        quality_score = float(request.context.get("qualityScore", 1.0))
        risk_tier = "low"
        if quality_score < 0.6:
            risk_tier = "critical"
        elif quality_score < 0.75:
            risk_tier = "high"
        elif quality_score < 0.9:
            risk_tier = "medium"

        requires_approval = request.actionType in self.HIGH_IMPACT_ACTIONS or risk_tier in {"high", "critical"}
        obligations = ["log_audit", "record_lineage"]
        if requires_approval:
            obligations.append("human_approval")
        if risk_tier in {"high", "critical"}:
            obligations.append("quality_escalation")

        return PolicyDecision(
            allowed=True,
            reasonCode="allowed_by_default_policy",
            requiresApproval=requires_approval,
            riskTier=risk_tier,  # type: ignore[arg-type]
            obligations=obligations,
        )


policy_engine = PolicyEngine()
