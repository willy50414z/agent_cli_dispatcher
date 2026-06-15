import json
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_eval import cli
from llm_eval.job import JobResult
from llm_eval.llm_svc import LLMEvaluationError
from llm_eval.llm_target import LLMTarget
from llm_eval.preflight import TargetStatus


def test_help_and_subcommand_help(capsys):
    assert cli.main(["--help"]) == 0
    assert "run" in capsys.readouterr().out

    assert cli.main(["run", "--help"]) == 0
    assert "--prompt" in capsys.readouterr().out

    assert cli.main(["evaluate", "--help"]) == 0
    assert "--outcome" in capsys.readouterr().out

    assert cli.main(["health", "--help"]) == 0
    assert "--json" in capsys.readouterr().out

    assert cli.main(["install_delegant", "--help"]) == 0
    assert "--level" in capsys.readouterr().out


def test_run_with_inline_prompt(capsys):
    with patch("llm_eval.cli.llm_eval.run", return_value="answer") as mock_run:
        assert cli.main(["run", "--target", "deepseek", "--prompt", "hello"]) == 0

    mock_run.assert_called_once_with(
        target=LLMTarget.DEEPSEEK,
        targets=None,
        prompt="hello",
        model=None,
        timeout=1800,
        cwd=None,
    )
    assert capsys.readouterr().out == "answer"


def test_run_with_prompt_file(tmp_path, capsys):
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("from file", encoding="utf-8")

    with patch("llm_eval.cli.llm_eval.run", return_value="ok") as mock_run:
        assert cli.main(["run", "--target", "deepseek", "--prompt-file", str(prompt_file)]) == 0

    assert mock_run.call_args.kwargs["prompt"] == "from file"
    assert capsys.readouterr().out == "ok"


def test_run_with_stdin_prompt(monkeypatch, capsys):
    class FakeStdin:
        def read(self):
            return "from stdin"

    monkeypatch.setattr("sys.stdin", FakeStdin())
    with patch("llm_eval.cli.llm_eval.run", return_value="ok") as mock_run:
        assert cli.main(["run", "--target", "deepseek", "--stdin"]) == 0

    assert mock_run.call_args.kwargs["prompt"] == "from stdin"
    assert capsys.readouterr().out == "ok"


def test_evaluate_json_with_declared_outcomes(tmp_path, capsys):
    purpose_file = tmp_path / "purpose.md"
    purpose_file.write_text("do work", encoding="utf-8")

    def fake_execute(targets, purpose, outcomes, **kwargs):
        assert targets == [LLMTarget.DEEPSEEK]
        assert purpose == "do work"
        assert [o.status for o in outcomes] == ["complete", "failed"]
        return JobResult(
            job_id="abc12345",
            status="complete",
            target="deepseek",
            duration_seconds=1.25,
            files={},
            stdout="done",
        )

    with patch("llm_eval.cli._execute_evaluate", fake_execute):
        exit_code = cli.main(
            [
                "evaluate",
                "--target",
                "deepseek",
                "--purpose-file",
                str(purpose_file),
                "--outcome",
                "complete=Done",
                "--outcome",
                "failed=Failed",
                "--json",
            ]
        )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "status": "complete",
        "target": "deepseek",
        "duration_seconds": 1.25,
        "stdout": "done",
        "files": {},
    }


def test_evaluate_output_file_json_serialization(tmp_path, capsys):
    def fake_execute(targets, purpose, outcomes, **kwargs):
        assert outcomes[0].output_files == ["errors.txt"]
        return JobResult(
            job_id="abc12345",
            status="failed",
            target="deepseek",
            duration_seconds=2.0,
            files={"errors.txt": b"bad bytes: \xff"},
            stdout="",
        )

    with patch("llm_eval.cli._execute_evaluate", fake_execute):
        exit_code = cli.main(
            [
                "evaluate",
                "--target",
                "deepseek",
                "--purpose",
                "do work",
                "--outcome",
                "failed=Failed",
                "--output-file",
                "failed=errors.txt",
                "--json",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "failed"
    assert payload["files"] == {"errors.txt": "bad bytes: \ufffd"}


def test_target_and_targets_are_mutually_exclusive(capsys):
    exit_code = cli.main(
        ["run", "--target", "deepseek", "--targets", "claude,deepseek", "--prompt", "hello"]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "not allowed with argument" in captured.err


def test_targets_are_parsed_in_order(capsys):
    with patch("llm_eval.cli.llm_eval.run", return_value="answer") as mock_run:
        assert cli.main(["run", "--targets", "claude,deepseek", "--prompt", "hello"]) == 0

    assert mock_run.call_args.kwargs["target"] is None
    assert mock_run.call_args.kwargs["targets"] == [LLMTarget.CLAUDE, LLMTarget.DEEPSEEK]
    assert capsys.readouterr().out == "answer"


def test_health_json_for_all_targets(capsys):
    statuses = {
        LLMTarget.CODEX: TargetStatus(ok=True),
        LLMTarget.DEEPSEEK: TargetStatus(ok=False, reason="missing token"),
    }

    with patch("llm_eval.cli.check_all", return_value=statuses):
        assert cli.main(["health", "--json"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "codex": {"ok": True, "reason": None},
        "deepseek": {"ok": False, "reason": "missing token"},
    }


def test_health_json_for_single_target(capsys):
    with patch("llm_eval.cli.check_target", return_value=TargetStatus(ok=True)) as mock_check:
        assert cli.main(["health", "--target", "codex", "--json"]) == 0

    mock_check.assert_called_once_with(LLMTarget.CODEX)
    assert json.loads(capsys.readouterr().out) == {"codex": {"ok": True, "reason": None}}


def test_missing_prompt_input_is_argument_error(capsys):
    exit_code = cli.main(["run", "--target", "deepseek"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "one of the arguments --prompt --prompt-file --stdin is required" in captured.err


def test_execution_failure_writes_stderr_only(capsys):
    with patch("llm_eval.cli.llm_eval.run", side_effect=LLMEvaluationError("target failed")):
        exit_code = cli.main(["run", "--target", "deepseek", "--prompt", "hello"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "target failed" in captured.err


def test_install_delegant_creates_project_guidance(tmp_path, capsys):
    exit_code = cli.main(["install_delegant", "--cwd", str(tmp_path), "--level", "1"])

    assert exit_code == 0
    guidance = tmp_path / "AGENTS.md"
    assert guidance.exists()
    text = guidance.read_text(encoding="utf-8")
    assert "agent-dispatch:openspec-delegation:start" in text
    assert "Delegation level: 1" in text
    assert "Codex-routed selective delegation" in text
    captured = capsys.readouterr()
    assert "Scope: project-local" in captured.out


def test_install_delegant_updates_existing_managed_block(tmp_path):
    guidance = tmp_path / "AGENTS.md"
    guidance.write_text("Existing guidance\n", encoding="utf-8")

    assert cli.main(["install_delegant", "--cwd", str(tmp_path), "--level", "1"]) == 0
    assert cli.main(["install_delegant", "--cwd", str(tmp_path), "--level", "2"]) == 0

    text = guidance.read_text(encoding="utf-8")
    assert text.count("agent-dispatch:openspec-delegation:start") == 1
    assert "Existing guidance" in text
    assert "Delegation level: 2" in text
    assert "submodel-first implementation" in text
    assert "Delegation level: 1" not in text


def test_install_delegant_non_interactive_requires_level(tmp_path, capsys):
    exit_code = cli.main(["install_delegant", "--cwd", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "requires --level in non-interactive mode" in captured.err
    assert not (tmp_path / "AGENTS.md").exists()


def test_install_delegant_yes_uses_level_one_default(tmp_path):
    assert cli.main(["install_delegant", "--cwd", str(tmp_path), "--yes"]) == 0

    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Delegation level: 1" in text


def test_install_delegant_uninstall_removes_managed_block(tmp_path):
    guidance = tmp_path / "AGENTS.md"
    guidance.write_text("Keep me\n", encoding="utf-8")
    assert cli.main(["install_delegant", "--cwd", str(tmp_path), "--level", "1"]) == 0

    assert cli.main(["install_delegant", "--cwd", str(tmp_path), "--uninstall"]) == 0

    text = guidance.read_text(encoding="utf-8")
    assert "Keep me" in text
    assert "agent-dispatch:openspec-delegation:start" not in text
