import json
import logging
import re

logger = logging.getLogger(__name__)

# Matches a fenced block ANYWHERE in the text (not anchored to start/end),
# since a chatty model can precede or follow the fence with prose ("Here's
# the JSON you asked for:\n```json\n{...}\n```\nLet me know if you need
# changes."). Falls back to the first balanced {...} object if there's no
# fence at all.
_CODE_FENCE_BLOCK = re.compile(r"```(?:[a-zA-Z]*)\s*\n?(.*?)```", re.DOTALL)
_TRAILING_COMMA = re.compile(r",(\s*[}\]])")
_SMART_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def _extract_json_candidate(raw: str) -> str:
    text = raw.strip()
    fence_match = _CODE_FENCE_BLOCK.search(text)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _repair_truncated_json(text: str) -> dict:
    """Best-effort recovery for output the token budget cut off mid-object -
    the exact shape of a Gemini response hitting max_output_tokens before it
    finished writing. First closes a dangling unterminated string, keeping
    whatever partial content it had rather than discarding it. If that alone
    isn't enough to parse (e.g. truncated right after a comma, colon, or
    dangling key with no value yet), repeatedly trims the last incomplete
    token from the tail and closes whatever brackets are still open, until
    something parses - this can drop the last, genuinely-incomplete item
    from an array, which is preferable to failing the whole generation over
    one truncated tail. Raises the original error if nothing, down to an
    empty string, ever parses."""
    candidate = text
    if len(re.findall(r'(?<!\\)"', candidate)) % 2 == 1:
        candidate += '"'

    while candidate:
        trimmed = candidate.rstrip().rstrip(",:")
        stack = []
        for ch in trimmed:
            if ch in "{[":
                stack.append(ch)
            elif ch in "}]" and stack:
                stack.pop()
        closers = "".join("}" if opener == "{" else "]" for opener in reversed(stack))
        try:
            return json.loads(trimmed + closers)
        except json.JSONDecodeError:
            candidate = trimmed[:-1]

    raise json.JSONDecodeError("Could not repair truncated JSON", text, 0)


def parse_json_response(raw: str) -> dict:
    """Parses a crew's raw JSON-only response. The model is never assumed to
    return clean, complete JSON - this tolerates a markdown fence anywhere in
    the response, chatty prose surrounding it, curly/smart quotes, trailing
    commas, and - as a last resort - output truncated mid-object by the
    token budget. On any parse failure the raw response and the exact
    failure position are logged so a real production failure is debuggable
    from the logs, not just a generic 500."""
    candidate = _extract_json_candidate(raw)
    candidate = candidate.translate(_SMART_QUOTES)
    candidate = _TRAILING_COMMA.sub(r"\1", candidate)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as first_error:
        logger.warning(
            "JSON parse failed at char %d (%s) - attempting truncation repair. "
            "Raw response (%d chars): %r",
            first_error.pos,
            first_error.msg,
            len(raw),
            raw,
        )
        try:
            repaired = _repair_truncated_json(candidate)
        except json.JSONDecodeError:
            logger.error(
                "JSON repair also failed. Raw response (%d chars): %r", len(raw), raw
            )
            raise first_error from None
        logger.warning("Truncation repair succeeded - parsed response: %r", repaired)
        return repaired
