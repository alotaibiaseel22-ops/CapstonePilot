import hashlib
import json
from pathlib import Path

from app.application.decision_engine.rules import ProjectSignals
from app.application.ports.risk_orchestrator import RecommendationItem, RiskAnalysisOutput, RiskItem

# Disk-backed (not in-memory) so it survives process restarts, same pattern as
# plan_cache.py - an unchanged project's signals must never re-trigger a paid
# Gemini call, across scheduler ticks or backend restarts.
_CACHE_DIR = Path(__file__).resolve().parents[3] / ".cache"
_CACHE_FILE = _CACHE_DIR / "risk_cache.json"


def _cache_key(signals: ProjectSignals) -> str:
    # Rounded so trivial float noise (e.g. 0.1999999 vs 0.2) doesn't defeat
    # the cache on an otherwise-unchanged project.
    raw = (
        f"{signals.project_id}\x00{round(signals.schedule_variance, 2)}"
        f"\x00{round(signals.overdue_ratio, 2)}\x00{round(signals.workload_imbalance, 2)}"
        f"\x00{signals.total_tasks}\x00{signals.overdue_tasks}"
        f"\x00{signals.days_since_last_activity}"
    )
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


def get_cached_analysis(signals: ProjectSignals) -> RiskAnalysisOutput | None:
    entry = _load().get(_cache_key(signals))
    if entry is None:
        return None
    return RiskAnalysisOutput(
        risks=[RiskItem(**r) for r in entry["risks"]],
        recommendations=[RecommendationItem(**r) for r in entry["recommendations"]],
    )


def set_cached_analysis(signals: ProjectSignals, output: RiskAnalysisOutput) -> None:
    data = _load()
    data[_cache_key(signals)] = {
        "risks": [
            {
                "title": r.title,
                "category": r.category,
                "severity": r.severity,
                "description": r.description,
            }
            for r in output.risks
        ],
        "recommendations": [
            {
                "title": r.title,
                "category": r.category,
                "severity": r.severity,
                "effort": r.effort,
                "impact": r.impact,
                "description": r.description,
                "rationale": r.rationale,
                "risk_index": r.risk_index,
            }
            for r in output.recommendations
        ],
    }
    _save(data)
