from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from app.infrastructure.agents.llm import documentation_analysis_llm

# Full field names on purpose (unlike PlannerOutputSchema's wire format) -
# this schema is never itself an LLM *output* budget concern downstream, only
# compact *input* to the Planner (see planner_crew.py, which serializes it
# with model_dump_json()). Defaults are empty, never None, so the Planner's
# prompt can safely assume every field is present even when nothing was
# extracted for it.


class DocumentAnalysisSchema(BaseModel):
    project_title: str = ""
    problem_statement: str = ""
    project_objectives: list[str] = Field(default_factory=list)
    target_users: list[str] = Field(default_factory=list)
    functional_requirements: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    main_modules: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    important_keywords: list[str] = Field(default_factory=list)


def build_documentation_crew(proposal_text: str) -> Crew:
    # This agent's ONLY job is extraction - it must never generate milestones,
    # tasks, or recommendations. Splitting this out from the Planner (see
    # planner_crew.py) is what lets the Planner work from a compact, already-
    # understood JSON instead of re-reading (and re-interpreting) the raw
    # document under its own tight output budget.
    analyst = Agent(
        role="Senior Software Requirements Analyst",
        goal=(
            "Perform a rigorous requirements-engineering pass over the "
            "uploaded project documentation: identify and correctly "
            "categorize every explicitly stated objective, user, functional "
            "and non-functional requirement, module, deliverable, "
            "constraint, and technology - without adding, inferring, or "
            "reinterpreting anything the document does not say. Never plan, "
            "never summarize, never invent."
        ),
        backstory=(
            "A senior requirements analyst with two decades of experience "
            "turning raw capstone and enterprise proposals into precise "
            "software requirement specifications. Trained to distinguish "
            "functional behavior from non-functional constraints, and to "
            "separate what a document promises to deliver from how it will "
            "be built. Treats every extracted fact as something that must "
            "trace back to an explicit sentence in the source - if it isn't "
            "written down, it doesn't exist."
        ),
        llm=documentation_analysis_llm(),
        verbose=False,
        max_retry_limit=0,
    )

    task = Task(
        description=(
            "You are a senior Software Business Analyst.\n\n"
            "Your task is NOT to create a plan.\n\n"
            "Your task is to carefully read the uploaded project "
            "documentation below and extract every important project fact "
            "into structured JSON.\n\n"
            "Do not summarize.\n"
            "Do not generate milestones.\n"
            "Do not generate recommendations.\n"
            "Do not invent requirements.\n"
            "Only extract.\n\n"
            "Rules:\n"
            "- Extract only information explicitly present in the proposal.\n"
            "- Never invent missing requirements.\n"
            "- If information does not exist, return an empty array or "
            "empty string for that field.\n"
            "- Ignore acknowledgements, cover pages, page numbers, "
            "references and formatting noise.\n"
            "- Focus on software requirements.\n\n"
            f"Project documentation:\n{proposal_text}\n\n"
            "Output ONLY this JSON shape (no markdown, no explanation):\n"
            '{"project_title":"","problem_statement":"","project_objectives"'
            ':[],"target_users":[],"functional_requirements":[],'
            '"non_functional_requirements":[],"main_modules":[],'
            '"deliverables":[],"constraints":[],"technologies":[],'
            '"important_keywords":[]}'
        ),
        expected_output="One JSON object matching the shape above. Nothing else.",
        agent=analyst,
    )

    return Crew(agents=[analyst], tasks=[task], process=Process.sequential, tracing=False)
