_QUOTA_MARKERS = ("RESOURCE_EXHAUSTED", "429", "quota")


def describe_error(exc: Exception) -> str:
    """A clear, distinguishable message for quota/rate-limit failures - the
    frontend keys off the QUOTA_EXCEEDED prefix to show a specific message
    instead of the generic "couldn't generate a plan" it uses for everything
    else, so a quota hit reads as an actionable error, not a silently empty
    plan/analysis that looks like nothing happened. Shared by the Planner
    (orchestrator_service.py) and the Risk scheduler (scheduler.py) - lives
    here, not in either of those, since scheduler.py needs to call into
    orchestrator_service.py (to trigger an immediate risk check right after a
    plan is generated) and importing this the other way around would be
    circular."""
    text = str(exc)
    if any(marker in text for marker in _QUOTA_MARKERS):
        return "QUOTA_EXCEEDED: The Gemini API quota has been exceeded. Please try again later."
    return text
