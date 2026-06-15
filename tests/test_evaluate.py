import pytest
from pathlib import Path
from unittest.mock import patch
from llm_eval import evaluate, run, LLMTarget
from llm_eval.job import Outcome, JobResult


def _noop(r):
    pass


def _fake_run_writing(status_name, extra_files=None):
    """Returns a fake run that creates status + extra files in the workspace cwd."""
    def fake(target, prompt, **kwargs):
        ws = Path(kwargs["cwd"])
        (ws / f"status_{status_name}").touch()
        for fname, content in (extra_files or {}).items():
            (ws / fname).write_text(content)
        return "fake stdout"
    return fake


def test_evaluate_calls_matching_callback(tmp_path):
    received = []

    outcomes = [
        Outcome("Done",      lambda r: received.append(r), status="complete"),
        Outcome("Has gaps",  _noop, status="incomplete", output_files=["questions.txt"]),
    ]

    with patch("llm_eval.llm_svc.run", _fake_run_writing("complete")):
        evaluate(target=LLMTarget.CLAUDE, purpose="Review.", outcomes=outcomes, cwd=str(tmp_path))

    assert len(received) == 1
    assert received[0].status == "complete"
    assert received[0].target == "claude"
    assert received[0].stdout == "fake stdout"


def test_evaluate_passes_files_to_callback(tmp_path):
    received = []

    outcomes = [
        Outcome("Has gaps", lambda r: received.append(r),
                status="incomplete", output_files=["questions.txt"]),
    ]

    with patch("llm_eval.llm_svc.run",
               _fake_run_writing("incomplete", {"questions.txt": "Q1?"})):
        evaluate(target=LLMTarget.CLAUDE, purpose="Review.", outcomes=outcomes, cwd=str(tmp_path))

    assert received[0].files["questions.txt"] == b"Q1?"


def test_evaluate_cleans_up_workspace_after_callback(tmp_path):
    ws_path = []

    def capture_ws(target, prompt, **kwargs):
        ws_path.append(Path(kwargs["cwd"]))
        (ws_path[0] / "status_complete").touch()
        return ""

    outcomes = [Outcome("Done", _noop, status="complete")]

    with patch("llm_eval.llm_svc.run", capture_ws):
        evaluate(target=LLMTarget.CLAUDE, purpose=".", outcomes=outcomes, cwd=str(tmp_path))

    assert not ws_path[0].exists()


def test_evaluate_cleans_up_workspace_even_when_callback_raises(tmp_path):
    ws_path = []

    def capture_ws(target, prompt, **kwargs):
        ws_path.append(Path(kwargs["cwd"]))
        (ws_path[0] / "status_complete").touch()
        return ""

    def raising_callback(r):
        raise ValueError("callback error")

    outcomes = [Outcome("Done", raising_callback, status="complete")]

    with patch("llm_eval.llm_svc.run", capture_ws):
        with pytest.raises(ValueError, match="callback error"):
            evaluate(target=LLMTarget.CLAUDE, purpose=".", outcomes=outcomes, cwd=str(tmp_path))

    assert not ws_path[0].exists()


def test_evaluate_calls_on_exception_when_run_raises(tmp_path):
    errors = []

    def boom(target, prompt, **kwargs):
        raise RuntimeError("CLI not found")

    outcomes = [Outcome("Done", _noop, status="complete")]

    with patch("llm_eval.llm_svc.run", boom):
        evaluate(
            target=LLMTarget.CLAUDE,
            purpose=".",
            outcomes=outcomes,
            on_exception=lambda exc: errors.append(exc),
            cwd=str(tmp_path),
        )

    assert len(errors) == 1
    assert "CLI not found" in str(errors[0])


def test_evaluate_propagates_exception_when_no_on_exception(tmp_path):
    def boom(target, prompt, **kwargs):
        raise RuntimeError("CLI not found")

    outcomes = [Outcome("Done", _noop, status="complete")]

    with patch("llm_eval.llm_svc.run", boom):
        with pytest.raises(RuntimeError, match="CLI not found"):
            evaluate(target=LLMTarget.CLAUDE, purpose=".", outcomes=outcomes, cwd=str(tmp_path))


def test_run_returns_raw_llm_stdout(tmp_path):
    def fake_run(target, prompt, **kwargs):
        assert target == LLMTarget.CLAUDE
        assert prompt == "What is 2 + 2?"
        assert kwargs["cwd"] == str(tmp_path)
        return "4"

    with patch("llm_eval.llm_svc.run", fake_run):
        assert run(target=LLMTarget.CLAUDE, prompt="What is 2 + 2?", cwd=str(tmp_path)) == "4"


def test_run_supports_target_fallback_list(tmp_path):
    def fake_run_with_fallback(targets, prompt, **kwargs):
        assert targets == [LLMTarget.CLAUDE, LLMTarget.CODEX]
        assert prompt == "Question"
        assert kwargs["cwd"] == str(tmp_path)
        return "Answer"

    with patch("llm_eval.llm_svc.run_with_fallback", fake_run_with_fallback):
        assert run(targets=[LLMTarget.CLAUDE, LLMTarget.CODEX], prompt="Question", cwd=str(tmp_path)) == "Answer"


def test_evaluate_rejects_empty_outcomes(tmp_path):
    with pytest.raises(ValueError, match="outcomes must not be empty"):
        evaluate(target=LLMTarget.CLAUDE, purpose="Review.", outcomes=[], cwd=str(tmp_path))
