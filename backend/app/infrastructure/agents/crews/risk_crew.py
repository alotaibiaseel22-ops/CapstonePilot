from typing import Literal

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.agents.llm import risk_analysis_llm

# Same short-key wire schema convention as planner_crew.py - key names repeat
# on every item and are the highest-leverage place to cut tokens under a
# 300 max_output_tokens budget. `populate_by_name=True` keeps full-name
# construction working from Python too.


class RiskSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(alias="t")
    category: str = Field(alias="c")
    severity: Literal["low", "medium", "high"] = Field(alias="s")
    description: str = Field(default="", alias="d")


class RecommendationSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(alias="t")
    category: str = Field(alias="c")
    severity: Literal["low", "medium", "high"] = Field(alias="s")
    effort: Literal["low", "medium", "high"] = Field(alias="e")
    impact: Literal["low", "medium", "high"] = Field(alias="i")
    description: str = Field(default="", alias="d")
    risk_index: int | None = Field(default=None, alias="r")


class RiskAnalysisSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    risks: list[RiskSchema] = Field(alias="rk")
    recommendations: list[RecommendationSchema] = Field(alias="rc")


def build_risk_crew(
    project_name: str,
    project_description: str,
    signals_text: str,
    task_summary: str,
    dependencies_text: str,
    activity_text: str,
) -> Crew:
    # One call produces both risks and recommendations together - no separate
    # Recommendation step, same "one call" lesson as the Planner.
    analyst = Agent(
        role="Senior Software Delivery Risk Analyst",
        goal=(
            "Diagnose the underlying delivery problems behind the "
            "already-computed project signals - schedule slippage, "
            "workload imbalance, inactivity, scope risk - and translate "
            "each into a specific risk paired with a targeted, actionable "
            "recommendation. Never recompute or second-guess the signals "
            "themselves, and never surface a risk the signals don't "
            "support. JSON only."
        ),
        backstory=(
            "A senior software delivery risk analyst who has watched dozens "
            "of capstone projects fall behind, and has learned to "
            "recognize the early numeric fingerprint of each failure mode "
            "before it becomes a missed deadline. Reads signals like a "
            "doctor reads vitals: diagnoses the cause, not just the "
            "symptom, and pairs every risk raised with a concrete, doable "
            "recommendation rather than vague advice."
        ),
        llm=risk_analysis_llm(),
        verbose=False,
        max_retry_limit=0,
    )

    task = Task(
        description=(
            f"Project: {project_name}\n"
            f"Description: {project_description}\n"
            f"Computed signals (already calculated, do not recompute): {signals_text}\n"
            f"Tasks: {task_summary[:800]}\n"
            f"Dependencies (from the project plan): {dependencies_text or 'none recorded'}\n"
            f"Recent team activity: {activity_text or 'none recorded'}\n\n"
            "Using ONLY the data above, actively check for each of these "
            "before deciding what to report - do not limit yourself to "
            "restating the breach reasons verbatim:\n"
            "- A specific milestone or task overdue (name it)\n"
            "- Low progress compared to days remaining (schedule compression)\n"
            "- Too many unfinished high-priority tasks\n"
            "- Team inactivity\n"
            "- A dependency bottleneck (one milestone/task blocking others "
            "per the dependencies list)\n"
            "- High probability of missing the deadline, if a deadline exists\n\n"
            "If days_remaining is not present in the signals above, no "
            "deadline has been set - never invent a schedule-compression or "
            "missed-deadline risk in that case; only report risks the "
            "available data actually supports.\n\n"
            "Identify 1-3 risks and 1-3 recommendations. Every recommendation "
            "must directly address one specific risk you identified - never "
            "generic advice unconnected to a named risk. Titles <=6 words, "
            "specific (name the actual milestone/task, not \"a task\"). "
            "Descriptions <=15 words. 'r' on a recommendation is the 0-based "
            "index of the risk it addresses (omit only if truly none).\n\n"
            "Output ONLY this minified JSON (no spaces, no newlines, no "
            "markdown, no explanation):\n"
            '{"rk":[{"t":"...","c":"...","s":"low|medium|high","d":"..."}],'
            '"rc":[{"t":"...","c":"...","s":"low|medium|high","e":"low|medium|high",'
            '"i":"low|medium|high","d":"...","r":0}]}'
        ),
        expected_output="One line of minified JSON matching the shape above. Nothing else.",
        agent=analyst,
    )

    return Crew(agents=[analyst], tasks=[task], process=Process.sequential, tracing=False)
