from lithic.tools.audit import _redact, _redact_obj, _summarize, tool_call


def test_summarize_truncates_long_strings() -> None:
    result = _summarize({"key": "a" * 300})
    assert len(result["key"]) == 203
    assert result["key"].endswith("...")


def test_summarize_short_strings_passthrough() -> None:
    result = _summarize({"key": "short"})
    assert result["key"] == "short"


def test_summarize_none() -> None:
    assert _summarize(None) == {}


def test_summarize_empty() -> None:
    assert _summarize({}) == {}


def test_tool_call_does_not_raise() -> None:
    tool_call("test_tool", {"arg": "val"}, True, 0.05)


def test_redact_assignment_forms() -> None:
    assert _redact("api_key=sk-secret") == "api_key=***"
    assert _redact("api_key: sk-secret") == "api_key: ***"
    assert _redact("Authorization: Bearer sk-secret") == "Authorization: ***"
    assert _redact("authorization=sk-secret") == "Authorization=***"


def test_redact_sensitive_dict_keys() -> None:
    assert _redact_obj({"api_key": "sk-secret", "safe": "value"}) == {
        "api_key": "***",
        "safe": "value",
    }
