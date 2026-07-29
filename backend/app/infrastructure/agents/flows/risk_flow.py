from crewai import Flow
from crewai.flow import start
from pydantic import BaseModel

from app.infrastructure.agents.crews.risk_crew import RiskAnalysisSchema, build_risk_crew
from app.infrastructure.agents.json_parsing import parse_json_response


class RiskFlowState(BaseModel):
    project_name: str = ""
    project_description: str = ""
    signals_text: str = ""
    task_summary: str = ""
    dependencies_text: str = ""
    activity_text: str = ""


class RiskFlow(Flow[RiskFlowState]):
    """Exactly ONE Gemini call per breached project per tick: a single Risk
    Analyst crew reads the Decision Engine's already-computed signals text and
    produces risks + recommendations together in one shot."""

    @start()
    def analyze(self) -> RiskAnalysisSchema:
        crew = build_risk_crew(
            self.state.project_name,
            self.state.project_description,
            self.state.signals_text,
            self.state.task_summary,
            self.state.dependencies_text,
            self.state.activity_text,
        )
        result = crew.kickoff()
        return RiskAnalysisSchema.model_validate(parse_json_response(result.raw))
