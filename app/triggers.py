from app.models import IngestEventRequest, TriggerDecision


class TriggerEngine:
    """
    Reverse-trigger logic:
    Data events can trigger outbound actions.
    """

    def evaluate(self, event: IngestEventRequest, rule_set: str) -> TriggerDecision:
        if rule_set == "security-default":
            severity = str(event.payload.get("severity", "")).lower()
            fixed_version = str(event.payload.get("fixedVersion", ""))
            if event.eventType == "critical_vulnerability_detected" and severity == "critical" and fixed_version:
                return TriggerDecision(
                    triggered=True,
                    triggerType="security_vuln_critical",
                    recommendedAction="create_patch_pr",
                    confidence=0.95,
                )

        if rule_set == "finance-default":
            risk = float(event.payload.get("riskScore", 0))
            if event.eventType == "payment_risk_spike" and risk >= 0.9:
                return TriggerDecision(
                    triggered=True,
                    triggerType="finance_payment_risk",
                    recommendedAction="hold_payment",
                    confidence=0.9,
                )

        if rule_set == "healthcare-default":
            missing_critical = bool(event.payload.get("missingCriticalFields", False))
            if event.eventType == "clinical_data_quality_alert" and missing_critical:
                return TriggerDecision(
                    triggered=True,
                    triggerType="healthcare_data_quality",
                    recommendedAction="open_data_stewardship_task",
                    confidence=0.88,
                )

        return TriggerDecision(triggered=False, triggerType="no_match", recommendedAction=None, confidence=0.0)


trigger_engine = TriggerEngine()
