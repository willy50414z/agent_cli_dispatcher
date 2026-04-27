import pytest
from pathlib import Path
from unittest.mock import patch
from llm_eval import evaluate
from llm_eval.job import Outcome, JobResult


def _noop(r):
    pass


def _fake_run_once_writing(status_name, extra_files=None):
    """Returns a fake run_once that creates status + extra files in the workspace cwd."""
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
        Outcome("complete",   "Done",      lambda r: received.append(r)),
        Outcome("incomplete", "Has gaps",  _noop, output_files=["questions.txt"]),
    ]

    with patch("llm_eval.llm_svc.run_once", _fake_run_once_writing("complete")):
        evaluate(target="claude", purpose="Review.", outcomes=outcomes, cwd=str(tmp_path))

    assert len(received) == 1
    assert received[0].status == "complete"
    assert received[0].target == "claude"
    assert received[0].stdout == "fake stdout"


def test_evaluate_passes_files_to_callback(tmp_path):
    received = []

    outcomes = [
        Outcome("incomplete", "Has gaps", lambda r: received.append(r),
                output_files=["questions.txt"]),
    ]

    with patch("llm_eval.llm_svc.run_once",
               _fake_run_once_writing("incomplete", {"questions.txt": "Q1?"})):
        evaluate(target="claude", purpose="Review.", outcomes=outcomes, cwd=str(tmp_path))

    assert received[0].files["questions.txt"] == "Q1?"


def test_evaluate_cleans_up_workspace_after_callback(tmp_path):
    ws_path = []

    def capture_ws(target, prompt, **kwargs):
        ws_path.append(Path(kwargs["cwd"]))
        (ws_path[0] / "status_complete").touch()
        return ""

    outcomes = [Outcome("complete", "Done", _noop)]

    with patch("llm_eval.llm_svc.run_once", capture_ws):
        evaluate(target="claude", purpose=".", outcomes=outcomes, cwd=str(tmp_path))

    assert not ws_path[0].exists()


def test_evaluate_cleans_up_workspace_even_when_callback_raises(tmp_path):
    ws_path = []

    def capture_ws(target, prompt, **kwargs):
        ws_path.append(Path(kwargs["cwd"]))
        (ws_path[0] / "status_complete").touch()
        return ""

    def raising_callback(r):
        raise ValueError("callback error")

    outcomes = [Outcome("complete", "Done", raising_callback)]

    with patch("llm_eval.llm_svc.run_once", capture_ws):
        with pytest.raises(ValueError, match="callback error"):
            evaluate(target="claude", purpose=".", outcomes=outcomes, cwd=str(tmp_path))

    assert not ws_path[0].exists()


def test_evaluate_calls_on_exception_when_run_once_raises(tmp_path):
    errors = []

    def boom(target, prompt, **kwargs):
        raise RuntimeError("CLI not found")

    outcomes = [Outcome("complete", "Done", _noop)]

    with patch("llm_eval.llm_svc.run_once", boom):
        evaluate(
            target="claude",
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

    outcomes = [Outcome("complete", "Done", _noop)]

    with patch("llm_eval.llm_svc.run_once", boom):
        with pytest.raises(RuntimeError, match="CLI not found"):
            evaluate(target="claude", purpose=".", outcomes=outcomes, cwd=str(tmp_path))


def test_evaluate_raises_on_invalid_target(tmp_path):
    with pytest.raises(ValueError, match="Unsupported target"):
        evaluate(target="nonexistent", purpose=".", outcomes=[])
