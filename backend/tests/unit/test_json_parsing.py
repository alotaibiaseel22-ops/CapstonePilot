import json

import pytest

from app.infrastructure.agents.json_parsing import parse_json_response


def test_parses_clean_json_with_no_fence():
    assert parse_json_response('{"a": 1, "b": [1, 2]}') == {"a": 1, "b": [1, 2]}


def test_strips_a_markdown_fence():
    raw = '```json\n{"a": 1}\n```'
    assert parse_json_response(raw) == {"a": 1}


def test_strips_a_fence_surrounded_by_chatty_prose():
    raw = (
        'Sure, here is the JSON you asked for:\n```json\n{"a": 1}\n```\n'
        "Let me know if you need changes!"
    )
    assert parse_json_response(raw) == {"a": 1}


def test_extracts_the_object_when_there_is_no_fence_at_all():
    raw = 'Here you go: {"a": 1} - hope that helps.'
    assert parse_json_response(raw) == {"a": 1}


def test_normalizes_smart_quotes():
    raw = "{“a”: “hello”}"
    assert parse_json_response(raw) == {"a": "hello"}


def test_strips_trailing_commas():
    raw = '{"a": [1, 2, 3,], "b": 4,}'
    assert parse_json_response(raw) == {"a": [1, 2, 3], "b": 4}


def test_repairs_a_string_truncated_mid_value():
    # The model was cut off mid-string, e.g. by max_output_tokens - the
    # dangling quote gets closed, keeping the partial content rather than
    # discarding it (it still parses as valid, if slightly mangled, JSON).
    raw = '{"a": 1, "b": ["x", "y", "half-writ'
    assert parse_json_response(raw) == {"a": 1, "b": ["x", "y", "half-writ"]}


def test_repairs_json_truncated_right_after_a_comma():
    raw = '{"a": 1, "b": ["x", "y",'
    assert parse_json_response(raw) == {"a": 1, "b": ["x", "y"]}


def test_repairs_json_truncated_at_a_dangling_key():
    raw = '{"a": 1, "b": ["x"], "unfinished_ke'
    assert parse_json_response(raw) == {"a": 1, "b": ["x"]}


def test_repairs_a_nested_object_truncated_mid_field():
    raw = '{"m": [{"t": "Milestone One", "d": 0}, {"t": "Milestone Two", "d'
    assert parse_json_response(raw) == {"m": [{"t": "Milestone One", "d": 0}]}


def test_raises_the_original_error_for_genuinely_unparseable_garbage():
    with pytest.raises(json.JSONDecodeError):
        parse_json_response("not json at all, just prose with no braces")
