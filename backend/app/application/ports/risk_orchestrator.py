from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.application.decision_engine.rules import ProjectSignals


@dataclass
class RiskItem:
    title: str
    category: str
    severity: str
    description: str = ""


@dataclass
class RecommendationItem:
    title: str
    category: str
    severity: str
    effort: str
    impact: str
    description: str = ""
    rationale: str = ""
    risk_index: int | None = None


@dataclass
class RiskAnalysisOutput:
    risks: list[RiskItem] = field(default_factory=list)
    recommendations: list[RecommendationItem] = field(default_factory=list)


class RiskAnalysisOrchestratorPort(ABC):
    """The seam between application/ and the CrewAI-specific implementation in
    infrastructure/agents/ - application code never imports crewai directly.
    `signals` is already-computed by the (free, local) Decision Engine - the
    LLM interprets facts, it never computes them."""

    @abstractmethod
    def analyze(
        self,
        project_name: str,
        project_description: str,
        signals: ProjectSignals,
        task_summary: str,
        dependencies_text: str,
        activity_text: str,
    ) -> RiskAnalysisOutput: ...
