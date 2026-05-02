from app.models import IngestEventRequest, TriggerDecision


class TriggerEngine:
    """
    Reverse-trigger logic:
    Data events can trigger outbound actions.
    """

    def evaluate(self, event: IngestEventRequest, rule_set: str) -> TriggerDecision:
        quality_score = self._quality_score(event)
        if rule_set == "security-default":
            severity = str(event.payload.get("severity", "")).lower()
            fixed_version = str(event.payload.get("fixedVersion", ""))
            if event.eventType == "critical_vulnerability_detected" and severity == "critical" and fixed_version and quality_score >= 0.7:
                return TriggerDecision(
                    triggered=True,
                    triggerType="security_vuln_critical",
                    recommendedAction="create_patch_pr",
                    confidence=0.95,
                    qualityScore=quality_score,
                    explanation="Critical vulnerability with available fix and trusted quality signal.",
                )

        if rule_set == "finance-default":
            risk = float(event.payload.get("riskScore", 0))
            if event.eventType == "payment_risk_spike" and risk >= 0.9 and quality_score >= 0.65:
                return TriggerDecision(
                    triggered=True,
                    triggerType="finance_payment_risk",
                    recommendedAction="hold_payment",
                    confidence=0.9,
                    qualityScore=quality_score,
                    explanation="High payment risk anomaly with acceptable data confidence.",
                )

        if rule_set == "healthcare-default":
            missing_critical = bool(event.payload.get("missingCriticalFields", False))
            if event.eventType == "clinical_data_quality_alert" and missing_critical and quality_score >= 0.6:
                return TriggerDecision(
                    triggered=True,
                    triggerType="healthcare_data_quality",
                    recommendedAction="open_data_stewardship_task",
                    confidence=0.88,
                    qualityScore=quality_score,
                    explanation="Clinical data quality degradation detected with valid lineage trust.",
                )

        return TriggerDecision(
            triggered=False,
            triggerType="no_match",
            recommendedAction=None,
            confidence=0.0,
            qualityScore=quality_score,
            explanation="Conditions not met or trust score below threshold.",
        )

    def _quality_score(self, event: IngestEventRequest) -> float:
        freshness = float(event.quality.get("freshness", 1.0))
        completeness = float(event.quality.get("completeness", 1.0))
        lineage = float(event.quality.get("lineageCoverage", 1.0))
        score = (freshness + completeness + lineage) / 3.0
        return max(0.0, min(1.0, score))


trigger_engine = TriggerEngine()
