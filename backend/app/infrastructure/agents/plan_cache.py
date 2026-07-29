import hashlib
import json
from pathlib import Path

from app.application.ports.planning_orchestrator import MilestonePlan, PlannerOutput, TaskPlan

# Disk-backed (not in-memory) so it survives process restarts - a repeated
# "Generate Project Plan" request with identical inputs (same project name,
# description, and extracted proposal text) must never re-trigger the LLM,
# regardless of how many times the backend has been restarted in between.
_CACHE_DIR = Path(__file__).resolve().parents[3] / ".cache"
_CACHE_FILE = _CACHE_DIR / "plan_cache.json"


def _cache_key(project_name: str, project_description: str, proposal_text: str) -> str:
    raw = f"{project_name}\x00{project_description}\x00{proposal_text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load() -> dict:
    if not _CACHE_FILE.exists():
        return {}
    try:
        return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(data), encoding="utf-8")


def get_cached_plan(
    project_name: str, project_description: str, proposal_text: str
) -> PlannerOutput | None:
    entry = _load().get(_cache_key(project_name, project_description, proposal_text))
    if entry is None:
        return None
    return PlannerOutput(
        summary=entry["summary"],
        milestones=[
            MilestonePlan(
                title=m["title"],
                days_from_start=m["days_from_start"],
                estimated_duration_days=m.get("estimated_duration_days"),
                tasks=[TaskPlan(**t) for t in m["tasks"]],
            )
            for m in entry["milestones"]
        ],
        dependencies=entry.get("dependencies", []),
        estimated_timeline=entry.get("estimated_timeline", ""),
    )


def set_cached_plan(
    project_name: str, project_description: str, proposal_text: str, output: PlannerOutput
) -> None:
    data = _load()
    data[_cache_key(project_name, project_description, proposal_text)] = {
        "summary": output.summary,
        "milestones": [
            {
                "title": m.title,
                "days_from_start": m.days_from_start,
                "estimated_duration_days": m.estimated_duration_days,
                "tasks": [
                    {
                        "title": t.title,
                        "description": t.description,
                        "priority": t.priority,
                        "days_from_start": t.days_from_start,
                    }
                    for t in m.tasks
                ],
            }
            for m in output.milestones
        ],
        "dependencies": output.dependencies,
        "estimated_timeline": output.estimated_timeline,
    }
    _save(data)
