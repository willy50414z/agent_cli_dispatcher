from pathlib import Path

from llm_eval.job import Outcome
from llm_eval.prompt_builder import build_prompt


def _noop(r):
    pass


def test_prompt_starts_with_purpose():
    outcomes = [Outcome("All done", _noop, status="complete")]
    prompt = build_prompt("Review this doc.", outcomes)
    assert prompt.startswith("Review this doc.")


def test_prompt_contains_output_files_for_outcome():
    outcomes = [
        Outcome("Has gaps", _noop, status="incomplete", output_files=["questions.txt"]),
    ]
    prompt = build_prompt("Review.", outcomes)
    assert "questions.txt" in prompt
    assert "incomplete" in prompt


def test_prompt_contains_output_files_for_all_non_error_outcomes():
    outcomes = [
        Outcome("Spec is complete", _noop, status="complete", output_files=["result.md"]),
        Outcome("Spec has gaps",    _noop, status="incomplete", output_files=["questions.txt"]),
    ]
    prompt = build_prompt("Review.", outcomes)
    assert "result.md" in prompt
    assert "questions.txt" in prompt


def test_prompt_omits_error_outcome_files():
    outcomes = [
        Outcome("All good", _noop, status="complete", output_files=["result.md"]),
        Outcome("Failed",   _noop, status="error"),
    ]
    prompt = build_prompt("Review.", outcomes)
    assert "error" not in prompt
    assert "result.md" in prompt


def test_prompt_returns_purpose_only_when_no_outcomes_have_files():
    outcomes = [Outcome("All done", _noop, status="complete")]
    prompt = build_prompt("Review this doc.", outcomes)
    assert prompt == "Review this doc."


def test_prompt_uses_absolute_paths_when_workspace_given(tmp_path):
    outcomes = [
        Outcome("Done", _noop, status="complete", output_files=["result.md"]),
    ]
    prompt = build_prompt("Review.", outcomes, workspace=tmp_path)
    assert str(tmp_path / "result.md") in prompt


def test_prompt_uses_relative_paths_when_no_workspace():
    outcomes = [
        Outcome("Done", _noop, status="complete", output_files=["result.md"]),
    ]
    prompt = build_prompt("Review.", outcomes)
    assert "result.md" in prompt
    assert str(Path.cwd()) not in prompt


def test_output_files_listed_after_separator():
    outcomes = [
        Outcome("Has gaps", _noop, status="incomplete", output_files=["questions.txt"]),
    ]
    prompt = build_prompt("Review.", outcomes)
    separator_pos = prompt.index("---")
    file_pos = prompt.index("questions.txt")
    assert file_pos > separator_pos
