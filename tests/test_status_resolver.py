import logging
import pytest
from pathlib import Path
from llm_eval.job import Outcome, JobResult
from llm_eval.status_resolver import resolve


def _noop(r):
    pass


def _outcomes(*statuses):
    return [Outcome(s, f"desc {s}", _noop) for s in statuses]


def test_resolve_detects_status_file(tmp_path):
    (tmp_path / "status_complete").touch()
    outcomes = _outcomes("complete", "error")
    matched, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert result.status == "complete"
    assert matched.status == "complete"


def test_resolve_raises_when_no_status_file_and_no_error_outcome(tmp_path):
    outcomes = _outcomes("complete")
    with pytest.raises(RuntimeError, match="No status file"):
        resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")


def test_resolve_triggers_error_outcome_when_no_status_file(tmp_path):
    outcomes = _outcomes("complete", "error")
    matched, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert result.status == "error"
    assert matched.status == "error"


def test_resolve_raises_when_status_file_matches_no_outcome(tmp_path):
    (tmp_path / "status_unknown").touch()
    outcomes = _outcomes("complete")
    with pytest.raises(RuntimeError, match="does not match any defined outcome"):
        resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")


def test_resolve_raises_when_declared_output_file_missing(tmp_path):
    (tmp_path / "status_incomplete").touch()
    outcomes = [Outcome("incomplete", "gaps", _noop, output_files=["questions.txt"])]
    with pytest.raises(RuntimeError, match="questions.txt"):
        resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")


def test_resolve_collects_declared_output_file_content(tmp_path):
    (tmp_path / "status_incomplete").touch()
    (tmp_path / "questions.txt").write_text("Q1?")
    outcomes = [Outcome("incomplete", "gaps", _noop, output_files=["questions.txt"])]
    _, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert result.files["questions.txt"] == "Q1?"


def test_resolve_excludes_status_file_from_files_dict(tmp_path):
    (tmp_path / "status_complete").touch()
    outcomes = _outcomes("complete")
    _, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert "status_complete" not in result.files


def test_resolve_populates_job_result_metadata(tmp_path):
    (tmp_path / "status_complete").touch()
    outcomes = _outcomes("complete")
    _, result = resolve(tmp_path, outcomes, "id1", "claude", 2.5, "raw stdout")
    assert result.job_id == "id1"
    assert result.target == "claude"
    assert result.duration_seconds == 2.5
    assert result.stdout == "raw stdout"


def test_resolve_uses_first_alphabetical_on_multiple_status_files(tmp_path, caplog):
    (tmp_path / "status_complete").touch()
    (tmp_path / "status_incomplete").touch()
    outcomes = _outcomes("complete", "incomplete")
    with caplog.at_level(logging.WARNING, logger="llm_eval.status_resolver"):
        matched, result = resolve(tmp_path, outcomes, "id1", "claude", 1.0, "stdout")
    assert result.status == "complete"
    assert "Multiple status files" in caplog.text
