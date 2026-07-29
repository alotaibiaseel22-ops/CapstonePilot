from crewai import Flow
from crewai.flow import listen, start
from pydantic import BaseModel

from app.infrastructure.agents.crews.documentation_crew import (
    DocumentAnalysisSchema,
    build_documentation_crew,
)
from app.infrastructure.agents.crews.planner_crew import PlannerOutputSchema, build_planner_crew
from app.infrastructure.agents.json_parsing import parse_json_response

# Safety cap on what gets sent to the Documentation Agent - never triggers for
# a real capstone proposal (a few pages of text), only guards against a
# pathological upload (ProposalAnalysisService accepts files up to 20MB).
# Named and applied here, not silently buried inside the crew, since it's the
# one deliberate limit left after removing the old proposal_text[:3000] cut.
_MAX_PROPOSAL_CHARS = 40_000


class PlanningFlowState(BaseModel):
    project_name: str = ""
    project_description: str = ""
    proposal_text: str = ""


class PlanningFlow(Flow[PlanningFlowState]):
    """Two Gemini calls per generation, deliberately: a Documentation
    Analysis Agent reads the entire proposal and extracts structured facts
    (stage 1), then a Planner Agent turns only that compact extraction - never
    the raw document - into milestones/tasks (stage 2). Replaces the earlier
    single-call design (see docs/architecture.md, "One Gemini Call Per
    Generation") because that design forced one prompt to both understand and
    plan at once, producing generic, template-shaped plans. Future iterations
    (Risk, Recommendation) become new @listen/@router steps off this Flow
    without changing its control structure."""

    @start()
    def analyze_documentation(self) -> DocumentAnalysisSchema:
        crew = build_documentation_crew(self.state.proposal_text[:_MAX_PROPOSAL_CHARS])
        result = crew.kickoff()
        return DocumentAnalysisSchema.model_validate(parse_json_response(result.raw))

    @listen(analyze_documentation)
    def plan(self, analysis: DocumentAnalysisSchema) -> PlannerOutputSchema:
        crew = build_planner_crew(self.state.project_name, self.state.project_description, analysis)
        result = crew.kickoff()
        return PlannerOutputSchema.model_validate(parse_json_response(result.raw))
