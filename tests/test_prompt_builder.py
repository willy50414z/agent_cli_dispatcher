from llm_eval.job import Outcome
from llm_eval.prompt_builder import build_prompt


def _noop(r):
    pass


def test_prompt_starts_with_purpose():
    outcomes = [Outcome("All done", _noop, status="complete")]
    prompt = build_prompt("Review this doc.", outcomes)
    assert prompt.startswith("Review this doc.")


def test_prompt_contains_all_status_file_names():
    outcomes = [
        Outcome("Spec is complete", _noop, status="complete"),
        Outcome("Spec has gaps",    _noop, status="incomplete"),
    ]
    prompt = build_prompt("Review.", outcomes)
    assert "status_complete" in prompt
    assert "status_incomplete" in prompt


def test_prompt_uses_index_when_status_not_set():
    outcomes = [
        Outcome("Spec is complete", _noop),
        Outcome("Spec has gaps",    _noop),
    ]
    prompt = build_prompt("Review.", outcomes)
    assert "status_0" in prompt
    assert "status_1" in prompt


def test_prompt_contains_outcome_descriptions():
    outcomes = [Outcome("Spec is complete", _noop, status="complete")]
    prompt = build_prompt("Review.", outcomes)
    assert "Spec is complete" in prompt


def test_output_files_listed_only_for_their_outcome():
    outcomes = [
        Outcome("All good", _noop, status="complete"),
        Outcome("Has gaps", _noop, status="incomplete", output_files=["questions.txt"]),
    ]
    prompt = build_prompt("Review.", outcomes)
    assert "questions.txt" in prompt
    assert prompt.index("questions.txt") > prompt.index("incomplete")


def test_no_output_files_section_when_none_declared():
    outcomes = [Outcome("All good", _noop, status="complete")]
    prompt = build_prompt("Review.", outcomes)
    assert "also write" not in prompt


def test_prompt_contains_single_file_rule():
    outcomes = [Outcome("All good", _noop, status="complete")]
    prompt = build_prompt("Review.", outcomes)
    assert "Do not create more than one status file" in prompt
    assert "Do not write anything inside the status file" in prompt
