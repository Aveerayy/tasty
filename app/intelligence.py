from __future__ import annotations

from app.models import IntelligenceQueryRequest, IntelligenceQueryResponse
from app.store import store


class IntelligenceLayer:
    """
    Centralized read-only intelligent layer over business systems.
    """

    def query(self, request: IntelligenceQueryRequest) -> IntelligenceQueryResponse:
        systems = store.list_systems(request.domain)
        avg_quality = sum(s.qualityScore for s in systems) / max(1, len(systems))
        avg_lineage = sum(s.lineageCoverage for s in systems) / max(1, len(systems))
        max_freshness = max((s.freshnessMinutes for s in systems), default=0)

        answer = (
            f"Read-only intelligence for {request.domain}: "
            f"{len(systems)} systems, quality {avg_quality:.2f}, lineage {avg_lineage:.2f}, "
            f"max freshness lag {max_freshness} minutes."
        )

        return IntelligenceQueryResponse(
            domain=request.domain,
            answer=answer,
            systems=systems,
            qualitySummary={
                "qualityScore": round(avg_quality, 3),
                "lineageCoverage": round(avg_lineage, 3),
                "freshnessLagMinutes": max_freshness,
            },
        )


intelligence_layer = IntelligenceLayer()
