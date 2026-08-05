import os

# Must be set before crewai's telemetry module initializes (first import anywhere
# in the process) - otherwise a first-run interactive "enable tracing?" prompt can
# block indefinitely with no stdin available, which would hang this iteration's
# background job forever the first time it ever runs on a fresh machine.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from google.genai import types  # noqa: E402

from app.infrastructure.agents.gemini_client import (  # noqa: E402
    RetryingGeminiCompletion,
    build_gemini_llm,
)

# Confirmed empirically against the real API (twice, in two different
# sessions - the model's behavior changed between them): Gemini's "thinking"
# mode consumes tokens from the SAME max_output_tokens budget as the visible
# answer, silently. thinking_budget=0 used to disable it outright; as of this
# check, the live API now rejects thinking_budget=0 for this model with a
# flat 400 INVALID_ARGUMENT (confirmed via a direct, non-crewai google-genai
# call - not a crewai bug). The lowest accepted value, 1, does NOT mean "1
# token of thinking" - a real planner-shaped prompt still spent ~960 thinking
# tokens against a budget of 1. Since thinking can no longer be forced to
# zero, the budget has to be sized to survive it rather than avoid it:
# max_output_tokens raised from 300 to 1500 (confirmed empirically: 960
# thinking + 215 visible tokens = 1175 total for a real 4-milestone plan,
# 1500 leaves real margin). This is a real regression in what's achievable
# here, not a config that was wrong before - the previous 300-token budget
# was correct for the API behavior that existed when Iteration 12b shipped.
_MINIMAL_THINKING = types.ThinkingConfig(thinking_budget=1)
_MAX_OUTPUT_TOKENS = 1500

# The Documentation Agent reads the entire proposal (up to a 40k-char safety
# cap - see planning_flow.py) and extracts across 11 fields, which needs real
# headroom beyond just the ~1000-token forced-thinking tax every Gemini call
# already pays: verify empirically and adjust if it truncates on a real
# document (see docs/architecture.md).
_DOC_ANALYSIS_MAX_OUTPUT_TOKENS = 4000


def documentation_analysis_llm() -> RetryingGeminiCompletion:
    # Separate function/budget from planning_llm() - this call's output can
    # legitimately be much larger (a full extraction) even though the
    # Planner's own output stays small, since the Planner never sees the raw
    # document anymore (see planner_crew.py).
    return build_gemini_llm(
        max_output_tokens=_DOC_ANALYSIS_MAX_OUTPUT_TOKENS,
        temperature=0.1,
        thinking_config=_MINIMAL_THINKING,
    )


def planning_llm() -> RetryingGeminiCompletion:
    # The Planner no longer reads the raw proposal - it receives only the
    # Documentation Agent's compact extracted JSON (see planner_crew.py,
    # planning_flow.py), which is what keeps this call's budget small despite
    # the Documentation stage now reading the entire document.
    return build_gemini_llm(
        max_output_tokens=_MAX_OUTPUT_TOKENS,
        temperature=0.2,
        thinking_config=_MINIMAL_THINKING,
    )


def risk_analysis_llm() -> RetryingGeminiCompletion:
    # Own function (not shared with planning_llm) so its budget/temperature
    # can be tuned independently later, matching the one-function-per-crew
    # precedent - same model, same "one call" and minimal-thinking discipline.
    return build_gemini_llm(
        max_output_tokens=_MAX_OUTPUT_TOKENS,
        temperature=0.2,
        thinking_config=_MINIMAL_THINKING,
    )
