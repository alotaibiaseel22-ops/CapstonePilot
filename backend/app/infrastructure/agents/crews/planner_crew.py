from typing import Literal

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.agents.crews.documentation_crew import DocumentAnalysisSchema
from app.infrastructure.agents.llm import planning_llm

# Wire schema uses short keys (t/d/k/p/dep/tl/m/s) since key names get
# repeated on every single item and are the highest-leverage place to cut
# tokens under a 300 max_output_tokens budget - `populate_by_name=True` means
# these models still work fine if ever constructed from Python by full name.


class TaskPlanSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(alias="t")
    description: str = ""
    priority: Literal["low", "medium", "high"] = Field(default="medium", alias="p")
    days_from_start: int = Field(default=0, alias="d")


class MilestonePlanSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(alias="t")
    days_from_start: int = Field(alias="d")
    tasks: list[TaskPlanSchema] = Field(alias="k")
    # A duration estimate, never a calendar date - omitted/null when the
    # Planner can't reasonably estimate it, never guessed with false
    # confidence. The deadline itself always comes from the project owner.
    estimated_duration_days: int | None = Field(default=None, alias="ed")


class PlannerOutputSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: str = Field(alias="s")
    milestones: list[MilestonePlanSchema] = Field(alias="m")
    dependencies: list[str] = Field(alias="dep")
    estimated_timeline: str = Field(alias="tl")


def build_planner_crew(
    project_name: str, project_description: str, analysis: DocumentAnalysisSchema
) -> Crew:
    # Stage 2 of 2 (see documentation_crew.py for stage 1): this agent never
    # reads the raw proposal - only the already-extracted, compact JSON -
    # which is what keeps this call's own prompt/output small even though
    # the Documentation Agent read the entire document to produce it.
    planner = Agent(
        role="Senior Software Delivery Planner",
        goal=(
            "Turn extracted project knowledge into a realistic, sequenced "
            "SDLC delivery plan where every milestone and task is traceable "
            "to a specific extracted module or requirement - never a "
            "generic software-project template. Reason about realistic "
            "build order and dependencies between modules. Never invent "
            "scope beyond what was extracted. JSON only."
        ),
        backstory=(
            "A senior technical delivery planner who has scoped and "
            "sequenced dozens of capstone-scale software projects. Thinks "
            "in terms of what must be built before what, and refuses to "
            "write a milestone titled 'Development' when the actual module "
            "has a name. Writes like a senior PM handing off a real sprint "
            "plan: concrete, grounded, no filler."
        ),
        llm=planning_llm(),
        verbose=False,
        max_retry_limit=0,
    )

    task = Task(
        description=(
            "You are a Software Project Planner.\n\n"
            "You are NOT allowed to read the original proposal.\n\n"
            "You receive only the extracted project knowledge below.\n\n"
            "Generate a realistic SDLC project plan using ONLY the extracted "
            "information. Every milestone must correspond to actual project "
            "modules or requirements from this data. Preserve the "
            "terminology used in it. Never generate generic software "
            "milestones (e.g. plain \"Requirements\", \"Development\", "
            "\"Testing\") when a specific module or requirement name is "
            "available instead. Never invent features that were not "
            "extracted. If required information is missing, do not invent "
            "it.\n\n"
            f"Project: {project_name}\n"
            f"Description: {project_description}\n"
            f"Extracted project knowledge:\n{analysis.model_dump_json()}\n\n"
            "Produce a plan: 3-4 milestones, 2-3 tasks each. Titles <=6 "
            "words and specific to the extracted modules/requirements. No "
            "task descriptions. <=3 dependencies. Timeline <=12 words. "
            "Summary <=15 words. 'd' is an integer day offset from project "
            "start, increasing across the plan. 'ed' is your best estimate "
            "of how many days that milestone takes, as a plain integer - "
            "only include it when you can reasonably estimate it from the "
            "extracted scope, omit it entirely otherwise. Never output a "
            "calendar date or a project deadline anywhere - only relative "
            "day offsets/durations. The submission deadline is defined by "
            "the project owner, not by you.\n\n"
            "Output ONLY this minified JSON (no spaces, no newlines, no "
            "markdown, no explanation):\n"
            '{"s":"...","m":[{"t":"...","d":0,"ed":0,"k":[{"t":"...","p":'
            '"low|medium|high","d":0}]}],"dep":["..."],"tl":"..."}'
        ),
        expected_output="One line of minified JSON matching the shape above. Nothing else.",
        agent=planner,
    )

    return Crew(agents=[planner], tasks=[task], process=Process.sequential, tracing=False)
