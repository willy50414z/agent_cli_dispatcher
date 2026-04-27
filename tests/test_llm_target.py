import pytest
from llm_eval.llm_target import LLMTarget


def test_all_targets_accessible():
    assert LLMTarget.CLAUDE.value == "claude"
    assert LLMTarget.GEMINI.value == "gemini"
    assert LLMTarget.CODEX.value == "codex"
    assert LLMTarget.OPENCODE.value == "opencode"
    assert LLMTarget.COPILOT.value == "copilot"


def test_lookup_by_string():
    assert LLMTarget("claude") == LLMTarget.CLAUDE


def test_invalid_string_raises():
    with pytest.raises(ValueError):
        LLMTarget("unknown")
